"""Isolated offline tests for CMP-02 Communication Gateway."""

from __future__ import annotations

import asyncio
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from rich.console import Console
from typer.testing import CliRunner

from aira.config import ApplicationSettings, EnvironmentMode
from aira.interfaces import (
    ActiveTurnCoordinator,
    CLIDeliveryAdapter,
    CLIGateway,
    CommandRouter,
    DurableOffsetCursor,
    HttpxTelegramTransport,
    IPCControlError,
    LocalIPCClient,
    LocalIPCServer,
    MessagePaginator,
    OutboundMessage,
    OwnerAuthGuard,
    RouteOutcomeKind,
    SingleInstanceLock,
    SingleInstancePollingError,
    SlashCommand,
    TelegramChat,
    TelegramDeliveryAdapter,
    TelegramGatewayError,
    TelegramMessage,
    TelegramPollingGateway,
    TelegramRateLimitError,
    TelegramUpdate,
    TelegramUser,
    TelegramWebhookConflictError,
    TelegramWebhookInfo,
    create_cli_app,
    redact_bot_token,
)
from aira.ports import (
    CancellationHandler,
    CancellationSignal,
    ChannelDeliveryPort,
    ChannelType,
    InboundTurnHandler,
    InboundUserRequest,
    SecurityAuditHandler,
    SecurityIngressEvent,
    TurnResponse,
)

FAKE_BOT_TOKEN = "999999:SYNTHETIC-TEST-BOT-TOKEN-XYZ"
FAKE_IPC_TOKEN = "synthetic-ipc-auth-token-12345"
OWNER_USER_ID = 11223344


def make_test_settings(
    tmp_path: Path,
    *,
    socket_path: Path | None = None,
    telegram_enabled: bool = True,
) -> ApplicationSettings:
    """Create isolated ApplicationSettings with synthetic tokens and temp paths."""
    return ApplicationSettings(
        aira_env=EnvironmentMode.DEVELOPMENT,
        data_dir=tmp_path,
        sqlite_db_path=tmp_path / "aira.db",
        ipc_socket_path=socket_path or (tmp_path / "aira.sock"),
        telegram_bot_enabled=telegram_enabled,
        telegram_bot_token=SecretStr(FAKE_BOT_TOKEN),
        authorized_telegram_user_ids=(OWNER_USER_ID,),
        ipc_auth_token=SecretStr(FAKE_IPC_TOKEN),
    )


def make_update(
    *,
    update_id: int = 1,
    user_id: int = OWNER_USER_ID,
    chat_id: int | None = None,
    chat_type: str = "private",
    is_bot: bool = False,
    text: str | None = "Hello AIRA",
    include_from: bool = True,
    include_message: bool = True,
    message_id: int = 10,
) -> TelegramUpdate:
    """Construct a synthetic TelegramUpdate DTO without network interaction."""
    if not include_message:
        return TelegramUpdate(update_id=update_id, message=None)

    from_user = (
        TelegramUser(id=user_id, is_bot=is_bot, first_name="Owner")
        if include_from
        else None
    )
    resolved_chat_id = user_id if chat_id is None else chat_id
    return TelegramUpdate(
        update_id=update_id,
        message=TelegramMessage(
            message_id=message_id,
            date=1_700_000_000,
            chat=TelegramChat(id=resolved_chat_id, type=chat_type),
            from_user=from_user,
            text=text,
        ),
    )


class FakeTelegramTransport:
    """In-memory mock implementation of TelegramTransportProtocol."""

    def __init__(self) -> None:
        self.webhook_info = TelegramWebhookInfo(url="")
        self.poll_batches: list[list[TelegramUpdate] | Exception] = []
        self.poll_calls: list[dict[str, Any]] = []
        self.sent_messages: list[dict[str, Any]] = []
        self.chat_actions: list[dict[str, Any]] = []
        self.fail_typing = False
        self.fail_markdown_once = False
        self.closed = False
        self._next_msg_id = 1000

    async def get_webhook_info(self) -> TelegramWebhookInfo:
        return self.webhook_info

    async def get_updates(
        self,
        *,
        offset: int | None,
        timeout: int,
        allowed_updates: tuple[str, ...],
    ) -> list[TelegramUpdate]:
        self.poll_calls.append(
            {
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": allowed_updates,
            }
        )
        if not self.poll_batches:
            return []
        item = self.poll_batches.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> int:
        if self.fail_markdown_once and parse_mode is not None:
            self.fail_markdown_once = False
            raise TelegramGatewayError("Bad Request: can't parse entities", status_code=400)

        self._next_msg_id += 1
        self.sent_messages.append(
            {
                "message_id": self._next_msg_id,
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_to_message_id": reply_to_message_id,
                "reply_markup": reply_markup,
            }
        )
        return self._next_msg_id

    async def send_chat_action(self, *, chat_id: int, action: str = "typing") -> None:
        self.chat_actions.append({"chat_id": chat_id, "action": action})
        if self.fail_typing:
            raise TelegramGatewayError("Temporary chat action failure", status_code=503)

    async def aclose(self) -> None:
        self.closed = True


