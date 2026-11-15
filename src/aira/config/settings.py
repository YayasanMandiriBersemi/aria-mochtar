"""Configuration and secret management for AIRA MOCHTAR (CMP-01)."""

from __future__ import annotations

import json
import os
import stat
import warnings
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from aira.config.exceptions import (
    REDACTED_PLACEHOLDER,
    ConfigurationError,
    InsecureFilePermissionWarning,
)

MIN_SECRET_LENGTH: int = 12
ALLOWED_DATABASE_SCHEMES: tuple[str, ...] = (
    "sqlite://",
    "sqlite+aiosqlite://",
    "postgresql://",
    "postgresql+asyncpg://",
)
_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "your_",
    "changeme",
    "replace_me",
    "placeholder",
    "example",
    "xxx",
)


class EnvironmentMode(StrEnum):
    """Supported execution environments for AIRA MOCHTAR."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Supported structured logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _is_placeholder_secret(value: str) -> bool:
    """Return True if a credential value appears to be an unreplaced template placeholder."""
    normalized = value.strip().lower()
    if normalized.startswith("<") or normalized.startswith("["):
        return True
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS)


class ApplicationSettings(BaseSettings):
    """Schema-validated runtime settings and secret enclosure for AIRA MOCHTAR."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        populate_by_name=True,
    )

    # Core runtime configuration
    aira_env: EnvironmentMode = Field(
        default=EnvironmentMode.DEVELOPMENT,
        validation_alias="AIRA_ENV",
    )
    app_name: str = Field(
        default="AIRA MOCHTAR",
        validation_alias="AIRA_APP_NAME",
        min_length=1,
    )
    timezone: str = Field(
        default="Asia/Jakarta",
        validation_alias="AIRA_TIMEZONE",
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        validation_alias="AIRA_LOG_LEVEL",
    )

    # Local filesystem paths and IPC socket
    data_dir: Path = Field(
        default=Path("./data"),
        validation_alias="AIRA_DATA_DIR",
    )
    log_file_path: Path = Field(
        default=Path("./data/logs/aira.jsonl"),
        validation_alias="AIRA_LOG_FILE_PATH",
    )
    ipc_socket_path: Path = Field(
        default=Path("./data/aira.sock"),
        validation_alias="AIRA_IPC_SOCKET_PATH",
    )

    # Persistence configuration
    database_url: str = Field(
        default="sqlite:///./data/aira.db",
        validation_alias="DATABASE_URL",
    )

    # AI reasoning provider configuration (runtime Gemini API)
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
    )
    gemini_fast_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias="GEMINI_FAST_MODEL",
        min_length=1,
    )
    gemini_pro_model: str = Field(
        default="gemini-2.5-pro",
        validation_alias="GEMINI_PRO_MODEL",
        min_length=1,
    )
    gemini_embedding_model: str = Field(
        default="gemini-embedding-001",
        validation_alias="GEMINI_EMBEDDING_MODEL",
        min_length=1,
    )

    # Telegram Bot ingress configuration
    telegram_bot_enabled: bool = Field(
        default=False,
        validation_alias="TELEGRAM_BOT_ENABLED",
    )
    telegram_bot_token: SecretStr | None = Field(
        default=None,
        validation_alias="TELEGRAM_BOT_TOKEN",
    )
    authorized_telegram_user_ids: Annotated[tuple[int, ...], NoDecode] = Field(
        default=(),
        validation_alias="AUTHORIZED_TELEGRAM_USER_IDS",
    )

    # Safety budgets and reasoning bounds
    daily_token_budget_cap: int = Field(
        default=500_000,
        validation_alias="DAILY_TOKEN_BUDGET_CAP",
        gt=0,
    )
    max_input_tokens_per_turn: int = Field(
        default=16_000,
        validation_alias="MAX_INPUT_TOKENS_PER_TURN",
        gt=0,
    )
    max_tool_iterations: int = Field(
        default=5,
        validation_alias="MAX_TOOL_ITERATIONS",
        ge=1,
        le=25,
    )

    # Local IPC authentication secret (optional until daemon mode is started)
    ipc_auth_token: SecretStr | None = Field(
        default=None,
        validation_alias="AIRA_IPC_AUTH_TOKEN",
    )

    @field_validator("aira_env", mode="before")
    @classmethod
    def _normalize_env_mode(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("timezone")
    @classmethod
    def _validate_iana_timezone(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Timezone must not be empty.")
        try:
            ZoneInfo(stripped)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Invalid IANA timezone: '{stripped}'") from exc
        return stripped

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        stripped = value.strip()
        for scheme in ALLOWED_DATABASE_SCHEMES:
            if stripped.startswith(scheme) and len(stripped) > len(scheme):
                return stripped
        allowed = ", ".join(ALLOWED_DATABASE_SCHEMES)
        raise ValueError(f"DATABASE_URL must start with one of: {allowed}")

    @field_validator("gemini_api_key", "telegram_bot_token", "ipc_auth_token", mode="before")
    @classmethod
    def _validate_optional_secret(cls, value: Any) -> SecretStr | None:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            raw = value.get_secret_value()
        elif isinstance(value, str):
            raw = value
        else:
            raise ValueError("Secret value must be provided as a string.")

        stripped = raw.strip()
        if not stripped:
            return None
        if len(stripped) < MIN_SECRET_LENGTH:
            raise ValueError(
                f"Configured secret must be at least {MIN_SECRET_LENGTH} characters long."
            )
        return SecretStr(stripped)

    @field_validator("authorized_telegram_user_ids", mode="before")
    @classmethod
    def _parse_telegram_user_ids(cls, value: Any) -> tuple[int, ...]:
        if value is None:
            return ()

        items: list[Any]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    decoded = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "AUTHORIZED_TELEGRAM_USER_IDS JSON array is malformed."
                    ) from exc
                if not isinstance(decoded, list):
                    raise ValueError("AUTHORIZED_TELEGRAM_USER_IDS JSON value must be a list.")
                items = decoded
            else:
                items = [part.strip() for part in stripped.split(",") if part.strip()]
        elif isinstance(value, bool):
            raise ValueError("AUTHORIZED_TELEGRAM_USER_IDS cannot be a boolean.")
        elif isinstance(value, int):
            items = [value]
        elif isinstance(value, (list, tuple, set)):
            items = list(value)
        else:
            raise ValueError(
                "AUTHORIZED_TELEGRAM_USER_IDS must be a comma-separated string or list of integers."
            )

        parsed_ids: list[int] = []
        for item in items:
            if isinstance(item, bool):
                raise ValueError("Telegram user ID must be a positive integer, not boolean.")
            if isinstance(item, float) and not item.is_integer():
                raise ValueError("Telegram user ID must be a whole positive integer.")
            try:
                uid = int(str(item).strip()) if isinstance(item, str) else int(item)
            except (TypeError, ValueError) as exc:
                raise ValueError("Telegram user IDs must be valid positive integers.") from exc
            if uid <= 0:
                raise ValueError("Telegram user IDs must be strictly positive integers.")
            parsed_ids.append(uid)

        # Deduplicate while preserving order
        return tuple(dict.fromkeys(parsed_ids))

    @model_validator(mode="after")
    def _validate_cross_field_policies(self) -> ApplicationSettings:
        if self.max_input_tokens_per_turn > self.daily_token_budget_cap:
            raise ValueError(
                "MAX_INPUT_TOKENS_PER_TURN cannot exceed DAILY_TOKEN_BUDGET_CAP."
            )

        if self.aira_env == EnvironmentMode.PRODUCTION:
            if self.gemini_api_key is None or _is_placeholder_secret(
                self.gemini_api_key.get_secret_value()
            ):
                raise ValueError(
                    "GEMINI_API_KEY must be configured with a real credential in production."
                )
            if self.telegram_bot_token is None or _is_placeholder_secret(
                self.telegram_bot_token.get_secret_value()
            ):
                raise ValueError(
                    "TELEGRAM_BOT_TOKEN must be configured with a real credential in production."
                )
            if not self.authorized_telegram_user_ids:
                raise ValueError(
                    "AUTHORIZED_TELEGRAM_USER_IDS must contain at least one owner ID in production."
                )

        if self.telegram_bot_enabled:
            if self.telegram_bot_token is None or _is_placeholder_secret(
                self.telegram_bot_token.get_secret_value()
            ):
                raise ValueError(
                    "TELEGRAM_BOT_TOKEN must be configured when TELEGRAM_BOT_ENABLED is true."
                )
            if not self.authorized_telegram_user_ids:
                raise ValueError(
                    "AUTHORIZED_TELEGRAM_USER_IDS must be non-empty when TELEGRAM_BOT_ENABLED is true."
                )

        return self

    def get_redaction_patterns(self) -> list[str]:
        """Return literal and URL-encoded secret patterns for AuditLogger redaction.

        Only secrets meeting MIN_SECRET_LENGTH are included to prevent false-positive
        scrubbing of common short substrings. Patterns are sorted longest-first.
        """
        candidates: set[str] = set()
        for secret in (self.gemini_api_key, self.telegram_bot_token, self.ipc_auth_token):
            if secret is None:
                continue
            raw = secret.get_secret_value()
            if len(raw) >= MIN_SECRET_LENGTH:
                candidates.add(raw)
                encoded = quote(raw, safe="")
                if encoded != raw:
                    candidates.add(encoded)

        return sorted(candidates, key=len, reverse=True)

    def redact_text(self, text: str) -> str:
        """Scrub any configured secret literal from arbitrary text."""
        sanitized = text
        for pattern in self.get_redaction_patterns():
            sanitized = sanitized.replace(pattern, REDACTED_PLACEHOLDER)
        return sanitized

    def model_dump_safe(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary with all secrets masked."""
        return self.model_dump(mode="json")


AppConfig = ApplicationSettings


def check_env_file_permissions(env_path: Path) -> bool:
    """Warn if a local .env file grants group or world access on POSIX systems.

    Returns True if the file does not exist, permissions cannot be checked cleanly,
    or permissions are owner-only (0600 or stricter); returns False if overly permissive.
    """
    if os.name != "posix" or not env_path.exists() or not env_path.is_file():
        return True

    mode = stat.S_IMODE(env_path.stat().st_mode)
    if mode & 0o077:
        warnings.warn(
            (
                f"Environment file '{env_path.name}' has overly permissive mode {oct(mode)}. "
                "Restrict permissions with 'chmod 600 .env'."
            ),
            InsecureFilePermissionWarning,
            stacklevel=2,
        )
        return False
    return True


def load_settings(
    env_file: str | Path | None = ".env",
    **overrides: Any,
) -> ApplicationSettings:
    """Load and validate ApplicationSettings, raising sanitized ConfigurationError on failure."""
    if env_file is not None:
        check_env_file_permissions(Path(env_file))

    try:
        return ApplicationSettings(_env_file=env_file, **overrides)
    except ValidationError as exc:
        raise ConfigurationError.from_validation_error(exc) from exc


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    """Return the cached singleton ApplicationSettings instance."""
    return load_settings()


def reset_settings_cache() -> None:
    """Clear the cached ApplicationSettings singleton (primarily for testing)."""
    get_settings.cache_clear()
