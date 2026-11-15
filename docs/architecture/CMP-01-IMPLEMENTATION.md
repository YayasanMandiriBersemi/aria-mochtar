# AIRA MOCHTAR — `CMP-01`: Configuration & Secret Manager Implementation Record

| Implementation Metadata | Details |
| :--- | :--- |
| **Component ID** | `CMP-01` (`src/aira/config`) |
| **Linked Requirements** | `SYS-001` (Local-First Runtime Environment), `SEC-001` (Secret Isolation & Credential Vaulting) |
| **Upstream Specifications** | `SYSTEM_ARCHITECTURE.md` (`Section 7.1`, `Section 7.3`), `COMPONENT_OVERVIEW.md` (`CMP-01`), `SECURITY_BASELINE.md` (`Control 2`) |
| **Status** | Implemented & Unit-Tested (Stage 1 MVP Foundation) |
| **Runtime Target** | Python `3.12+`, `pydantic >= 2.7`, `pydantic-settings >= 2.2` |

---

## 1. What Was Implemented

`CMP-01` is the foundational root component (`Zone 3: Restricted Kernel`) of **AIRA MOCHTAR**. It establishes:

1. **Canonical Python `src`-Layout & Packaging (`pyproject.toml`):**
   - Reconciled six previously empty, untracked placeholder directories (`src/core`, `src/memory`, `src/workflows`, `src/agents`, `src/integrations`, `src/notifications`) into the agreed `src/aira/` namespace layout documented in `SYSTEM_ARCHITECTURE.md` Section 7.1 (`src/aira/config`).
   - Created a local Python `3.12.13` virtual environment (`.venv`) containing only `pydantic`, `pydantic-settings`, `pytest`, and their direct minimal dependencies—with zero unrelated AI frameworks installed.
2. **Schema-Validated Runtime Configuration (`ApplicationSettings` / `AppConfig`):**
   - Typed, immutable (`frozen=True`) Pydantic `BaseSettings` model loading from OS environment variables and local `.env` files.
   - Sensible local development defaults (`AIRA_ENV=development`, `AIRA_TIMEZONE=Asia/Jakarta`, SQLite WAL path `sqlite:///./data/aira.db`, conservative token budgets and tool iteration limits).
   - Strict validation for IANA timezones (`zoneinfo.ZoneInfo`), database URL schemes (`sqlite://`, `sqlite+aiosqlite://`, `postgresql://`, `postgresql+asyncpg://`), numeric Telegram owner IDs (comma-separated strings or JSON arrays), and cross-field safety invariants (`MAX_INPUT_TOKENS_PER_TURN <= DAILY_TOKEN_BUDGET_CAP`).
3. **Production & Telegram Bot Enforcement:**
   - Allows minimal zero-secret execution in `development` and `test` modes when Telegram Bot mode is disabled (supporting offline unit tests and CLI work).
   - Enforces mandatory, non-placeholder `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `AUTHORIZED_TELEGRAM_USER_IDS` when running in `production` mode or whenever `TELEGRAM_BOT_ENABLED=true`.
4. **Secret Protection & Redaction Primitives (`SEC-001`):**
   - Wraps sensitive credentials in Pydantic `SecretStr` containers.
   - Enforces the `MIN_SECRET_LENGTH = 12` policy (`SECURITY_BASELINE.md` Control 2).
   - Scrubs sensitive values from `ConfigurationError` messages and structured validation error dictionaries.
   - Emits `InsecureFilePermissionWarning` if a local `.env` file grants group/world read or write permissions on POSIX (`mode & 0o077 != 0`).
   - Provides `get_redaction_patterns()` (raw and URL-encoded patterns sorted longest-first) and `redact_text()` for downstream consumption by `CMP-09` (`Audit Logger`).

---

## 2. Files Created

| File Path | Role & Responsibility |
| :--- | :--- |
| `pyproject.toml` | Project metadata, Python `>=3.12` constraint, minimal dependency declaration (`pydantic`, `pydantic-settings`, dev `pytest`), setuptools `src`-layout discovery, and `pytest` settings. |
| `.env.example` | Safe environment template containing placeholder variable names and security guidance (`chmod 600 .env`). Contains zero real credentials. |
| `src/aira/__init__.py` | Root namespace package initialization and `__version__`. |
| `src/aira/config/__init__.py` | Public API exports for configuration classes, exceptions, warnings, and loaders. |
| `src/aira/config/exceptions.py` | Defines `ConfigurationError` (with automatic credential scrubbing) and `InsecureFilePermissionWarning`. |
| `src/aira/config/settings.py` | Defines `EnvironmentMode`, `LogLevel`, `ApplicationSettings` (`AppConfig`), `load_settings()`, `get_settings()`, `reset_settings_cache()`, and `check_env_file_permissions()`. |
| `tests/test_config.py` | Automated pytest suite covering 35 test cases across valid configs, optional defaults, invalid types/constraints, env/`.env` loading, secret masking/scrubbing, file permission warnings, and production checks. |
| `docs/architecture/CMP-01-IMPLEMENTATION.md` | This implementation record. |

---

## 3. How Configuration Works

### Loading Sequence
1. Application code or tests invoke `load_settings(env_file=".env")` or `get_settings()`.
2. On POSIX platforms, `check_env_file_permissions(env_path)` inspects the `.env` file mode if it exists and warns if group/other bits are set.
3. `ApplicationSettings` loads values with the standard Pydantic Settings priority: explicit keyword overrides $\rightarrow$ OS environment variables $\rightarrow$ `.env` file (UTF-8) $\rightarrow$ field defaults.
4. Field validators normalize strings (`AIRA_ENV` lowercase, `AIRA_LOG_LEVEL` uppercase, blank secret strings coerced to `None`), verify IANA timezone names via `zoneinfo.ZoneInfo`, validate `DATABASE_URL` prefixes, and parse `AUTHORIZED_TELEGRAM_USER_IDS` from either CSV (`"123,456"`) or JSON (`"[123, 456]"`).
5. The model validator enforces cross-field policies (`max_input_tokens_per_turn <= daily_token_budget_cap`, production credential completeness, and Telegram bot prerequisite checks).
6. Any `ValidationError` is caught by `load_settings()` and converted via `ConfigurationError.from_validation_error()`, ensuring clean diagnostics and zero raw secret exposure.

### Key Configuration Fields

| Environment Variable | Default (Development) | Required in Production | Notes |
| :--- | :--- | :---: | :--- |
| `AIRA_ENV` | `development` | Yes | `development`, `test`, or `production` |
| `AIRA_TIMEZONE` | `Asia/Jakarta` | Yes | Validated against `zoneinfo.ZoneInfo` |
| `AIRA_LOG_LEVEL` | `INFO` | Yes | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DATABASE_URL` | `sqlite:///./data/aira.db` | Yes | Allowed schemes: `sqlite://`, `sqlite+aiosqlite://`, `postgresql://`, `postgresql+asyncpg://` |
| `GEMINI_API_KEY` | `None` | **Yes** | `SecretStr`, min 12 chars when provided, non-placeholder in prod |
| `GEMINI_FAST_MODEL` | `gemini-2.5-flash` | Yes | Default fast interactive model |
| `GEMINI_PRO_MODEL` | `gemini-2.5-pro` | Yes | Default analytical reasoning model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Yes | Stage 2+ embedding model identifier |
| `TELEGRAM_BOT_ENABLED` | `false` | Optional | Enables bot prerequisite enforcement even in dev |
| `TELEGRAM_BOT_TOKEN` | `None` | **Yes** | `SecretStr`, required in prod or when bot enabled |
| `AUTHORIZED_TELEGRAM_USER_IDS` | `()` | **Yes** | Positive integer IDs (CSV or JSON array) |
| `DAILY_TOKEN_BUDGET_CAP` | `500000` | Yes | Positive integer safety limit |
| `MAX_INPUT_TOKENS_PER_TURN` | `16000` | Yes | Positive integer, `<= DAILY_TOKEN_BUDGET_CAP` |
| `MAX_TOOL_ITERATIONS` | `5` | Yes | Bounded `[1, 25]` |
| `AIRA_IPC_AUTH_TOKEN` | `None` | Optional | Local daemon Unix socket (`data/aira.sock`) auth secret |