class RecordingAuditHandler(SecurityAuditHandler):
    """Collects emitted SecurityIngressEvent instances in memory."""

    def __init__(self) -> None:
        self.events: list[SecurityIngressEvent] = []

    async def record_security_event(self, event: SecurityIngressEvent) -> None:
        self.events.append(event)


class EchoTurnHandler(InboundTurnHandler):
    """Simple test turn handler echoing input text or blocking on an asyncio Event."""

    def __init__(self, *, block_event: asyncio.Event | None = None) -> None:
        self.requests: list[InboundUserRequest] = []
        self.block_event = block_event
        self.was_cancelled = False

    async def handle_turn(self, request: InboundUserRequest) -> TurnResponse:
        self.requests.append(request)
        if self.block_event is not None:
            try:
                await self.block_event.wait()
            except asyncio.CancelledError:
                self.was_cancelled = True
                raise
        return TurnResponse(
            turn_id=request.request_id,
            text=f"Reply to: {request.normalized_text}",
        )


def test_port_protocol_conformance() -> None:
    """Verify concrete adapters and coordinators satisfy port protocols at runtime."""
    transport = FakeTelegramTransport()
    tg_delivery = TelegramDeliveryAdapter(transport)
    cli_delivery = CLIDeliveryAdapter(console=Console(quiet=True))
    audit = RecordingAuditHandler()

    assert isinstance(tg_delivery, ChannelDeliveryPort)
    assert isinstance(cli_delivery, ChannelDeliveryPort)
    assert isinstance(audit, SecurityAuditHandler)
    assert tg_delivery.channel == ChannelType.TELEGRAM
    assert cli_delivery.channel == ChannelType.LOCAL_CLI

    with tempfile.TemporaryDirectory() as tmp:
        coordinator = ActiveTurnCoordinator(make_test_settings(Path(tmp)))
        assert isinstance(coordinator, InboundTurnHandler)
        assert isinstance(coordinator, CancellationHandler)


def test_owner_auth_guard_matrix() -> None:
    """Enforce owner whitelist, private chat check, non-bot check, and missing sender check."""
    guard = OwnerAuthGuard([OWNER_USER_ID])

    ok = guard.verify_telegram_update(make_update())
    assert ok.authorized is True
    assert ok.sender_id == str(OWNER_USER_ID)
    assert ok.chat_id == str(OWNER_USER_ID)
    assert ok.audit_event is None

    wrong_user = guard.verify_telegram_update(make_update(user_id=99999999))
    assert wrong_user.authorized is False
    assert wrong_user.audit_event is not None
    assert wrong_user.audit_event.event_type == "SECURITY_UNAUTHORIZED_SENDER"

    group_chat = guard.verify_telegram_update(
        make_update(chat_type="group", chat_id=-100555)
    )
    assert group_chat.authorized is False
    assert group_chat.audit_event is not None
    assert group_chat.audit_event.event_type == "TELEGRAM_NON_PRIVATE_CHAT"

    mismatched_private = guard.verify_telegram_update(
        make_update(chat_type="private", chat_id=88888888)
    )
    assert mismatched_private.authorized is False
    assert mismatched_private.audit_event is not None
    assert mismatched_private.audit_event.event_type == "TELEGRAM_NON_PRIVATE_CHAT"

    bot_sender = guard.verify_telegram_update(make_update(is_bot=True))
    assert bot_sender.authorized is False
    assert bot_sender.audit_event is not None
    assert bot_sender.audit_event.event_type == "TELEGRAM_BOT_SENDER_REJECTED"

    missing_sender = guard.verify_telegram_update(make_update(include_from=False))
    assert missing_sender.authorized is False
    assert missing_sender.audit_event is not None
    assert missing_sender.audit_event.event_type == "TELEGRAM_MISSING_SENDER"

    missing_msg = guard.verify_telegram_update(make_update(include_message=False))
    assert missing_msg.authorized is False
    assert missing_msg.audit_event is not None
    assert missing_msg.audit_event.event_type == "TELEGRAM_UNSUPPORTED_UPDATE"


