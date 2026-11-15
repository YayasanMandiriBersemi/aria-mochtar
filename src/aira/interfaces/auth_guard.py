"""Telegram owner identity and private-chat enforcement guard for CMP-02."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from aira.config import ApplicationSettings
from aira.interfaces.models import ChannelType, SecurityIngressEvent, TelegramUpdate


class AuthCheckResult(BaseModel):
    """Outcome of evaluating an incoming Telegram update against owner policy."""

    model_config = ConfigDict(frozen=True)

    authorized: bool
    sender_id: str | None = None
    chat_id: str | None = None
    audit_event: SecurityIngressEvent | None = None


class OwnerAuthGuard:
    """Enforces single-owner, private-chat-only Telegram access controls."""

    def __init__(self, authorized_user_ids: Iterable[int]) -> None:
        self._authorized_user_ids: frozenset[int] = frozenset(authorized_user_ids)

    @classmethod
    def from_settings(cls, settings: ApplicationSettings) -> OwnerAuthGuard:
        """Build an OwnerAuthGuard from validated CMP-01 ApplicationSettings."""
        return cls(settings.authorized_telegram_user_ids)

    @property
    def authorized_user_ids(self) -> frozenset[int]:
        """Return immutable set of whitelisted Telegram owner user IDs."""
        return self._authorized_user_ids

    def verify_telegram_update(self, update: TelegramUpdate) -> AuthCheckResult:
        """Validate sender presence, non-bot origin, private chat, and owner ID."""
        if update.message is None:
            return AuthCheckResult(
                authorized=False,
                audit_event=SecurityIngressEvent(
                    event_type="TELEGRAM_UNSUPPORTED_UPDATE",
                    channel=ChannelType.TELEGRAM,
                    reason="Rejected Telegram update without a direct message payload.",
                    update_id=update.update_id,
                ),
            )

        msg = update.message
        sender = msg.from_user
        chat = msg.chat
        chat_id_str = str(chat.id)
        sender_id_str = str(sender.id) if sender is not None else None

        if sender is None:
            return AuthCheckResult(
                authorized=False,
                chat_id=chat_id_str,
                audit_event=SecurityIngressEvent(
                    event_type="TELEGRAM_MISSING_SENDER",
                    channel=ChannelType.TELEGRAM,
                    chat_id=chat_id_str,
                    chat_type=chat.type,
                    reason="Rejected Telegram message without sender metadata.",
                    update_id=update.update_id,
                ),
            )

        if sender.is_bot:
            return AuthCheckResult(
                authorized=False,
                sender_id=sender_id_str,
                chat_id=chat_id_str,
                audit_event=SecurityIngressEvent(
                    event_type="TELEGRAM_BOT_SENDER_REJECTED",
                    channel=ChannelType.TELEGRAM,
                    sender_id=sender_id_str,
                    chat_id=chat_id_str,
                    chat_type=chat.type,
                    reason="Rejected message sent by another Telegram bot.",
                    update_id=update.update_id,
                ),
            )

        if chat.type != "private" or chat.id != sender.id:
            return AuthCheckResult(
                authorized=False,
                sender_id=sender_id_str,
                chat_id=chat_id_str,
                audit_event=SecurityIngressEvent(
                    event_type="TELEGRAM_NON_PRIVATE_CHAT",
                    channel=ChannelType.TELEGRAM,
                    sender_id=sender_id_str,
                    chat_id=chat_id_str,
                    chat_type=chat.type,
                    reason="Rejected Telegram message outside an owner private chat.",
                    update_id=update.update_id,
                ),
            )

        if sender.id not in self._authorized_user_ids:
            return AuthCheckResult(
                authorized=False,
                sender_id=sender_id_str,
                chat_id=chat_id_str,
                audit_event=SecurityIngressEvent(
                    event_type="SECURITY_UNAUTHORIZED_SENDER",
                    channel=ChannelType.TELEGRAM,
                    sender_id=sender_id_str,
                    chat_id=chat_id_str,
                    chat_type=chat.type,
                    reason="Rejected Telegram message from non-whitelisted sender ID.",
                    update_id=update.update_id,
                ),
            )

        return AuthCheckResult(
            authorized=True,
            sender_id=sender_id_str,
            chat_id=chat_id_str,
            audit_event=None,
        )