---

## 4. How Secrets Are Protected

- **Opaque `SecretStr` Containers:** `gemini_api_key`, `telegram_bot_token`, and `ipc_auth_token` use Pydantic's `SecretStr`. Calling `str(settings)`, `repr(settings)`, `settings.model_dump_json()`, or `settings.model_dump_safe()` outputs `'**********'` instead of plaintext.
- **Exception & Error Payload Scrubbing:** `ConfigurationError.from_validation_error()` disables Pydantic's `include_input` flag (`include_input=False`) and recursively sanitizes any sensitive error dictionary fields (`_sanitize_error_entry` / `_sanitize_mapping`). Validation errors never interpolate raw secret strings.
- **Minimum Secret Length (`>= 12` chars):** Prevents weak credentials and avoids false-positive redaction collisions inside `Audit Logger`.
- **Placeholder Detection in Production / Bot Mode:** Blocks accidental deployment using unedited `.env.example` placeholder strings (`your_...`, `changeme`, `placeholder`, `<...>`, `[...]`).
- **Log Redaction Export (`CMP-09` Integration Ready):** `settings.get_redaction_patterns()` returns both raw secret strings and their URL-encoded (`urllib.parse.quote`) forms sorted longest-first, enabling downstream `AuditLogger` redaction filters to replace leaks in URLs or tracebacks with `[REDACTED_SECRET]`.
- **`.env` File Permission Hygiene:** `.gitignore` ignores `.env` and `.env.*` (except `.env.example`). `check_env_file_permissions()` warns at load time if `.env` permissions are looser than `0600`.

---

## 5. How to Run Checks & Automated Tests

From the repository root using the local Python 3.12 virtual environment:

```bash
# 1. Python syntax verification
.venv/bin/python -m py_compile \
  src/aira/__init__.py \
  src/aira/config/__init__.py \
  src/aira/config/exceptions.py \
  src/aira/config/settings.py \
  tests/test_config.py

# 2. Run the full automated configuration & secret test suite
.venv/bin/pytest -v
```

---

## 6. Known Limitations

1. **No macOS Keychain Adapter Yet:** Stage 1 loads secrets exclusively from OS environment variables and `.env` (`0600`). Native macOS Keychain (`keyring`) integration and Cloud Secret Manager adapters remain future enhancements per `SYSTEM_ARCHITECTURE.md` Section 6.3.
2. **Static Type Checker Not Yet Installed:** Following strict Stage 1 Step 2 dependency minimization, only `pydantic`, `pydantic-settings`, and `pytest` were installed in `.venv`. `mypy`/`pyright` and `ruff` checks should be added once dev linting/type-checking tooling is approved for the repository.
3. **`.gitignore` Entry for `src/*.egg-info/`:** Editable installation (`pip install -e .`) writes `src/aira_mochtar.egg-info/`, which is not yet excluded by `.gitignore` and was left untouched per the constraint against modifying unrelated existing files.
4. **Placeholder Pattern Heuristic Scope:** Placeholder detection checks known template prefixes/substrings (`your_`, `changeme`, `placeholder`, `example`, `xxx`, `<...>`, `[...]`) and cannot verify live API key validity with Google Gemini or Telegram servers (which is out of scope for `CMP-01` offline startup validation).
