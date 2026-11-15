# AIRA MOCHTAR — `CMP-02`: Communication Gateway Implementation Record

| Implementation Metadata | Details |
| :--- | :--- |
| **Component ID** | `CMP-02` (`src/aira/ports/channel.py`, `src/aira/interfaces/`) |
| **Linked Requirements** | `FR-COMM-001` (Telegram & CLI Interface), `FR-AUTO-004` (Cancellation), `INT-002` (Telegram Output Limits), `SEC-001`, `SEC-002`, `PERM-001` |
| **Upstream Specifications** | `CMP-02-IMPLEMENTATION-PLAN.md`, `SYSTEM_ARCHITECTURE.md` (`ADR-007`, `ADR-008`), `COMPONENT_OVERVIEW.md` (`CMP-02`), `SECURITY_BASELINE.md` (`Control 1`, `Control 6`) |
| **Status** | Implemented & Offline Unit-Tested (Stage 1 MVP Communication Layer) |
| **Runtime Target** | Python `3.12+`, `httpx >= 0.27`, `typer >= 0.12`, `rich >= 13.7`, dev `pytest-asyncio >= 0.23` |

---

## 1. What Was Implemented

`CMP-02` (`Communication Gateway`) establishes the dual-channel ingress, egress, security enforcement, and cancellation control boundary of **AIRA MOCHTAR** without introducing a second application core or bypassing `CMP-01` (`ApplicationSettings`):

1. **Port & Handler Contracts (`src/aira/ports/channel.py`):**
   - `@runtime_checkable Protocol` interfaces for `ChannelDeliveryPort`, `InboundTurnHandler`, `CancellationHandler`, and `SecurityAuditHandler`.
   - Frozen Pydantic v2 transport-agnostic DTOs (`ChannelType`, `SlashCommand`, `CancellationScope`, `InboundUserRequest`, `CancellationSignal`, `OutboundMessage`, `DeliveryReceipt`, `TurnResponse`, `CancelResult`, `SecurityIngressEvent`).
2. **Ingress Auth Guard, Router & Paginator (`src/aira/interfaces/`):**
   - `OwnerAuthGuard`: fail-closed enforcement requiring non-bot sender, `chat.type == "private"`, `chat.id == from.id`, and `from.id in AUTHORIZED_TELEGRAM_USER_IDS`.
   - `CommandRouter`: strict slash-command allowlist (`/start`, `/help`, `/status`, `/cancel` + `/stop` and `/kill_all` aliases), `@bot_username` mention stripping, input length cap (`32_000` chars), honest `UNAVAILABLE` responses for unimplemented roadmap commands (`/tasks`, `/notes`, `/briefing`), and safe rejection of unknown commands without shell execution.
   - `ActiveTurnCoordinator`: non-blocking background `asyncio.Task` registry with immediate `/cancel` task cancellation and explicit external-API caveat (`CancelResult.external_call_warning`).
   - `MessagePaginator`: splits outbound replies to `<= 4096` characters with `[k/N]` prefixes while closing and reopening fenced Markdown code blocks (` ```lang ` / ` ``` `) across boundaries.
3. **Telegram Long Polling & Outbound Delivery (`src/aira/interfaces/telegram_adapter.py`):**
   - `HttpxTelegramTransport`: async `httpx.AsyncClient` transport enforcing `read_timeout_seconds > poll_timeout_seconds`, `allowed_updates=["message"]`, `429 Retry-After` handling (`TelegramRateLimitError`), `409` conflict reporting (`TelegramWebhookConflictError`) without deleting webhooks, and URL/message token redaction (`redact_bot_token`).
   - `DurableOffsetCursor` (`0600`, atomic temp-file + `os.replace`) and `SingleInstanceLock` (`fcntl.flock LOCK_EX | LOCK_NB`, `0600` + in-process guard).
   - `TelegramDeliveryAdapter`: paginated sending with inline keyboards, best-effort `typing` indicator, and automatic plain-text retry on HTTP `400` Markdown parsing errors.
   - `TelegramPollingGateway`: pre-flight `getWebhookInfo` check (fails closed if webhook configured), duplicate `update_id` protection, non-blocking background turn execution so `/cancel` runs immediately, exponential backoff + jitter, and graceful `stop()`.
4. **Local CLI & Authenticated Unix Socket IPC (`src/aira/interfaces/ipc_control.py`, `cli_adapter.py`):**
   - `LocalIPCServer` / `LocalIPCClient`: `AF_UNIX` control socket (`data/aira.sock`, `0600`) with safe non-socket & live-listener collision checks before cleaning stale sockets, constant-time `hmac.compare_digest` token validation, and `SECURITY_INVALID_IPC_TOKEN` audit events.
   - `CLIDeliveryAdapter`, `CLIGateway`, and `typer` CLI app (`chat`, `help`, `status`, `cancel`) with Rich output and IPC-first cancellation falling back cleanly to local cancellation when no daemon is active.