def test_command_router_whitelist_mentions_and_bounds() -> None:
    """Test command allowlisting, @bot_username stripping, roadmap unavailability, and bounds."""
    router = CommandRouter(bot_username="aira_mochtar_bot")

    d_help = router.route(
        channel=ChannelType.TELEGRAM,
        sender_id="1",
        chat_id="1",
        raw_text="/help@aira_mochtar_bot",
    )
    assert d_help.outcome == RouteOutcomeKind.COMMAND_LOCAL
    assert d_help.request is not None
    assert d_help.request.command == SlashCommand.HELP

    d_other_bot = router.route(
        channel=ChannelType.TELEGRAM,
        sender_id="1",
        chat_id="1",
        raw_text="/help@other_bot",
    )
    assert d_other_bot.outcome == RouteOutcomeKind.UNAVAILABLE

    for alias in ("/cancel", "/stop", "/kill_all"):
        d_cancel = router.route(
            channel=ChannelType.TELEGRAM,
            sender_id="1",
            chat_id="1",
            raw_text=alias,
        )
        assert d_cancel.outcome == RouteOutcomeKind.CANCEL
        assert d_cancel.cancellation is not None

    d_tasks = router.route(
        channel=ChannelType.TELEGRAM,
        sender_id="1",
        chat_id="1",
        raw_text="/tasks",
    )
    assert d_tasks.outcome == RouteOutcomeKind.UNAVAILABLE

    router_with_tasks = CommandRouter(enabled_roadmap_commands=[SlashCommand.TASKS])
    d_tasks_enabled = router_with_tasks.route(
        channel=ChannelType.LOCAL_CLI,
        sender_id="1",
        chat_id="1",
        raw_text="/tasks list",
    )
    assert d_tasks_enabled.outcome == RouteOutcomeKind.TURN
    assert d_tasks_enabled.request is not None
    assert d_tasks_enabled.request.command == SlashCommand.TASKS
    assert d_tasks_enabled.request.command_args == "list"

    d_shell = router.route(
        channel=ChannelType.LOCAL_CLI,
        sender_id="1",
        chat_id="1",
        raw_text="/exec rm -rf /",
    )
    assert d_shell.outcome == RouteOutcomeKind.UNAVAILABLE

    d_empty = router.route(
        channel=ChannelType.LOCAL_CLI,
        sender_id="1",
        chat_id="1",
        raw_text="   ",
    )
    assert d_empty.outcome == RouteOutcomeKind.UNAVAILABLE

    d_oversized = router.route(
        channel=ChannelType.LOCAL_CLI,
        sender_id="1",
        chat_id="1",
        raw_text="x" * 32_001,
    )
    assert d_oversized.outcome == RouteOutcomeKind.UNAVAILABLE


def test_message_paginator_preserves_markdown_fences_and_length() -> None:
    """Verify <=4096 chunks, [k/N] headers, fenced code preservation, and single-line splits."""
    paginator = MessagePaginator(max_length=160)
    short = "Short reply under limit"
    assert paginator.paginate(short) == [short]

    code_lines = [f"print('line number {i} value={i * 2}')" for i in range(12)]
    payload = "Intro line\n```python\n" + "\n".join(code_lines) + "\n```\nOutro line."
    chunks = paginator.paginate(payload)

    assert len(chunks) > 1
    for idx, chunk in enumerate(chunks, start=1):
        assert len(chunk) <= 160
        assert chunk.startswith(f"[{idx}/{len(chunks)}]\n")
        assert chunk.count("```") % 2 == 0

    assert any("```python" in c for c in chunks[1:])

    unbroken = "A" * 500
    tg_paginator = MessagePaginator(max_length=120)
    hard_chunks = tg_paginator.paginate(unbroken)
    assert len(hard_chunks) >= 5
    assert all(len(c) <= 120 for c in hard_chunks)


