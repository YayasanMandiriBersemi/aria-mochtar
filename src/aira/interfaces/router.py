"""Command routing and in-process active-turn cancellation coordinator for CMP-02."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from aira.config import ApplicationSettings
from aira.ports.channel import (
    CancellationHandler,
    CancellationScope,
    CancellationSignal,
    CancelResult,
    ChannelType,
    InboundTurnHandler,
    InboundUserRequest,
    SlashCommand,
    TurnResponse,
)

MAX_INPUT_TEXT_LENGTH = 32_000

_COMMAND_ALIASES: dict[str, SlashCommand] = {
    "/start": SlashCommand.START,
    "/help": SlashCommand.HELP,
    "/status": SlashCommand.STATUS,
    "/cancel": SlashCommand.CANCEL,
    "/stop": SlashCommand.CANCEL,
    "/kill_all": SlashCommand.CANCEL,
    "/tasks": SlashCommand.TASKS,
    "/notes": SlashCommand.NOTES,
    "/briefing": SlashCommand.BRIEFING,
}

_ROADMAP_DEFERRED_COMMANDS: frozenset[SlashCommand] = frozenset(
    {
        SlashCommand.TASKS,
        SlashCommand.NOTES,
        SlashCommand.BRIEFING,
    }
)


class RouteOutcomeKind(str, Enum):
    """Classification of a routed inbound user line or Telegram message."""

    TURN = "turn"
    COMMAND_LOCAL = "command_local"
    CANCEL = "cancel"
    UNAVAILABLE = "unavailable"


class RouteDecision(BaseModel):
    """Deterministic routing outcome produced by CommandRouter."""

    model_config = ConfigDict(frozen=True)

    outcome: RouteOutcomeKind
    request: InboundUserRequest | None = None
    cancellation: CancellationSignal | None = None
    response_text: str | None = None
    reason: str = ""


class CommandRouter:
    """Validates message bounds and maps whitelisted slash commands cleanly."""

    def __init__(
        self,
        *,
        bot_username: str | None = None,
        enabled_roadmap_commands: Iterable[SlashCommand] = (),
        max_input_length: int = MAX_INPUT_TEXT_LENGTH,
    ) -> None:
        self._bot_username = bot_username.lstrip("@").lower() if bot_username else None
        self._enabled_roadmap_commands = frozenset(enabled_roadmap_commands)
        self._max_input_length = max_input_length

    def route(
        self,
        *,
        channel: ChannelType,
        sender_id: str,
        chat_id: str,
        raw_text: str,
        update_id: int | None = None,
        message_id: str | None = None,
    ) -> RouteDecision:
        """Normalize and classify raw inbound user text into a safe RouteDecision."""
        trimmed = raw_text.strip()
        if not trimmed:
            return RouteDecision(
                outcome=RouteOutcomeKind.UNAVAILABLE,
                response_text="Empty messages cannot be processed. Send a message or /help.",
                reason="Empty inbound message text.",
            )

        if len(trimmed) > self._max_input_length:
            return RouteDecision(
                outcome=RouteOutcomeKind.UNAVAILABLE,
                response_text=(
                    f"Message exceeds maximum allowed length of "
                    f"{self._max_input_length} characters."
                ),
                reason="Inbound text exceeded maximum input bound.",
            )

        if trimmed.startswith("/"):
            parts = trimmed.split(maxsplit=1)
            raw_cmd_token = parts[0]
            args = parts[1].strip() if len(parts) > 1 else ""
            normalized_cmd = self._normalize_command_token(raw_cmd_token)

            if normalized_cmd is None or normalized_cmd not in _COMMAND_ALIASES:
                return RouteDecision(
                    outcome=RouteOutcomeKind.UNAVAILABLE,
                    response_text=(
                        f"Unsupported command `{raw_cmd_token}`. "
                        "Use /help to view supported commands."
                    ),
                    reason=f"Rejected unsupported slash command: {raw_cmd_token}",
                )

            cmd = _COMMAND_ALIASES[normalized_cmd]
            if cmd == SlashCommand.CANCEL:
                target_id = args if args else None
                signal = CancellationSignal(
                    source_channel=channel,
                    requested_by=sender_id,
                    target_turn_id=target_id,
                    target_chat_id=None,
                    scope=CancellationScope.TURN if target_id else CancellationScope.ALL_ACTIVE,
                )
                return RouteDecision(
                    outcome=RouteOutcomeKind.CANCEL,
                    cancellation=signal,
                    reason=f"Routed cancellation command ({cmd.value}).",
                )

            if cmd in _ROADMAP_DEFERRED_COMMANDS and cmd not in self._enabled_roadmap_commands:
                return RouteDecision(
                    outcome=RouteOutcomeKind.UNAVAILABLE,
                    response_text=(
                        f"Command `{cmd.value}` is planned for a later stage and is "
                        "not enabled yet in CMP-02. Use /help to list active commands."
                    ),
                    reason=f"Deferred roadmap command not enabled: {cmd.value}",
                )

            normalized_text = f"{cmd.value} {args}".strip()
            request = InboundUserRequest(
                channel=channel,
                sender_id=sender_id,
                chat_id=chat_id,
                raw_text=raw_text,
                normalized_text=normalized_text,
                command=cmd,
                command_args=args,
                update_id=update_id,
                message_id=message_id,
            )
            outcome = (
                RouteOutcomeKind.COMMAND_LOCAL
                if cmd in {SlashCommand.START, SlashCommand.HELP, SlashCommand.STATUS}
                else RouteOutcomeKind.TURN
            )
            return RouteDecision(
                outcome=outcome,
                request=request,
                reason=f"Routed whitelisted command {cmd.value}.",
            )

        request = InboundUserRequest(
            channel=channel,
            sender_id=sender_id,
            chat_id=chat_id,
            raw_text=raw_text,
            normalized_text=trimmed,
            command=None,
            command_args="",
            update_id=update_id,
            message_id=message_id,
        )
        return RouteDecision(
            outcome=RouteOutcomeKind.TURN,
            request=request,
            reason="Routed conversational turn.",
        )

    def _normalize_command_token(self, token: str) -> str | None:
        if "@" not in token:
            return token.lower()

        cmd_part, mention = token.split("@", 1)
        if not mention:
            return None
        if self._bot_username is not None and mention.lower() != self._bot_username:
            return None
        return cmd_part.lower()


@dataclass
class _TrackedTurn:
    turn_id: str
    chat_id: str
    channel: ChannelType
    task: asyncio.Task[Any]
    started_at: datetime


class ActiveTurnCoordinator(InboundTurnHandler, CancellationHandler):
    """Tracks in-flight asyncio tasks and coordinates local/IPC/Telegram cancellation."""

    def __init__(
        self,
        settings: ApplicationSettings,
        *,
        downstream_turn_handler: InboundTurnHandler | None = None,
    ) -> None:
        self._settings = settings
        self._downstream = downstream_turn_handler
        self._active_turns: dict[str, _TrackedTurn] = {}
        self._started_at = datetime.now(timezone.utc)

    @property
    def active_turn_ids(self) -> tuple[str, ...]:
        """Return IDs of currently tracked non-finished turns."""
        return tuple(
            turn_id
            for turn_id, entry in self._active_turns.items()
            if not entry.task.done()
        )

    def get_status_snapshot(self) -> dict[str, Any]:
        """Return runtime status dictionary without exposing secrets."""
        active_ids = self.active_turn_ids
        return {
            "app_name": self._settings.app_name,
            "environment": self._settings.aira_env.value,
            "timezone": self._settings.timezone,
            "telegram_enabled": self._settings.telegram_bot_enabled,
            "reasoning_core_attached": self._downstream is not None,
            "active_turn_count": len(active_ids),
            "active_turn_ids": list(active_ids),
            "started_at": self._started_at.isoformat(),
        }

    def register_turn_task(
        self,
        *,
        turn_id: str,
        chat_id: str,
        channel: ChannelType,
        task: asyncio.Task[Any],
    ) -> None:
        """Register an active asyncio.Task for cross-channel cancellation tracking."""
        self._active_turns[turn_id] = _TrackedTurn(
            turn_id=turn_id,
            chat_id=chat_id,
            channel=channel,
            task=task,
            started_at=datetime.now(timezone.utc),
        )

    def unregister_turn_task(self, turn_id: str) -> None:
        """Remove a completed or cancelled turn task from active tracking."""
        self._active_turns.pop(turn_id, None)

    async def handle_turn(self, request: InboundUserRequest) -> TurnResponse:
        """Serve built-in gateway commands or delegate active turns with cancellation tracking."""
        if request.command == SlashCommand.START:
            return TurnResponse(
                turn_id=request.request_id,
                text=(
                    f"{self._settings.app_name} gateway online "
                    f"(env: {self._settings.aira_env.value}). Use /help to see commands."
                ),
            )

        if request.command == SlashCommand.HELP:
            return TurnResponse(
                turn_id=request.request_id,
                text=(
                    "Available commands:\n"
                    "/help - Show available gateway commands\n"
                    "/status - Show active runtime status\n"
                    "/cancel - Cancel currently running turn\n"
                    "/start - Show gateway readiness message\n"
                    "Planned commands (/tasks, /notes, /briefing) are not enabled in this stage."
                ),
            )

        if request.command == SlashCommand.STATUS:
            snap = self.get_status_snapshot()
            return TurnResponse(
                turn_id=request.request_id,
                text=(
                    f"Status: OK | App: {snap['app_name']} | Env: {snap['environment']} | "
                    f"Reasoning core: {'attached' if snap['reasoning_core_attached'] else 'not attached'} | "
                    f"Active turns: {snap['active_turn_count']}"
                ),
                metadata=snap,
            )

        current_task = asyncio.current_task()
        registered_here = False
        if current_task is not None and request.request_id not in self._active_turns:
            self.register_turn_task(
                turn_id=request.request_id,
                chat_id=request.chat_id,
                channel=request.channel,
                task=current_task,
            )
            registered_here = True

        try:
            if self._downstream is None:
                return TurnResponse(
                    turn_id=request.request_id,
                    available=False,
                    text=(
                        "AI reasoning core is not connected yet in CMP-02. "
                        "Use /status or /help while operating in gateway-only mode."
                    ),
                )
            return await self._downstream.handle_turn(request)
        finally:
            if registered_here:
                self.unregister_turn_task(request.request_id)

    async def handle_cancel(self, signal: CancellationSignal) -> CancelResult:
        """Cancel matching active asyncio tasks without falsely claiming external API undo."""
        matched: list[_TrackedTurn] = []
        for entry in list(self._active_turns.values()):
            if entry.task.done():
                self._active_turns.pop(entry.turn_id, None)
                continue
            if signal.target_turn_id is not None:
                if entry.turn_id == signal.target_turn_id:
                    matched.append(entry)
            elif signal.target_chat_id is not None:
                if entry.chat_id == signal.target_chat_id:
                    matched.append(entry)
            else:
                matched.append(entry)

        if not matched:
            return CancelResult(
                acknowledged=True,
                cancelled_count=0,
                cancelled_turn_ids=(),
                already_idle=True,
                detail="No active local turn is running.",
            )

        cancelled_ids: list[str] = []
        tasks_to_wait: list[asyncio.Task[Any]] = []
        for entry in matched:
            if entry.task.cancel():
                cancelled_ids.append(entry.turn_id)
                tasks_to_wait.append(entry.task)

        if tasks_to_wait:
            await asyncio.wait(tasks_to_wait, timeout=0.05)

        return CancelResult(
            acknowledged=True,
            cancelled_count=len(cancelled_ids),
            cancelled_turn_ids=tuple(cancelled_ids),
            already_idle=(len(cancelled_ids) == 0),
            detail=(
                f"Cancelled {len(cancelled_ids)} active local turn(s). "
                "Already-dispatched external API requests cannot be undone locally."
            ),
        )
