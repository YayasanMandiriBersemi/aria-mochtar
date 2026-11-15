"""Channel delivery and ingress port contracts for AIRA MOCHTAR (CMP-02)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ChannelType(str, Enum):
    """Supported communication channels for Stage 1 MVP."""

    TELEGRAM = "telegram"
    LOCAL_CLI = "local_cli"


class SlashCommand(str, Enum):
    """Supported canonical slash commands across channels."""

    START = "/start"
    HELP = "/help"
    STATUS = "/status"
    CANCEL = "/cancel"
    TASKS = "/tasks"
    NOTES = "/notes"
    BRIEFING = "/briefing"


class CancellationScope(str, Enum):
    """Target scope for user cancellation signals."""

    TURN = "turn"
    ALL_ACTIVE = "all_active"


class InlineButton(BaseModel):
    """Channel-agnostic inline button specification."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    callback_data: str | None = None
    url: str | None = None


class InboundUserRequest(BaseModel):
    """Validated user request normalized from an ingress channel."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: uuid4().hex)
    channel: ChannelType
    sender_id: str = Field(min_length=1)
    chat_id: str = Field(min_length=1)
    raw_text: str
    normalized_text: str
    command: SlashCommand | None = None
    command_args: str = ""
    update_id: int | None = None
    message_id: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CancellationSignal(BaseModel):
    """Signal requesting immediate cancellation of active work."""

    model_config = ConfigDict(frozen=True)

    signal_id: str = Field(default_factory=lambda: uuid4().hex)
    source_channel: ChannelType
    requested_by: str = Field(min_length=1)
    target_turn_id: str | None = None
    target_chat_id: str | None = None
    scope: CancellationScope = CancellationScope.ALL_ACTIVE
    reason: str = "User requested cancellation"
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutboundMessage(BaseModel):
    """Channel-agnostic outbound payload produced for delivery."""

    model_config = ConfigDict(frozen=True)

    channel: ChannelType
    chat_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    parse_mode: Literal["Markdown", "MarkdownV2", "HTML"] | None = None
    reply_to_message_id: str | None = None
    correlation_id: str | None = None
    inline_keyboard: tuple[tuple[InlineButton, ...], ...] = ()


class DeliveryReceipt(BaseModel):
    """Outcome metadata returned by a channel delivery adapter."""

    model_config = ConfigDict(frozen=True)

    channel: ChannelType
    chat_id: str
    delivered: bool = True
    chunk_count: int = Field(default=1, ge=0)
    message_ids: tuple[str, ...] = ()
    used_plain_text_fallback: bool = False
    error_detail: str | None = None


class TurnResponse(BaseModel):
    """Response emitted by downstream turn handling or gateway commands."""

    model_config = ConfigDict(frozen=True)

    turn_id: str
    text: str
    parse_mode: Literal["Markdown", "MarkdownV2", "HTML"] | None = None
    cancelled: bool = False
    available: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CancelResult(BaseModel):
    """Result of processing a cancellation signal."""

    model_config = ConfigDict(frozen=True)

    acknowledged: bool = True
    cancelled_count: int = Field(default=0, ge=0)
    cancelled_turn_ids: tuple[str, ...] = ()
    already_idle: bool = False
    external_call_warning: str = (
        "Local active turn execution was signalled to stop. "
        "Any already-dispatched external API requests cannot be undone locally."
    )
    detail: str = ""


class SecurityIngressEvent(BaseModel):
    """Structured security audit event emitted on ingress rejections or anomalies."""

    model_config = ConfigDict(frozen=True)

    event_type: str = Field(min_length=1)
    channel: ChannelType
    sender_id: str | None = None
    chat_id: str | None = None
    chat_type: str | None = None
    reason: str = Field(min_length=1)
    update_id: int | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@runtime_checkable
class ChannelDeliveryPort(Protocol):
    """Outbound delivery contract implemented by channel adapters."""

    @property
    def channel(self) -> ChannelType:
        """Return the channel identifier served by this adapter."""
        ...

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """Deliver an outbound message, paginating if the channel limits length."""
        ...

    async def send_typing_indicator(self, chat_id: str) -> None:
        """Best-effort typing acknowledgement; failures must not crash a turn."""
        ...


@runtime_checkable
class InboundTurnHandler(Protocol):
    """Downstream handler invoked for authorized chat messages and enabled commands."""

    async def handle_turn(self, request: InboundUserRequest) -> TurnResponse:
        """Process an authorized inbound request and return a turn response."""
        ...


@runtime_checkable
class CancellationHandler(Protocol):
    """Handler invoked when a user or local IPC requests active-turn cancellation."""

    async def handle_cancel(self, signal: CancellationSignal) -> CancelResult:
        """Cancel targeted active work and return an honest cancellation result."""
        ...


@runtime_checkable
class SecurityAuditHandler(Protocol):
    """Audit sink for rejected ingress attempts and security anomalies."""

    async def record_security_event(self, event: SecurityIngressEvent) -> None:
        """Persist or emit a security ingress event without raising on caller path."""
        ...