async def test_httpx_transport_long_poll_rate_limit_conflict_and_redaction(tmp_path: Path) -> None:
    """Validate httpx transport timeouts, 429 retry_after, 409 conflict, and token scrubbing."""
    settings = make_test_settings(tmp_path)

    with pytest.raises(ValueError, match="read_timeout_seconds"):
        HttpxTelegramTransport(
            bot_token=FAKE_BOT_TOKEN,
            settings=settings,
            poll_timeout_seconds=30,
            read_timeout_seconds=30.0,
        )

    observed_requests: list[tuple[str, dict[str, Any]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8")) if request.content else {}
        observed_requests.append((request.url.path, body))
        if request.url.path.endswith("/getUpdates"):
            if body.get("offset") == 429:
                return httpx.Response(
                    429,
                    json={"ok": False, "description": "Too Many Requests", "parameters": {"retry_after": 7}},
                )
            if body.get("offset") == 409:
                return httpx.Response(
                    409,
                    json={"ok": False, "description": "Conflict: terminated by other getUpdates"},
                )
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": [
                        {
                            "update_id": 100,
                            "message": {
                                "message_id": 5,
                                "date": 1700000000,
                                "chat": {"id": OWNER_USER_ID, "type": "private"},
                                "from": {"id": OWNER_USER_ID, "is_bot": False, "first_name": "O"},
                                "text": "/status",
                            },
                        }
                    ],
                },
            )
        if request.url.path.endswith("/getWebhookInfo"):
            return httpx.Response(200, json={"ok": True, "result": {"url": ""}})
        raise httpx.ConnectError(f"Network down calling https://api.telegram.org/bot{FAKE_BOT_TOKEN}/sendMessage")

    transport = HttpxTelegramTransport(
        bot_token=FAKE_BOT_TOKEN,
        settings=settings,
        poll_timeout_seconds=10,
        read_timeout_seconds=15.0,
        transport=httpx.MockTransport(handler),
    )

    try:
        updates = await transport.get_updates(offset=50, timeout=10, allowed_updates=("message",))
        assert len(updates) == 1
        assert updates[0].update_id == 100
        assert observed_requests[-1][1]["allowed_updates"] == ["message"]
        assert FAKE_BOT_TOKEN not in redact_bot_token(observed_requests[-1][0], settings=settings)

        with pytest.raises(TelegramRateLimitError) as rate_exc:
            await transport.get_updates(offset=429, timeout=10, allowed_updates=("message",))
        assert rate_exc.value.retry_after == 7.0

        with pytest.raises(TelegramWebhookConflictError):
            await transport.get_updates(offset=409, timeout=10, allowed_updates=("message",))

        with pytest.raises(TelegramGatewayError) as conn_exc:
            await transport.send_message(chat_id=OWNER_USER_ID, text="hi")
        assert FAKE_BOT_TOKEN not in str(conn_exc.value)
        assert "[REDACTED_SECRET]" in str(conn_exc.value)
        assert all("/deleteWebhook" not in path for path, _ in observed_requests)
    finally:
        await transport.aclose()


async def test_telegram_delivery_adapter_pagination_fallback_and_typing() -> None:
    """Verify delivery pagination, Markdown->plain HTTP 400 fallback, and best-effort typing."""
    fake_transport = FakeTelegramTransport()
    fake_transport.fail_typing = True
    fake_transport.fail_markdown_once = True

    adapter = TelegramDeliveryAdapter(
        fake_transport,
        paginator=MessagePaginator(max_length=80),
        bot_token=FAKE_BOT_TOKEN,
    )

    # Must not raise even when typing fails.
    await adapter.send_typing_indicator(str(OWNER_USER_ID))
    assert len(fake_transport.chat_actions) == 1

    receipt = await adapter.send_message(
        OutboundMessage(
            channel=ChannelType.TELEGRAM,
            chat_id=str(OWNER_USER_ID),
            text=("Word " * 30).strip(),
            parse_mode="Markdown",
        )
    )
    assert receipt.delivered is True
    assert receipt.chunk_count >= 2
    assert receipt.used_plain_text_fallback is True
    assert fake_transport.sent_messages[0]["parse_mode"] is None


