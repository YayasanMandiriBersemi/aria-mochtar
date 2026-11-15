"""Pydantic v2 communication and Telegram payload models for CMP-02."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aira.ports.channel import (
    CancellationScope,
    CancellationSignal,
    CancelResult,
    ChannelType,
    DeliveryReceipt,
    InboundUserRequest,
    InlineButton,
    OutboundMessage,
    SecurityIngressEvent,
    SlashCommand,
    TurnResponse,
)


class TelegramUser(BaseModel):
    """Telegram user object parsed from incoming updates."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int
    is_bot: bool = False
    first_name: str = ""
    username: str | None = None


class TelegramChat(BaseModel):
    """Telegram chat object parsed from incoming updates."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int
    type: str
    title: str | None = None
    username: str | None = None


class TelegramMessage(BaseModel):
    """Telegram message payload parsed from incoming updates."""

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore")

    message_id: int
    date: int
    chat: TelegramChat
    from_user: TelegramUser | None = Field(default=None, alias="from")
    text: str | None = None
    caption: str | None = None


class TelegramUpdate(BaseModel):
    """Top-level Telegram getUpdates item."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    update_id: int
    message: TelegramMessage | None = None
    edited_message: TelegramMessage | None = None
    callback_query: dict[str, Any] | None = None
    channel_post: dict[str, Any] | None = None


class TelegramWebhookInfo(BaseModel):
    """Subset of Telegram getWebhookInfo response used for conflict checks."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    url: str = ""
    has_custom_certificate: bool = False
    pending_update_count: int = 0


__all__ = [
    "CancellationScope",
    "CancellationSignal",
    "CancelResult",
    "ChannelType",
    "DeliveryReceipt",
    "InboundUserRequest",
    "InlineButton",
    "OutboundMessage",
    "SecurityIngressEvent",
    "SlashCommand",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
    "TelegramUser",
    "TelegramWebhookInfo",
    "TurnResponse",
]