---

## 2. Files Added & Updated

| File Path | Role & Responsibility |
| :--- | :--- |
| `pyproject.toml` | Added `httpx`, `typer`, `rich` runtime dependencies, dev `pytest-asyncio`, and `asyncio_mode = "auto"`. |
| `src/aira/ports/__init__.py` | Public exports for port contracts and channel DTOs. |
| `src/aira/ports/channel.py` | `ChannelDeliveryPort`, `InboundTurnHandler`, `CancellationHandler`, `SecurityAuditHandler`, and channel DTOs. |
| `src/aira/interfaces/__init__.py` | Public API exports for `CMP-02` adapters, models, router, paginator, and IPC classes. |
| `src/aira/interfaces/models.py` | Telegram API schemas (`TelegramUser`, `TelegramChat`, `TelegramMessage`, `TelegramUpdate`, `TelegramWebhookInfo`) and port DTO re-exports. |
| `src/aira/interfaces/auth_guard.py` | `OwnerAuthGuard` and `AuthCheckResult`. |
| `src/aira/interfaces/paginator.py` | `MessagePaginator` and `TELEGRAM_MAX_MESSAGE_LENGTH`. |
| `src/aira/interfaces/router.py` | `CommandRouter`, `RouteDecision`, `RouteOutcomeKind`, and `ActiveTurnCoordinator`. |
| `src/aira/interfaces/telegram_adapter.py` | `HttpxTelegramTransport`, `DurableOffsetCursor`, `SingleInstanceLock`, `TelegramDeliveryAdapter`, `TelegramPollingGateway`, and `redact_bot_token`. |
| `src/aira/interfaces/ipc_control.py` | `LocalIPCServer`, `LocalIPCClient`, `IPCRequest`, `IPCResponse`, and `IPCControlError`. |
| `src/aira/interfaces/cli_adapter.py` | `CLIDeliveryAdapter`, `CLIGateway`, and `create_cli_app()` (`chat`, `help`, `status`, `cancel`). |
| `tests/test_communication_gateway.py` | 15 isolated offline tests using mocked HTTP transport, synthetic IDs/tokens, and short `/tmp` Unix socket paths. |
| `docs/architecture/CMP-02-IMPLEMENTATION.md` | This implementation record. |

---

## 3. Security & Resilience Controls

- **Zero Silent Leakage / Rejection Silence:** Unauthorized Telegram senders, bot senders, missing `from` payloads, and non-private or spoofed chats emit a `SecurityIngressEvent` to `SecurityAuditHandler` and receive zero outbound replies.
- **Credential Scrubbing Everywhere:** `redact_bot_token()` combines `ApplicationSettings.redact_text()` with `/bot<token>/` URL regex redaction before surfacing HTTP errors, trace messages, or typing warnings. `HttpxTelegramTransport` raises `TelegramGatewayError(...) from None` on `httpx.HTTPError` so raw request URLs cannot escape in tracebacks.
- **No Unwanted Webhook Side Effects:** Both `HttpxTelegramTransport` and `TelegramPollingGateway` never invoke `deleteWebhook`. If `getWebhookInfo` returns an active URL or Telegram returns HTTP `409`, polling halts cleanly with `TelegramWebhookConflictError`.
- **Authenticated Local IPC (`0600`):** `LocalIPCServer` binds its Unix domain socket with mode `0o600`, refuses non-socket paths, checks whether a live listener is connected before unlinking a dead stale socket, and verifies `IPC_AUTH_TOKEN` using `hmac.compare_digest`. Invalid tokens record `SECURITY_INVALID_IPC_TOKEN` without exposing either token.
- **Honest Cancellation Reporting:** Cancelling active asyncio turn tasks reports both the count of cancelled local turns and `CancelResult.external_call_warning`, stating clearly that already-dispatched external API calls cannot be undone locally.

---

## 4. Verification Commands

Run all syntax checks, automated tests, and dependency compatibility verification inside `.venv`:

```bash
# 1. Python syntax verification across src and tests
.venv/bin/python -m py_compile \
  src/aira/__init__.py \
  src/aira/config/*.py \
  src/aira/ports/*.py \
  src/aira/interfaces/*.py \
  tests/test_config.py \
  tests/test_communication_gateway.py

# 2. Full offline test suite (CMP-01 + CMP-02, sync + pytest-asyncio)
.venv/bin/pytest -v

# 3. Environment dependency compatibility check
/opt/homebrew/bin/uv pip check --python .venv/bin/python
```