def test_durable_offset_cursor_atomic_persistence_and_permissions(tmp_path: Path) -> None:
    """Persist next_update_id atomically with 0600 mode and enforce monotonicity."""
    cursor_path = tmp_path / "telegram_offset.json"
    cursor = DurableOffsetCursor(cursor_path)
    assert cursor.load_next_offset() is None

    cursor.save_next_offset(101)
    assert cursor.load_next_offset() == 101
    assert stat.S_IMODE(cursor_path.stat().st_mode) == 0o600

    # Backwards save is ignored safely.
    cursor.save_next_offset(50)
    assert DurableOffsetCursor(cursor_path).load_next_offset() == 101


def test_single_instance_lock_prevents_concurrent_poller(tmp_path: Path) -> None:
    """Ensure SingleInstanceLock blocks a second poller and releases cleanly."""
    lock_path = tmp_path / "polling.lock"
    lock1 = SingleInstanceLock(lock_path)
    lock2 = SingleInstanceLock(lock_path)

    lock1.acquire()
    try:
        assert lock1.is_acquired is True
        assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600
        with pytest.raises(SingleInstancePollingError):
            lock2.acquire()
    finally:
        lock1.release()

    assert lock1.is_acquired is False
    lock2.acquire()
    lock2.release()


async def test_gateway_webhook_conflict_fail_closed_and_backoff(tmp_path: Path) -> None:
    """Verify webhook conflict fails without deleting webhook, and backoff recovers on errors."""
    settings = make_test_settings(tmp_path)
    coordinator = ActiveTurnCoordinator(settings)
    audit = RecordingAuditHandler()

    conflict_transport = FakeTelegramTransport()
    conflict_transport.webhook_info = TelegramWebhookInfo(url="https://example.com/hook")

    gw_conflict = TelegramPollingGateway(
        settings=settings,
        transport=conflict_transport,
        delivery=TelegramDeliveryAdapter(conflict_transport),
        auth_guard=OwnerAuthGuard.from_settings(settings),
        router=CommandRouter(),
        turn_handler=coordinator,
        cancel_handler=coordinator,
        audit_handler=audit,
    )

    with pytest.raises(TelegramWebhookConflictError):
        await gw_conflict.run_polling_loop(max_polls=1)

    backoff_transport = FakeTelegramTransport()
    backoff_transport.poll_batches = [
        TelegramGatewayError("Temporary 502", status_code=502),
        TelegramRateLimitError("Rate limited", retry_after=0.05),
        [make_update(update_id=201, text="/status")],
    ]
    gw_backoff = TelegramPollingGateway(
        settings=settings,
        transport=backoff_transport,
        delivery=TelegramDeliveryAdapter(backoff_transport),
        auth_guard=OwnerAuthGuard.from_settings(settings),
        router=CommandRouter(),
        turn_handler=coordinator,
        cancel_handler=coordinator,
        base_backoff_seconds=0.01,
        max_backoff_seconds=0.1,
        jitter_fn=lambda _d: 0.0,
    )
    await gw_backoff.run_polling_loop(max_polls=3)
    assert any("Status: OK" in m["text"] for m in backoff_transport.sent_messages)
    await gw_backoff.stop()


async def test_gateway_rejects_unauthorized_silently_and_deduplicates_updates(tmp_path: Path) -> None:
    """Verify rejected updates emit audit only (no reply) and duplicate update_id is skipped."""
    settings = make_test_settings(tmp_path)
    transport = FakeTelegramTransport()
    audit = RecordingAuditHandler()
    echo = EchoTurnHandler()
    coordinator = ActiveTurnCoordinator(settings, downstream_turn_handler=echo)

    gw = TelegramPollingGateway(
        settings=settings,
        transport=transport,
        delivery=TelegramDeliveryAdapter(transport),
        auth_guard=OwnerAuthGuard.from_settings(settings),
        router=CommandRouter(),
        turn_handler=coordinator,
        cancel_handler=coordinator,
        audit_handler=audit,
    )

    # Unauthorized sender gets audited, zero replies delivered, offset still advances.
    unauth = make_update(update_id=10, user_id=777777)
    assert await gw.process_update(unauth) is True
    assert len(audit.events) == 1
    assert audit.events[0].event_type == "SECURITY_UNAUTHORIZED_SENDER"
    assert transport.sent_messages == []

    # Authorized message executes once; duplicate update_id=11 is ignored cleanly.
    auth_update = make_update(update_id=11, text="Hello once")
    assert await gw.process_update(auth_update) is True
    assert await gw.process_update(auth_update) is False
    await gw.wait_for_background_tasks()

    assert len(echo.requests) == 1
    assert len(transport.sent_messages) == 1
    assert transport.sent_messages[0]["text"] == "Reply to: Hello once"
    assert transport.chat_actions == [{"chat_id": OWNER_USER_ID, "action": "typing"}]


