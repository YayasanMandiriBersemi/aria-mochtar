"""Telegram Long Polling gateway, delivery adapter, lock, cursor, and redaction."""

from __future__ import annotations

import asyncio
import fcntl
import json
import logging
import os
import random
import re
import tempfile
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from urllib.parse import quote

import httpx
from pydantic import SecretStr

from aira.config import ApplicationSettings
from aira.config.exceptions import REDACTED_PLACEHOLDER
from aira.interfaces.auth_guard import OwnerAuthGuard
from aira.interfaces.models import (
    ChannelType,
    InboundUserRequest,
    OutboundMessage,
    TelegramUpdate,
    TelegramWebhookInfo,
)
from aira.interfaces.paginator import MessagePaginator
from aira.interfaces.router import ActiveTurnCoordinator, CommandRouter, RouteOutcomeKind
from aira.ports.channel import (
    CancellationHandler,
    ChannelDeliveryPort,
    DeliveryReceipt,
    InboundTurnHandler,
    SecurityAuditHandler,
)

logger = logging.getLogger(__name__)

_BOT_URL_TOKEN_RE = re.compile(r"(/bot)([^/\s]+)(/)")
_BOT_LITERAL_TOKEN_RE = re.compile(r"\bbot(\d{4,}:[A-Za-z0-9_-]{8,})\b")

# Tracks lock file paths acquired within the current Python process so duplicate
# pollers in the same process always fail cleanly even across flock quirks.
_IN_PROCESS_LOCK_PATHS: set[Path] = set()


