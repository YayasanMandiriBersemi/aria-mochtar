"""Custom exceptions and warnings for AIRA MOCHTAR configuration management."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

SENSITIVE_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "gemini_api_key",
        "telegram_bot_token",
        "ipc_auth_token",
    }
)

_SENSITIVE_SUBSTRINGS: tuple[str, ...] = ("key", "token", "secret", "password", "credential")
REDACTED_PLACEHOLDER = "[REDACTED_SECRET]"


def is_sensitive_field_name(field_name: str) -> bool:
    """Return True if a field name or alias represents sensitive credential material."""
    normalized = field_name.strip().lower()
    if normalized in SENSITIVE_FIELD_NAMES:
        return True
    return any(marker in normalized for marker in _SENSITIVE_SUBSTRINGS)


def _sanitize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask sensitive keys within a dictionary."""
    sanitized: dict[str, Any] = {}
    for key, value in mapping.items():
        if is_sensitive_field_name(str(key)):
            sanitized[key] = REDACTED_PLACEHOLDER if value is not None else None
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_mapping(value)
        else:
            sanitized[key] = value
    return sanitized


def _sanitize_error_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a validation error dict with all credential inputs scrubbed."""
    loc = tuple(entry.get("loc", ()))
    loc_sensitive = any(is_sensitive_field_name(str(part)) for part in loc)

    cleaned: dict[str, Any] = {
        "type": str(entry.get("type", "value_error")),
        "loc": loc,
        "msg": str(entry.get("msg", "Invalid configuration value")),
    }

    if "input" in entry:
        raw_input = entry["input"]
        if loc_sensitive:
            cleaned["input"] = REDACTED_PLACEHOLDER
        elif isinstance(raw_input, dict):
            cleaned["input"] = _sanitize_mapping(raw_input)
        elif not loc:
            cleaned["input"] = REDACTED_PLACEHOLDER
        else:
            cleaned["input"] = raw_input

    if "ctx" in entry and isinstance(entry["ctx"], dict):
        cleaned["ctx"] = _sanitize_mapping(entry["ctx"])

    return cleaned


class ConfigurationError(Exception):
    """Raised when runtime configuration is missing, invalid, or unsafe.

    Error payloads and string representations strictly scrub sensitive credential
    values to guarantee secrets never leak into logs or stack traces.
    """

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.errors: list[dict[str, Any]] = [
            _sanitize_error_entry(err) for err in (errors or [])
        ]
        self.message = message
        super().__init__(message)

    @classmethod
    def from_validation_error(cls, exc: ValidationError) -> ConfigurationError:
        """Build a scrubbed ConfigurationError from a Pydantic ValidationError."""
        raw_errors = exc.errors(include_url=False, include_input=False)
        sanitized_errors = [_sanitize_error_entry(dict(err)) for err in raw_errors]

        details: list[str] = []
        for err in sanitized_errors:
            loc_str = ".".join(str(part) for part in err["loc"]) if err["loc"] else "model"
            details.append(f"{loc_str}: {err['msg']}")

        summary = "; ".join(details) if details else "Invalid application configuration."
        return cls(
            message=f"Configuration validation failed: {summary}",
            errors=sanitized_errors,
        )


class InsecureFilePermissionWarning(UserWarning):
    """Emitted when a local .env file has overly permissive POSIX permissions."""