async def test_nonblocking_turn_and_telegram_cancel_under_load(tmp_path: Path) -> None:
    """Ensure /cancel immediately cancels a blocked background turn and reports honestly."""
    settings = make_test_settings(tmp_path)
    transport = FakeTelegramTransport()
    block_event = asyncio.Event()
    slow_handler = EchoTurnHandler(block_event=block_event)
    coordinator = ActiveTurnCoordinator(settings, downstream_turn_handler=slow_handler)

    gw = TelegramPollingGateway(
        settings=settings,
        transport=transport,
        delivery=TelegramDeliveryAdapter(transport),
        auth_guard=OwnerAuthGuard.from_settings(settings),
        router=CommandRouter(),
        turn_handler=coordinator,
        cancel_handler=coordinator,
    )

    await gw.process_update(make_update(update_id=300, text="Long running task"))
    await asyncio.sleep(0.02)
    assert gw.background_task_count == 1
    assert len(coordinator.active_turn_ids) == 1

    await gw.process_update(make_update(update_id=301, text="/cancel"))
    await gw.wait_for_background_tasks(timeout=1.0)

    assert slow_handler.was_cancelled is True
    assert gw.background_task_count == 0
    assert any(
        "Cancelled 1 active local turn(s)" in msg["text"]
        and "cannot be undone locally" in msg["text"]
        for msg in transport.sent_messages
    )


async def test_local_ipc_security_stale_socket_and_cross_process_cancel(tmp_path: Path) -> None:
    """Verify 0600 socket, invalid IPC token audit, stale socket check, and CLI->Telegram cancel."""
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="aira_") as sock_dir_str:
        sock_path = Path(sock_dir_str) / "aira.sock"
        settings = make_test_settings(tmp_path, socket_path=sock_path)
        transport = FakeTelegramTransport()
        block_event = asyncio.Event()
        slow_handler = EchoTurnHandler(block_event=block_event)
        coordinator = ActiveTurnCoordinator(settings, downstream_turn_handler=slow_handler)
        audit = RecordingAuditHandler()

        gw = TelegramPollingGateway(
            settings=settings,
            transport=transport,
            delivery=TelegramDeliveryAdapter(transport),
            auth_guard=OwnerAuthGuard.from_settings(settings),
            router=CommandRouter(),
            turn_handler=coordinator,
            cancel_handler=coordinator,
            audit_handler=audit,
        )

        # Refuse non-socket path protection.
        regular_file = Path(sock_dir_str) / "not_a_socket"
        regular_file.write_text("occupied", encoding="utf-8")
        bad_server = LocalIPCServer(
            socket_path=regular_file,
            auth_token=FAKE_IPC_TOKEN,
            cancel_handler=coordinator,
        )
        with pytest.raises(IPCControlError, match="non-socket"):
            await bad_server.start()

        server = LocalIPCServer(
            socket_path=sock_path,
            auth_token=FAKE_IPC_TOKEN,
            cancel_handler=coordinator,
            status_provider=coordinator.get_status_snapshot,
            audit_handler=audit,
        )
        await server.start()
        try:
            assert stat.S_IMODE(sock_path.stat().st_mode) == 0o600

            # Invalid IPC token rejected and audited without leaking tokens.
            bad_client = LocalIPCClient(socket_path=sock_path, auth_token="wrong-ipc-token")
            with pytest.raises(IPCControlError, match="Unauthorized IPC token"):
                await bad_client.send_cancel()
            assert any(e.event_type == "SECURITY_INVALID_IPC_TOKEN" for e in audit.events)

            # Start blocked Telegram turn, then cancel from CLI gateway via authenticated IPC.
            await gw.process_update(make_update(update_id=400, text="Wait forever"))
            await asyncio.sleep(0.02)
            assert len(coordinator.active_turn_ids) == 1

            cli_gw = CLIGateway(settings=settings, console=Console(quiet=True))
            cancel_res, source = await cli_gw.cancel_via_cli()
            await gw.wait_for_background_tasks(timeout=1.0)

            assert source == "ipc"
            assert cancel_res.cancelled_count == 1
            assert slow_handler.was_cancelled is True

            status_snap, status_source = await cli_gw.status_via_cli()
            assert status_source == "ipc"
            assert status_snap["active_turn_count"] == 0

            # Active listener collision refuses to steal a live socket.
            competing_server = LocalIPCServer(
                socket_path=sock_path,
                auth_token=FAKE_IPC_TOKEN,
                cancel_handler=coordinator,
            )
            with pytest.raises(IPCControlError, match="already listening"):
                await competing_server.start()
        finally:
            await server.stop()
            await gw.stop()

        # Simulate stale socket left behind after crash (create socket, close fd without unlink).
        import socket as stdlib_socket

        stale_sock = stdlib_socket.socket(stdlib_socket.AF_UNIX, stdlib_socket.SOCK_STREAM)
        stale_sock.bind(str(sock_path))
        stale_sock.close()
        assert sock_path.exists()

        recovered_server = LocalIPCServer(
            socket_path=sock_path,
            auth_token=FAKE_IPC_TOKEN,
            cancel_handler=coordinator,
        )
        await recovered_server.start()
        assert recovered_server.is_running is True
        await recovered_server.stop()