class TelegramGatewayError(Exception):
    """Base error raised by the Telegram gateway with token-redacted details."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(redact_bot_token(message))


class TelegramWebhookConflictError(TelegramGatewayError):
    """Raised when polling encounters an active webhook or 409 conflict."""


class SingleInstancePollingError(TelegramGatewayError):
    """Raised when another polling instance already holds the single-instance lock."""


class TelegramRateLimitError(TelegramGatewayError):
    """Raised when Telegram Bot API returns HTTP 429 with Retry-After."""

    def __init__(self, message: str, *, retry_after: float) -> None:
        self.retry_after = max(0.0, float(retry_after))
        super().__init__(message, status_code=429)


def redact_bot_token(
    text: str,
    *,
    settings: ApplicationSettings | None = None,
    bot_token: str | None = None,
) -> str:
    """Scrub Telegram bot tokens and configured secrets from strings and URLs."""
    sanitized = text
    if settings is not None:
        sanitized = settings.redact_text(sanitized)

    if bot_token:
        for candidate in (bot_token, quote(bot_token, safe="")):
            if candidate:
                sanitized = sanitized.replace(candidate, REDACTED_PLACEHOLDER)

    sanitized = _BOT_URL_TOKEN_RE.sub(rf"\1{REDACTED_PLACEHOLDER}\3", sanitized)
    sanitized = _BOT_LITERAL_TOKEN_RE.sub(f"bot{REDACTED_PLACEHOLDER}", sanitized)
    return sanitized


class DurableOffsetCursor:
    """Persists the next Telegram getUpdates offset atomically on disk."""

    def __init__(self, cursor_path: Path) -> None:
        self._path = cursor_path
        self._highest_next_offset: int | None = None

    @property
    def path(self) -> Path:
        """Return path of the cursor state file."""
        return self._path

    def load_next_offset(self) -> int | None:
        """Read the persisted next_update_id offset if present."""
        if not self._path.exists():
            return self._highest_next_offset

        try:
            raw = self._path.read_text(encoding="utf-8").strip()
            if not raw:
                return self._highest_next_offset
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise TelegramGatewayError(f"Failed to load Telegram offset cursor: {exc}") from None

        value = data.get("next_update_id")
        if value is None:
            return self._highest_next_offset
        if not isinstance(value, int) or isinstance(value, bool):
            raise TelegramGatewayError("Invalid next_update_id type in Telegram offset cursor.")

        self._highest_next_offset = (
            value
            if self._highest_next_offset is None
            else max(self._highest_next_offset, value)
        )
        return self._highest_next_offset

    def save_next_offset(self, next_update_id: int) -> None:
        """Atomically persist a strictly non-decreasing next_update_id cursor."""
        if self._highest_next_offset is not None and next_update_id < self._highest_next_offset:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"next_update_id": next_update_id})

        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent),
            prefix=f".{self._path.name}.",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_name)
        try:
            os.chmod(tmp_path, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self._path)
            os.chmod(self._path, 0o600)
        except OSError as exc:
            tmp_path.unlink(missing_ok=True)
            raise TelegramGatewayError(f"Failed to persist Telegram offset cursor: {exc}") from None

        self._highest_next_offset = next_update_id


class SingleInstanceLock:
    """Non-blocking advisory file lock ensuring one polling gateway runs per bot."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path.resolve()
        self._fd: int | None = None

    @property
    def is_acquired(self) -> bool:
        """Return whether this lock instance currently owns the lock."""
        return self._fd is not None

    def acquire(self) -> None:
        """Acquire exclusive non-blocking polling lock or raise SingleInstancePollingError."""
        if self._fd is not None:
            return

        if self._lock_path in _IN_PROCESS_LOCK_PATHS:
            raise SingleInstancePollingError(
                "Another Telegram polling gateway instance is already running in this process."
            )

        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.chmod(self._lock_path, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise SingleInstancePollingError(
                "Another Telegram polling process already holds the single-instance lock."
            ) from None
        except OSError as exc:
            os.close(fd)
            raise SingleInstancePollingError(f"Unable to acquire polling lock: {exc}") from None

        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
        self._fd = fd
        _IN_PROCESS_LOCK_PATHS.add(self._lock_path)

    def release(self) -> None:
        """Release the lock and close the underlying file descriptor safely."""
        if self._fd is None:
            return
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd = None
            _IN_PROCESS_LOCK_PATHS.discard(self._lock_path)

    def __enter__(self) -> SingleInstanceLock:
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


@runtime_checkable
class TelegramTransportProtocol(Protocol):
    """Transport boundary wrapping Telegram Bot API HTTP methods."""

    async def get_webhook_info(self) -> TelegramWebhookInfo:
        """Fetch current bot webhook configuration for conflict detection."""
        ...

    async def get_updates(
        self,
        *,
        offset: int | None,
        timeout: int,
        allowed_updates: tuple[str, ...],
    ) -> list[TelegramUpdate]:
        """Fetch pending updates using Telegram Long Polling."""
        ...

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> int:
        """Send an outbound Telegram message and return its assigned message_id."""
        ...

    async def send_chat_action(self, *, chat_id: int, action: str = "typing") -> None:
        """Send a typing/chat action indicator to the target private chat."""
        ...

    async def aclose(self) -> None:
        """Close any underlying network connection pool."""
        ...


class HttpxTelegramTransport:
    """Async Telegram Bot API client over httpx with strict token redaction."""

    def __init__(
        self,
        *,
        bot_token: SecretStr | str,
        settings: ApplicationSettings | None = None,
        base_url: str = "https://api.telegram.org",
        poll_timeout_seconds: int = 30,
        read_timeout_seconds: float = 40.0,
        connect_timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if read_timeout_seconds <= poll_timeout_seconds:
            raise ValueError(
                "read_timeout_seconds must exceed poll_timeout_seconds so long polling "
                "does not abort early."
            )
        token_value = (
            bot_token.get_secret_value()
            if isinstance(bot_token, SecretStr)
            else str(bot_token)
        ).strip()
        if not token_value:
            raise ValueError("Telegram bot token must not be empty.")

        self._token_value = token_value
        self._settings = settings
        self._base_url = base_url.rstrip("/")
        self._poll_timeout_seconds = poll_timeout_seconds
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=connect_timeout_seconds,
                read=read_timeout_seconds,
                write=10.0,
                pool=10.0,
            ),
            transport=transport,
        )

    def _sanitize(self, message: str) -> str:
        return redact_bot_token(
            message,
            settings=self._settings,
            bot_token=self._token_value,
        )

    async def _request(
        self,
        method: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> Any:
        url = f"{self._base_url}/bot{self._token_value}/{method}"
        try:
            response = await self._client.post(
                url,
                json=payload or {},
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            safe_detail = self._sanitize(f"Telegram HTTP error on {method}: {exc}")
            raise TelegramGatewayError(safe_detail) from None

        try:
            data = response.json()
        except ValueError:
            safe_detail = self._sanitize(
                f"Non-JSON response (HTTP {response.status_code}) from Telegram {method}."
            )
            raise TelegramGatewayError(safe_detail, status_code=response.status_code) from None

        if response.status_code == 429:
            params = data.get("parameters") if isinstance(data, dict) else {}
            retry_after = (
                params.get("retry_after", 5.0) if isinstance(params, dict) else 5.0
            )
            desc = (
                data.get("description", "Rate limited by Telegram Bot API")
                if isinstance(data, dict)
                else "Rate limited by Telegram Bot API"
            )
            raise TelegramRateLimitError(
                self._sanitize(f"Telegram 429 on {method}: {desc}"),
                retry_after=float(retry_after),
            )

        if response.status_code == 409:
            desc = (
                data.get("description", "Conflict with webhook or concurrent poller")
                if isinstance(data, dict)
                else "Conflict"
            )
            raise TelegramWebhookConflictError(
                self._sanitize(f"Telegram 409 conflict on {method}: {desc}"),
                status_code=409,
            )

        ok_flag = data.get("ok") if isinstance(data, dict) else False
        if response.status_code >= 400 or not ok_flag:
            desc = (
                data.get("description", f"HTTP {response.status_code}")
                if isinstance(data, dict)
                else f"HTTP {response.status_code}"
            )
            raise TelegramGatewayError(
                self._sanitize(f"Telegram API error ({response.status_code}) on {method}: {desc}"),
                status_code=response.status_code,
            )

        return data.get("result")

    async def get_webhook_info(self) -> TelegramWebhookInfo:
        """Query Telegram getWebhookInfo without altering webhook state."""
        result = await self._request("getWebhookInfo")
        return TelegramWebhookInfo.model_validate(result or {})

    async def get_updates(
        self,
        *,
        offset: int | None,
        timeout: int,
        allowed_updates: tuple[str, ...] = ("message",),
    ) -> list[TelegramUpdate]:
        """Execute a Telegram long-polling getUpdates call."""
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": list(allowed_updates),
        }
        if offset is not None:
            payload["offset"] = offset

        result = await self._request("getUpdates", payload=payload)
        if not isinstance(result, list):
            raise TelegramGatewayError("Unexpected getUpdates result format from Telegram API.")
        return [TelegramUpdate.model_validate(item) for item in result]

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        reply_to_message_id: int | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> int:
        """Call Telegram sendMessage and return the created message_id."""
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        result = await self._request("sendMessage", payload=payload)
        if not isinstance(result, dict) or "message_id" not in result:
            raise TelegramGatewayError("Telegram sendMessage response did not return message_id.")
        return int(result["message_id"])

    async def send_chat_action(self, *, chat_id: int, action: str = "typing") -> None:
        """Call Telegram sendChatAction."""
        await self._request(
            "sendChatAction",
            payload={"chat_id": chat_id, "action": action},
        )

    async def aclose(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()


class TelegramDeliveryAdapter(ChannelDeliveryPort):
    """Outbound ChannelDeliveryPort adapter for Telegram private chats."""

    def __init__(
        self,
        transport: TelegramTransportProtocol,
        *,
        paginator: MessagePaginator | None = None,
        settings: ApplicationSettings | None = None,
        bot_token: str | None = None,
    ) -> None:
        self._transport = transport
        self._paginator = paginator or MessagePaginator()
        self._settings = settings
        self._bot_token = bot_token

    @property
    def channel(self) -> ChannelType:
        """Identify this adapter as the Telegram channel."""
        return ChannelType.TELEGRAM

    async def send_typing_indicator(self, chat_id: str) -> None:
        """Best-effort typing ack; swallows transport errors with redacted warning."""
        try:
            await self._transport.send_chat_action(chat_id=int(chat_id), action="typing")
        except Exception as exc:  # noqa: BLE001 - typing failure must not abort turns
            safe = redact_bot_token(
                f"Best-effort typing indicator failed for chat {chat_id}: {exc}",
                settings=self._settings,
                bot_token=self._bot_token,
            )
            logger.warning(safe)

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """Send paginated outbound messages with plain-text fallback on parse rejection."""
        chunks = self._paginator.paginate(message.text)
        chat_id_int = int(message.chat_id)
        reply_to_int = (
            int(message.reply_to_message_id)
            if message.reply_to_message_id is not None
            else None
        )

        reply_markup = self._build_reply_markup(message)
        sent_ids: list[str] = []
        used_fallback = False

        for index, chunk in enumerate(chunks):
            chunk_reply_to = reply_to_int if index == 0 else None
            chunk_markup = reply_markup if index == len(chunks) - 1 else None
            try:
                msg_id = await self._transport.send_message(
                    chat_id=chat_id_int,
                    text=chunk,
                    parse_mode=message.parse_mode,
                    reply_to_message_id=chunk_reply_to,
                    reply_markup=chunk_markup,
                )
            except TelegramGatewayError as exc:
                if message.parse_mode is not None and exc.status_code == 400:
                    used_fallback = True
                    msg_id = await self._transport.send_message(
                        chat_id=chat_id_int,
                        text=chunk,
                        parse_mode=None,
                        reply_to_message_id=chunk_reply_to,
                        reply_markup=chunk_markup,
                    )
                else:
                    raise
            sent_ids.append(str(msg_id))

        return DeliveryReceipt(
            channel=ChannelType.TELEGRAM,
            chat_id=message.chat_id,
            delivered=True,
            chunk_count=len(chunks),
            message_ids=tuple(sent_ids),
            used_plain_text_fallback=used_fallback,
        )

    def _build_reply_markup(self, message: OutboundMessage) -> dict[str, Any] | None:
        if not message.inline_keyboard:
            return None
        rows: list[list[dict[str, str]]] = []
        for row in message.inline_keyboard:
            rendered_row: list[dict[str, str]] = []
            for btn in row:
                btn_dict: dict[str, str] = {"text": btn.text}
                if btn.callback_data is not None:
                    btn_dict["callback_data"] = btn.callback_data
                if btn.url is not None:
                    btn_dict["url"] = btn.url
                rendered_row.append(btn_dict)
            if rendered_row:
                rows.append(rendered_row)
        return {"inline_keyboard": rows} if rows else None


class TelegramPollingGateway:
    """Single-instance Telegram Long Polling ingress and lifecycle coordinator."""

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        transport: TelegramTransportProtocol,
        delivery: ChannelDeliveryPort,
        auth_guard: OwnerAuthGuard,
        router: CommandRouter,
        turn_handler: InboundTurnHandler,
        cancel_handler: CancellationHandler,
        audit_handler: SecurityAuditHandler | None = None,
        coordinator: ActiveTurnCoordinator | None = None,
        offset_cursor: DurableOffsetCursor | None = None,
        instance_lock: SingleInstanceLock | None = None,
        poll_timeout_seconds: int = 30,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 30.0,
        jitter_fn: Callable[[float], float] | None = None,
        max_seen_updates: int = 4096,
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._delivery = delivery
        self._auth_guard = auth_guard
        self._router = router
        self._turn_handler = turn_handler
        self._cancel_handler = cancel_handler
        self._audit_handler = audit_handler
        self._coordinator = (
            coordinator
            if coordinator is not None
            else (turn_handler if isinstance(turn_handler, ActiveTurnCoordinator) else None)
        )
        self._offset_cursor = offset_cursor or DurableOffsetCursor(
            settings.data_dir / "telegram_offset.json"
        )
        self._instance_lock = instance_lock or SingleInstanceLock(
            settings.data_dir / "telegram_polling.lock"
        )
        self._poll_timeout_seconds = poll_timeout_seconds
        self._base_backoff_seconds = base_backoff_seconds
        self._max_backoff_seconds = max_backoff_seconds
        self._jitter_fn = jitter_fn or (lambda delay: random.uniform(0.0, delay * 0.25))
        self._seen_order: deque[int] = deque()
        self._seen_set: set[int] = set()
        self._max_seen_updates = max_seen_updates
        self._stop_event = asyncio.Event()
        self._background_tasks: set[asyncio.Task[None]] = set()

    @property
    def background_task_count(self) -> int:
        """Return count of currently active background turn tasks."""
        return len(self._background_tasks)

    async def verify_no_webhook_conflict(self) -> None:
        """Fail closed if a Telegram webhook is configured; never deletes webhooks."""
        info = await self._transport.get_webhook_info()
        if info.url.strip():
            raise TelegramWebhookConflictError(
                "Cannot start Telegram long polling while a webhook URL is active. "
                "Remove the webhook explicitly out-of-band if polling is intended.",
                status_code=409,
            )

    def _is_duplicate_update(self, update_id: int) -> bool:
        return update_id in self._seen_set

    def _mark_update_seen(self, update_id: int) -> None:
        if update_id in self._seen_set:
            return
        self._seen_set.add(update_id)
        self._seen_order.append(update_id)
        while len(self._seen_order) > self._max_seen_updates:
            evicted = self._seen_order.popleft()
            self._seen_set.discard(evicted)

    async def process_update(self, update: TelegramUpdate) -> bool:
        """Authenticate, route, and dispatch one TelegramUpdate. Returns True if newly handled."""
        if self._is_duplicate_update(update.update_id):
            return False

        self._mark_update_seen(update.update_id)
        auth = self._auth_guard.verify_telegram_update(update)
        if not auth.authorized:
            if auth.audit_event is not None and self._audit_handler is not None:
                try:
                    await self._audit_handler.record_security_event(auth.audit_event)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(self._redact(f"Security audit sink error: {exc}"))
            self._offset_cursor.save_next_offset(update.update_id + 1)
            return True

        assert auth.sender_id is not None
        assert auth.chat_id is not None
        assert update.message is not None

        raw_text = update.message.text or update.message.caption or ""
        message_id_str = str(update.message.message_id)
        decision = self._router.route(
            channel=ChannelType.TELEGRAM,
            sender_id=auth.sender_id,
            chat_id=auth.chat_id,
            raw_text=raw_text,
            update_id=update.update_id,
            message_id=message_id_str,
        )

        self._offset_cursor.save_next_offset(update.update_id + 1)

        if decision.outcome == RouteOutcomeKind.CANCEL:
            assert decision.cancellation is not None
            result = await self._cancel_handler.handle_cancel(decision.cancellation)
            ack_text = result.detail or result.external_call_warning
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.TELEGRAM,
                    chat_id=auth.chat_id,
                    text=ack_text,
                    reply_to_message_id=message_id_str,
                )
            )
            return True

        if decision.outcome == RouteOutcomeKind.UNAVAILABLE:
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.TELEGRAM,
                    chat_id=auth.chat_id,
                    text=decision.response_text or "Command or input is unavailable.",
                    reply_to_message_id=message_id_str,
                )
            )
            return True

        if decision.outcome == RouteOutcomeKind.COMMAND_LOCAL:
            assert decision.request is not None
            response = await self._turn_handler.handle_turn(decision.request)
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.TELEGRAM,
                    chat_id=auth.chat_id,
                    text=response.text,
                    parse_mode=response.parse_mode,
                    reply_to_message_id=message_id_str,
                    correlation_id=response.turn_id,
                )
            )
            return True

        # Non-blocking background turn dispatch keeps /cancel responsive during long turns.
        assert decision.request is not None
        self._spawn_turn_task(decision.request)
        return True

    def _spawn_turn_task(self, request: InboundUserRequest) -> asyncio.Task[None]:
        task = asyncio.create_task(self._execute_turn(request))
        self._background_tasks.add(task)
        if self._coordinator is not None:
            self._coordinator.register_turn_task(
                turn_id=request.request_id,
                chat_id=request.chat_id,
                channel=ChannelType.TELEGRAM,
                task=task,
            )

        def _cleanup(done_task: asyncio.Task[None]) -> None:
            self._background_tasks.discard(done_task)
            if self._coordinator is not None:
                self._coordinator.unregister_turn_task(request.request_id)

        task.add_done_callback(_cleanup)
        return task

    async def _execute_turn(self, request: InboundUserRequest) -> None:
        try:
            await self._delivery.send_typing_indicator(request.chat_id)
            response = await self._turn_handler.handle_turn(request)
            await self._delivery.send_message(
                OutboundMessage(
                    channel=ChannelType.TELEGRAM,
                    chat_id=request.chat_id,
                    text=response.text,
                    parse_mode=response.parse_mode,
                    reply_to_message_id=request.message_id,
                    correlation_id=response.turn_id,
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error(self._redact(f"Telegram turn execution error: {exc}"))
            try:
                await self._delivery.send_message(
                    OutboundMessage(
                        channel=ChannelType.TELEGRAM,
                        chat_id=request.chat_id,
                        text="Unable to complete your request right now due to an internal error.",
                        reply_to_message_id=request.message_id,
                        correlation_id=request.request_id,
                    )
                )
            except Exception as delivery_exc:  # noqa: BLE001
                logger.error(self._redact(f"Error delivering fallback notice: {delivery_exc}"))

    async def poll_once(self) -> int:
        """Execute a single getUpdates poll cycle and return processed update count."""
        next_offset = self._offset_cursor.load_next_offset()
        updates = await self._transport.get_updates(
            offset=next_offset,
            timeout=self._poll_timeout_seconds,
            allowed_updates=("message",),
        )
        processed = 0
        for update in updates:
            if self._stop_event.is_set():
                break
            if await self.process_update(update):
                processed += 1
        return processed

    async def run_polling_loop(self, *, max_polls: int | None = None) -> None:
        """Run single-instance long polling with backoff until stopped or max_polls reached."""
        if not self._settings.telegram_bot_enabled:
            raise TelegramGatewayError("Telegram polling gateway is disabled in settings.")

        self._stop_event.clear()
        self._instance_lock.acquire()
        consecutive_failures = 0
        poll_count = 0

        try:
            await self.verify_no_webhook_conflict()
            while not self._stop_event.is_set():
                if max_polls is not None and poll_count >= max_polls:
                    break
                poll_count += 1
                try:
                    await self.poll_once()
                    consecutive_failures = 0
                except TelegramWebhookConflictError:
                    raise
                except TelegramRateLimitError as exc:
                    wait_seconds = min(
                        max(exc.retry_after, 0.05),
                        self._max_backoff_seconds,
                    )
                    logger.warning(self._redact(f"Telegram rate limited; backing off {wait_seconds:.2f}s."))
                    await self._wait_interruptible(wait_seconds)
                except TelegramGatewayError as exc:
                    consecutive_failures += 1
                    base = min(
                        self._max_backoff_seconds,
                        self._base_backoff_seconds * (2 ** (consecutive_failures - 1)),
                    )
                    jitter = max(0.0, float(self._jitter_fn(base)))
                    delay = min(self._max_backoff_seconds, base + jitter)
                    logger.warning(
                        self._redact(
                            f"Transient Telegram poll error ({exc}); retrying in {delay:.2f}s."
                        )
                    )
                    await self._wait_interruptible(delay)
        finally:
            self._instance_lock.release()

    async def wait_for_background_tasks(self, timeout: float | None = 5.0) -> None:
        """Await completion of currently spawned background turn tasks."""
        if not self._background_tasks:
            return
        tasks = list(self._background_tasks)
        await asyncio.wait(tasks, timeout=timeout)

    async def stop(self, *, cancel_active_turns: bool = True, drain_timeout: float = 2.0) -> None:
        """Signal polling loop exit, drain/cancel active turns, and close resources."""
        self._stop_event.set()
        if self._background_tasks:
            tasks = list(self._background_tasks)
            if cancel_active_turns:
                for task in tasks:
                    task.cancel()
            await asyncio.wait(tasks, timeout=drain_timeout)
        self._instance_lock.release()
        await self._transport.aclose()

    async def _wait_interruptible(self, seconds: float) -> None:
        if seconds <= 0:
            return
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            return

    def _redact(self, message: str) -> str:
        token = (
            self._settings.telegram_bot_token.get_secret_value()
            if self._settings.telegram_bot_token is not None
            else None
        )
        return redact_bot_token(message, settings=self._settings, bot_token=token)
