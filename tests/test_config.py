"""Automated tests for CMP-01 Configuration & Secret Manager."""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from aira.config import (
    MIN_SECRET_LENGTH,
    REDACTED_PLACEHOLDER,
    AppConfig,
    ApplicationSettings,
    ConfigurationError,
    EnvironmentMode,
    InsecureFilePermissionWarning,
    LogLevel,
    check_env_file_permissions,
    get_settings,
    load_settings,
    reset_settings_cache,
)

_ENV_VARS_TO_CLEAR: tuple[str, ...] = (
    "AIRA_ENV",
    "AIRA_APP_NAME",
    "AIRA_TIMEZONE",
    "AIRA_LOG_LEVEL",
    "AIRA_DATA_DIR",
    "AIRA_LOG_FILE_PATH",
    "AIRA_IPC_SOCKET_PATH",
    "DATABASE_URL",
    "GEMINI_API_KEY",
    "GEMINI_FAST_MODEL",
    "GEMINI_PRO_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "TELEGRAM_BOT_ENABLED",
    "TELEGRAM_BOT_TOKEN",
    "AUTHORIZED_TELEGRAM_USER_IDS",
    "DAILY_TOKEN_BUDGET_CAP",
    "MAX_INPUT_TOKENS_PER_TURN",
    "MAX_TOOL_ITERATIONS",
    "AIRA_IPC_AUTH_TOKEN",
)