async def test_gateway_graceful_shutdown_drains_and_closes(tmp_path: Path) -> None:
    """Verify stop() cancels active turns, releases polling lock, and closes transport."""
    settings = make_test_settings(tmp_path)
    transport = FakeTelegramTransport()
    block_event = asyncio.Event()
    slow_handler = EchoTurnHandler(block_event=block_event)
    coordinator = ActiveTurnCoordinator(settings, downstream_turn_handler=slow_handler)
    lock_path = tmp_path / "telegram_polling.lock"
    lock = SingleInstanceLock(lock_path)

    gw = TelegramPollingGateway(
        settings=settings,
        transport=transport,
        delivery=TelegramDeliveryAdapter(transport),
        auth_guard=OwnerAuthGuard.from_settings(settings),
        router=CommandRouter(),
        turn_handler=coordinator,
        cancel_handler=coordinator,
        instance_lock=lock,
    )
    lock.acquire()
    await gw.process_update(make_update(update_id=500, text="Background turn"))
    await asyncio.sleep(0.02)

    await gw.stop(cancel_active_turns=True, drain_timeout=1.0)
    assert slow_handler.was_cancelled is True
    assert lock.is_acquired is False
    assert transport.closed is True


async def test_cli_gateway_interactive_loop_and_local_fallback(tmp_path: Path) -> None:
    """Exercise interactive CLIGateway lines, /help, /cancel fallback, EOF, and exit."""
    settings = make_test_settings(tmp_path)
    lines: list[str] = ["/help", "hello cli", "/cancel", "exit"]

    def reader() -> str:
        if not lines:
            raise EOFError
        return lines.pop(0)

    out_console = Console(record=True, width=120)
    echo = EchoTurnHandler()
    coordinator = ActiveTurnCoordinator(settings, downstream_turn_handler=echo)
    cli_gw = CLIGateway(
        settings=settings,
        coordinator=coordinator,
        console=out_console,
    )
    await cli_gw.run_chat_loop(input_reader=reader)
    exported = out_console.export_text()

    assert "Available commands:" in exported
    assert "Reply to: hello cli" in exported
    assert "No active local turn is running." in exported
    assert "Goodbye." in exported
    assert FAKE_BOT_TOKEN not in exported
    assert FAKE_IPC_TOKEN not in exported


def test_typer_cli_commands_and_secret_non_exposure(tmp_path: Path) -> None:
    """Invoke Typer help/status/cancel commands cleanly via CliRunner without exposing secrets."""
    settings = make_test_settings(tmp_path)
    out_console = Console(record=True, width=120)
    app = create_cli_app(settings=settings, console=out_console)
    runner = CliRunner()

    res_help = runner.invoke(app, ["help"])
    assert res_help.exit_code == 0

    res_status = runner.invoke(app, ["status"])
    assert res_status.exit_code == 0

    res_cancel = runner.invoke(app, ["cancel"])
    assert res_cancel.exit_code == 0

    recorded = out_console.export_text()
    assert "AIRA Help" in recorded
    assert "AIRA Status" in recorded
    assert "Acknowledged (local):" in recorded
    assert FAKE_BOT_TOKEN not in recorded
    assert FAKE_IPC_TOKEN not in recorded
