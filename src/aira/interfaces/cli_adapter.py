"""Local Typer/Rich CLI adapter implementing ChannelDeliveryPort and IPC commands."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from aira.config import ApplicationSettings, load_settings
from aira.interfaces.ipc_control import IPCControlError, LocalIPCClient
from aira.interfaces.models import (
    CancellationScope,
    CancellationSignal,
    CancelResult,
    ChannelType,
    DeliveryReceipt,
    OutboundMessage,
)
from aira.interfaces.paginator import MessagePaginator
from aira.interfaces.router import (
    ActiveTurnCoordinator,
    CommandRouter,
    RouteDecision,
    RouteOutcomeKind,
)
from aira.ports.channel import (
    CancellationHandler,
    ChannelDeliveryPort,
    InboundTurnHandler,
)


class CLIDeliveryAdapter(ChannelDeliveryPort):
    """Outbound ChannelDeliveryPort adapter rendering messages via Rich Console."""

    def __init__(
        self,
        *,
        console: Console | None = None,
        paginator: MessagePaginator | None = None,
        show_typing: bool = False,
    ) -> None:
        self._console = console or Console()
        self._paginator = paginator
        self._show_typing = show_typing
        self.typing_indicator_count = 0

    @property
    def channel(self) -> ChannelType:
        """Identify this adapter as the local CLI channel."""
        return ChannelType.LOCAL_CLI

    async def send_typing_indicator(self, chat_id: str) -> None:
        """Best-effort CLI thinking indicator."""
        self.typing_indicator_count += 1
        if self._show_typing:
            self._console.print("[dim]AIRA is processing...[/dim]")

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """Render outbound text cleanly in the local CLI console."""
        chunks = self._paginator.paginate(message.text) if self._paginator else [message.text]
        for chunk in chunks:
            self._console.print(chunk)

        return DeliveryReceipt(
            channel=ChannelType.LOCAL_CLI,
            chat_id=message.chat_id,
            delivered=True,
            chunk_count=len(chunks),
            message_ids=tuple(f"cli-{idx}" for idx in range(1, len(chunks) + 1)),
        )


class CLIGateway:
    """Interactive and one-shot local CLI ingress gateway with IPC cancel/status."""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        router: CommandRouter | None = None,
        coordinator: ActiveTurnCoordinator | None = None,
        turn_handler: InboundTurnHandler | None = None,
        cancel_handler: CancellationHandler | None = None,
        delivery: ChannelDeliveryPort | None = None,
        console: Console | None = None,
    ) -> None:
        self._settings = settings
        self._router = router or CommandRouter()
        self._coordinator = coordinator or ActiveTurnCoordinator(settings)
        self._turn_handler = turn_handler or self._coordinator
        self._cancel_handler = cancel_handler or self._coordinator
        self._console = console or Console()
        self._delivery = delivery or CLIDeliveryAdapter(console=self._console)

    async def process_line(
        self,
        line: str,
        *,
        sender_id: str = "local_owner",
        chat_id: str = "cli_local",
    ) -> RouteDecision:
        """Route one CLI input line, execute its action, and deliver output cleanly."""
        decision = self._router.route(
            channel=ChannelType.LOCAL_CLI,
            sender_id=sender_id,
            chat_id=chat_id,
            raw_text=line,
        )

        if decision.outcome == RouteOutcomeKind.CANCEL:
            assert decision.cancellation is not None
            result, _source = await self.cancel_via_cli(
                target_turn_id=decision.cancellation.target_turn_id,
                reason=decision.cancellation.reason,
            )
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.LOCAL_CLI,
                    chat_id=chat_id,
                    text=result.detail or result.external_call_warning,
                )
            )
            return decision

        if decision.outcome == RouteOutcomeKind.UNAVAILABLE:
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.LOCAL_CLI,
                    chat_id=chat_id,
                    text=decision.response_text or "Command or input unavailable.",
                )
            )
            return decision

        assert decision.request is not None
        if decision.outcome == RouteOutcomeKind.TURN:
            await self._delivery.send_typing_indicator(chat_id)

        response = await self._turn_handler.handle_turn(decision.request)
        await self._delivery.send_message(
            OutboundMessage(
                channel=ChannelType.LOCAL_CLI,
                chat_id=chat_id,
                text=response.text,
                parse_mode=response.parse_mode,
                correlation_id=response.turn_id,
            )
        )
        return decision

    async def run_chat_loop(
        self,
        *,
        input_reader: Callable[[], str] | None = None,
        sender_id: str = "local_owner",
        chat_id: str = "cli_local",
    ) -> None:
        """Run interactive CLI conversation loop with clean exit on EOF/exit/Ctrl+C."""
        self._console.print(
            Panel.fit(
                f"{self._settings.app_name} Local CLI Gateway\n"
                "Type a message, /help, /status, /cancel, or 'exit' to quit.",
                title="AIRA CLI",
            )
        )
        read_fn = input_reader or (lambda: self._console.input("[bold cyan]aira>[/bold cyan] "))

        while True:
            try:
                raw_line = await asyncio.to_thread(read_fn) if input_reader is None else read_fn()
            except (EOFError, KeyboardInterrupt):
                self._console.print("\nExiting AIRA CLI.")
                break

            stripped = raw_line.strip()
            if stripped.lower() in {"exit", "/exit", "quit", "/quit"}:
                self._console.print("Goodbye.")
                break

            await self.process_line(raw_line, sender_id=sender_id, chat_id=chat_id)

    async def cancel_via_cli(
        self,
        *,
        target_turn_id: str | None = None,
        requested_by: str = "local_cli",
        reason: str = "CLI cancel command",
    ) -> tuple[CancelResult, str]:
        """Attempt authenticated cross-process IPC cancel first; fall back locally if idle."""
        sock_path = self._settings.ipc_socket_path
        ipc_token = self._settings.ipc_auth_token

        if sock_path.exists() and ipc_token is not None:
            client = LocalIPCClient(socket_path=sock_path, auth_token=ipc_token)
            try:
                result = await client.send_cancel(
                    target_turn_id=target_turn_id,
                    requested_by=requested_by,
                    reason=reason,
                )
                return result, "ipc"
            except IPCControlError as exc:
                if "Unauthorized IPC token" in str(exc):
                    raise

        signal = CancellationSignal(
            source_channel=ChannelType.LOCAL_CLI,
            requested_by=requested_by,
            target_turn_id=target_turn_id,
            scope=(
                CancellationScope.TURN if target_turn_id else CancellationScope.ALL_ACTIVE
            ),
            reason=reason,
        )
        local_res = await self._cancel_handler.handle_cancel(signal)
        return local_res, "local"

    async def status_via_cli(self) -> tuple[dict[str, Any], str]:
        """Fetch live IPC status if daemon socket is reachable, otherwise local snapshot."""
        sock_path = self._settings.ipc_socket_path
        ipc_token = self._settings.ipc_auth_token

        if sock_path.exists() and ipc_token is not None:
            client = LocalIPCClient(socket_path=sock_path, auth_token=ipc_token)
            try:
                status = await client.fetch_status()
                return status, "ipc"
            except IPCControlError as exc:
                if "Unauthorized IPC token" in str(exc):
                    raise

        return self._coordinator.get_status_snapshot(), "local"


def create_cli_app(
    *,
    settings: ApplicationSettings | None = None,
    gateway_factory: Callable[[ApplicationSettings, Console], CLIGateway] | None = None,
    console: Console | None = None,
) -> typer.Typer:
    """Build the Typer CLI application exposing chat, status, help, and cancel."""
    app = typer.Typer(
        name="aira",
        help="AIRA MOCHTAR Personal AI OS local command-line interface.",
        no_args_is_help=True,
    )
    active_console = console or Console()

    def _build_gateway() -> CLIGateway:
        resolved = settings or load_settings()
        if gateway_factory is not None:
            return gateway_factory(resolved, active_console)
        return CLIGateway(settings=resolved, console=active_console)

    @app.command("chat")
    def chat_command() -> None:
        """Start an interactive local CLI chat session with AIRA."""
        gateway = _build_gateway()
        asyncio.run(gateway.run_chat_loop())

    @app.command("help")
    def help_command() -> None:
        """Show supported AIRA CLI and gateway commands."""
        active_console.print(
            Panel.fit(
                "Commands:\n"
                "  chat    Interactive local conversation loop\n"
                "  status  Show local or running IPC runtime status\n"
                "  cancel  Cancel active turns over local IPC or in-process\n"
                "  help    Display this command reference\n\n"
                "In-chat commands: /help, /status, /cancel, /start",
                title="AIRA Help",
            )
        )

    @app.command("status")
    def status_command() -> None:
        """Display runtime gateway status safely without exposing secrets."""
        gateway = _build_gateway()
        try:
            snap, source = asyncio.run(gateway.status_via_cli())
        except IPCControlError as exc:
            active_console.print(f"[red]Status check failed: {exc}[/red]")
            raise typer.Exit(code=1) from None

        active_console.print(
            Panel.fit(
                f"App: {snap.get('app_name', 'AIRA MOCHTAR')}\n"
                f"Environment: {snap.get('environment', 'unknown')}\n"
                f"Telegram enabled: {snap.get('telegram_enabled', False)}\n"
                f"Reasoning core attached: {snap.get('reasoning_core_attached', False)}\n"
                f"Active turns: {snap.get('active_turn_count', 0)}\n"
                f"Source: {source}",
                title="AIRA Status",
            )
        )

    @app.command("cancel")
    def cancel_command(
        turn_id: str | None = typer.Option(
            None,
            "--turn-id",
            help="Optional specific turn ID to cancel.",
        ),
        reason: str = typer.Option(
            "CLI cancel command",
            "--reason",
            help="Audit/log reason recorded with the cancellation signal.",
        ),
    ) -> None:
        """Cancel active turns via authenticated IPC socket or local runtime."""
        gateway = _build_gateway()
        try:
            result, source = asyncio.run(
                gateway.cancel_via_cli(target_turn_id=turn_id, reason=reason)
            )
        except IPCControlError as exc:
            active_console.print(f"[red]Cancel failed: {exc}[/red]")
            raise typer.Exit(code=1) from None

        active_console.print(
            f"[{'green' if result.acknowledged else 'yellow'}]"
            f"Acknowledged ({source}): {result.detail}[/]\n"
            f"Note: {result.external_call_warning}"
        )

    return app