@pytest.fixture(autouse=True)
def _clean_env_and_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from host environment variables and singleton caches."""
    for var_name in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var_name, raising=False)
    reset_settings_cache()


# ---------------------------------------------------------------------------
# 1. Valid configuration & 7. Default configuration behavior
# ---------------------------------------------------------------------------


def test_default_configuration_behavior() -> None:
    """Loading without env vars succeeds in development with sensible defaults."""
    settings = load_settings(env_file=None)

    assert isinstance(settings, ApplicationSettings)
    assert AppConfig is ApplicationSettings
    assert settings.aira_env == EnvironmentMode.DEVELOPMENT
    assert settings.app_name == "AIRA MOCHTAR"
    assert settings.timezone == "Asia/Jakarta"
    assert settings.log_level == LogLevel.INFO
    assert settings.data_dir == Path("./data")
    assert settings.log_file_path == Path("./data/logs/aira.jsonl")
    assert settings.ipc_socket_path == Path("./data/aira.sock")
    assert settings.database_url == "sqlite:///./data/aira.db"
    assert settings.gemini_fast_model == "gemini-2.5-flash"
    assert settings.gemini_pro_model == "gemini-2.5-pro"
    assert settings.gemini_embedding_model == "gemini-embedding-001"
    assert settings.telegram_bot_enabled is False
    assert settings.daily_token_budget_cap == 500_000
    assert settings.max_input_tokens_per_turn == 16_000
    assert settings.max_tool_iterations == 5


def test_configuration_is_immutable() -> None:
    """ApplicationSettings instances are frozen and reject runtime mutation."""
    settings = load_settings(env_file=None)
    with pytest.raises(ValidationError):
        settings.daily_token_budget_cap = 999  # type: ignore[misc]


def test_valid_full_configuration_in_test_and_production() -> None:
    """Full valid configurations succeed in both test and production environments."""
    test_cfg = load_settings(
        env_file=None,
        AIRA_ENV="test",
        AIRA_TIMEZONE="UTC",
        DATABASE_URL="sqlite:///./data/test_aira.db",
        DAILY_TOKEN_BUDGET_CAP=100_000,
        MAX_INPUT_TOKENS_PER_TURN=8_000,
    )
    assert test_cfg.aira_env == EnvironmentMode.TEST
    assert test_cfg.timezone == "UTC"

    prod_cfg = load_settings(
        env_file=None,
        AIRA_ENV="production",
        AIRA_LOG_LEVEL="warning",
        DATABASE_URL="postgresql+asyncpg://aira:dbpass@localhost:5432/aira",
        GEMINI_API_KEY="synthetic-test-gemini-key-0001",
        TELEGRAM_BOT_ENABLED=True,
        TELEGRAM_BOT_TOKEN="synthetic-test-telegram-token-0001",
        AUTHORIZED_TELEGRAM_USER_IDS="123456789,987654321",
        AIRA_IPC_AUTH_TOKEN="synthetic-test-ipc-token-0001",
    )
    assert prod_cfg.aira_env == EnvironmentMode.PRODUCTION
    assert prod_cfg.log_level == LogLevel.WARNING
    assert prod_cfg.authorized_telegram_user_ids == (123456789, 987654321)


# ---------------------------------------------------------------------------
# 2. Missing optional variables
# ---------------------------------------------------------------------------


def test_missing_optional_variables_in_development() -> None:
    """Optional credentials default cleanly to None / empty tuple in development."""
    settings = load_settings(
        env_file=None,
        GEMINI_API_KEY="",
        TELEGRAM_BOT_TOKEN="   ",
        AIRA_IPC_AUTH_TOKEN=None,
        AUTHORIZED_TELEGRAM_USER_IDS="",
    )
    assert settings.gemini_api_key is None
    assert settings.telegram_bot_token is None
    assert settings.ipc_auth_token is None
    assert settings.authorized_telegram_user_ids == ()


# ---------------------------------------------------------------------------
# 3. Invalid configuration types and validation constraints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"AIRA_ENV": "staging"},
        {"AIRA_LOG_LEVEL": "VERBOSE"},
        {"AIRA_TIMEZONE": "Mars/Olympus_Mons"},
        {"AIRA_TIMEZONE": "   "},
        {"DATABASE_URL": "mysql://user:pass@localhost/db"},
        {"DATABASE_URL": "sqlite://"},
        {"DAILY_TOKEN_BUDGET_CAP": "not-an-int"},
        {"DAILY_TOKEN_BUDGET_CAP": 0},
        {"MAX_INPUT_TOKENS_PER_TURN": -100},
        {"DAILY_TOKEN_BUDGET_CAP": 1000, "MAX_INPUT_TOKENS_PER_TURN": 2000},
        {"MAX_TOOL_ITERATIONS": 0},
        {"MAX_TOOL_ITERATIONS": 99},
        {"AUTHORIZED_TELEGRAM_USER_IDS": "abc,123"},
        {"AUTHORIZED_TELEGRAM_USER_IDS": "-55"},
        {"AUTHORIZED_TELEGRAM_USER_IDS": "[true, 123]"},
        {"AUTHORIZED_TELEGRAM_USER_IDS": "[12.5]"},
        {"AUTHORIZED_TELEGRAM_USER_IDS": "[123, "},
    ],
)
def test_invalid_configuration_values_raise_configuration_error(
    overrides: dict[str, object],
) -> None:
    """Invalid field types or constraint violations raise sanitized ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None, **overrides)
    assert "Configuration validation failed" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Environment variable and .env file loading
# ---------------------------------------------------------------------------


def test_environment_variable_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Variables set in OS environment populate typed settings fields."""
    monkeypatch.setenv("AIRA_ENV", "TEST")
    monkeypatch.setenv("AIRA_TIMEZONE", "Asia/Makassar")
    monkeypatch.setenv("AIRA_LOG_LEVEL", "debug")
    monkeypatch.setenv("AUTHORIZED_TELEGRAM_USER_IDS", "1001, 2002, 1001")
    monkeypatch.setenv("DAILY_TOKEN_BUDGET_CAP", "250000")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-env-gemini-key-9876")

    settings = load_settings(env_file=None)
    assert settings.aira_env == EnvironmentMode.TEST
    assert settings.timezone == "Asia/Makassar"
    assert settings.log_level == LogLevel.DEBUG
    assert settings.authorized_telegram_user_ids == (1001, 2002)
    assert settings.daily_token_budget_cap == 250_000
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "synthetic-env-gemini-key-9876"


def test_dotenv_file_loading_and_json_user_ids(tmp_path: Path) -> None:
    """Settings load cleanly from a .env file with 0600 permissions."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AIRA_ENV=development",
                "AIRA_TIMEZONE=Asia/Jakarta",
                'AUTHORIZED_TELEGRAM_USER_IDS="[555111, 666222]"',
                "GEMINI_API_KEY=synthetic-dotenv-gemini-key-1234",
                "MAX_TOOL_ITERATIONS=7",
            ]
        ),
        encoding="utf-8",
    )
    os.chmod(env_file, 0o600)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        settings = load_settings(env_file=env_file)

    assert not [w for w in caught if issubclass(w.category, InsecureFilePermissionWarning)]
    assert settings.authorized_telegram_user_ids == (555111, 666222)
    assert settings.max_tool_iterations == 7
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "synthetic-dotenv-gemini-key-1234"


def test_singleton_cache_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings caches the instance until reset_settings_cache is called."""
    monkeypatch.setenv("AIRA_APP_NAME", "AIRA-FIRST")
    first = get_settings()
    assert first.app_name == "AIRA-FIRST"

    monkeypatch.setenv("AIRA_APP_NAME", "AIRA-SECOND")
    assert get_settings() is first

    reset_settings_cache()
    second = get_settings()
    assert second is not first
    assert second.app_name == "AIRA-SECOND"


# ---------------------------------------------------------------------------
# 5. Secret masking, redaction, exception scrubbing & .env file permissions
# ---------------------------------------------------------------------------


def test_secret_masking_in_string_repr_and_json_dumps() -> None:
    """SecretStr credentials never appear in str, repr, or serialized JSON dumps."""
    raw_gemini = "synthetic-super-secret-gemini-value"
    raw_tg = "synthetic-super-secret-telegram-value"
    raw_ipc = "synthetic-super-secret-ipc-value"

    settings = load_settings(
        env_file=None,
        GEMINI_API_KEY=raw_gemini,
        TELEGRAM_BOT_TOKEN=raw_tg,
        AIRA_IPC_AUTH_TOKEN=raw_ipc,
        AUTHORIZED_TELEGRAM_USER_IDS="123456",
    )

    assert isinstance(settings.gemini_api_key, SecretStr)
    assert str(settings.gemini_api_key) == "**********"
    assert repr(settings.gemini_api_key) == "SecretStr('**********')"

    for serialized in (
        str(settings),
        repr(settings),
        settings.model_dump_json(),
        json.dumps(settings.model_dump_safe()),
    ):
        assert raw_gemini not in serialized
        assert raw_tg not in serialized
        assert raw_ipc not in serialized

    safe_dict = settings.model_dump_safe()
    assert safe_dict["gemini_api_key"] == "**********"
    assert safe_dict["telegram_bot_token"] == "**********"
    assert safe_dict["ipc_auth_token"] == "**********"


def test_redaction_patterns_and_text_scrubbing() -> None:
    """Redaction helper emits raw and URL-encoded patterns and scrubs logs safely."""
    raw_secret = "synth+secret/value=with?special&chars"
    settings = load_settings(env_file=None, GEMINI_API_KEY=raw_secret)

    patterns = settings.get_redaction_patterns()
    assert raw_secret in patterns
    assert "synth%2Bsecret%2Fvalue%3Dwith%3Fspecial%26chars" in patterns

    dirty_log = (
        f"HTTP 500 calling https://api.example.invalid/?key={raw_secret} "
        "or encoded=synth%2Bsecret%2Fvalue%3Dwith%3Fspecial%26chars"
    )
    clean_log = settings.redact_text(dirty_log)
    assert raw_secret not in clean_log
    assert "synth%2Bsecret" not in clean_log
    assert clean_log.count(REDACTED_PLACEHOLDER) == 2


def test_short_secret_rejected_and_scrubbed_from_exception() -> None:
    """Secrets shorter than MIN_SECRET_LENGTH fail without leaking raw text in errors."""
    short_secret = "tiny-sec1"
    assert len(short_secret) < MIN_SECRET_LENGTH

    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None, GEMINI_API_KEY=short_secret)

    err = exc_info.value
    assert short_secret not in str(err)
    assert short_secret not in repr(err)
    assert short_secret not in json.dumps(err.errors, default=str)


def test_cross_field_error_never_leaks_valid_secrets_present_in_model() -> None:
    """Model validator failures scrub valid secrets present alongside invalid fields."""
    secret_val = "synthetic-very-sensitive-gemini-secret-xyz"
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(
            env_file=None,
            AIRA_ENV="production",
            GEMINI_API_KEY=secret_val,
            # Missing TELEGRAM_BOT_TOKEN -> triggers model_validator failure
        )

    err = exc_info.value
    assert secret_val not in str(err)
    assert secret_val not in repr(err)
    assert secret_val not in json.dumps(err.errors, default=str)


def test_insecure_env_file_permissions_emit_warning(tmp_path: Path) -> None:
    """World/group readable .env files trigger InsecureFilePermissionWarning."""
    if os.name != "posix":
        pytest.skip("POSIX file permission check only applies on POSIX OS")

    env_file = tmp_path / ".env"
    env_file.write_text("AIRA_ENV=development\n", encoding="utf-8")
    os.chmod(env_file, 0o644)

    with pytest.warns(InsecureFilePermissionWarning):
        is_secure = check_env_file_permissions(env_file)
    assert is_secure is False

    os.chmod(env_file, 0o600)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        is_secure_after = check_env_file_permissions(env_file)
    assert is_secure_after is True
    assert not caught


# ---------------------------------------------------------------------------
# 6. Production & Telegram bot-mode validation
# ---------------------------------------------------------------------------


def test_production_mode_requires_all_mandatory_credentials() -> None:
    """Production mode rejects missing GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, or owner IDs."""
    # Missing all
    with pytest.raises(ConfigurationError):
        load_settings(env_file=None, AIRA_ENV="production")

    # Missing Telegram token & user IDs
    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            AIRA_ENV="production",
            GEMINI_API_KEY="synthetic-real-looking-gemini-key-01",
        )

    # Missing authorized user IDs
    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            AIRA_ENV="production",
            GEMINI_API_KEY="synthetic-real-looking-gemini-key-01",
            TELEGRAM_BOT_TOKEN="synthetic-real-looking-tg-token-01",
        )


@pytest.mark.parametrize(
    "placeholder_value",
    [
        "your_gemini_api_key_placeholder",
        "changeme_1234567890",
        "<REPLACE_WITH_REAL_KEY>",
        "placeholder_secret_token",
    ],
)
def test_production_mode_rejects_placeholder_credentials(placeholder_value: str) -> None:
    """Production mode blocks unreplaced template placeholders even if >= 12 chars."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(
            env_file=None,
            AIRA_ENV="production",
            GEMINI_API_KEY=placeholder_value,
            TELEGRAM_BOT_TOKEN="synthetic-valid-tg-token-0001",
            AUTHORIZED_TELEGRAM_USER_IDS="123456789",
        )
    assert "GEMINI_API_KEY" in str(exc_info.value)


def test_telegram_bot_enabled_requires_token_and_owner_whitelist() -> None:
    """Enabling Telegram bot in development still requires token and owner whitelist."""
    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            AIRA_ENV="development",
            TELEGRAM_BOT_ENABLED=True,
        )

    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            AIRA_ENV="development",
            TELEGRAM_BOT_ENABLED=True,
            TELEGRAM_BOT_TOKEN="synthetic-dev-tg-token-0001",
        )

    cfg = load_settings(
        env_file=None,
        AIRA_ENV="development",
        TELEGRAM_BOT_ENABLED=True,
        TELEGRAM_BOT_TOKEN="synthetic-dev-tg-token-0001",
        AUTHORIZED_TELEGRAM_USER_IDS="987654321",
    )
    assert cfg.telegram_bot_enabled is True
    assert cfg.authorized_telegram_user_ids == (987654321,)
