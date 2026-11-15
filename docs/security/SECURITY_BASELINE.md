# AIRA MOCHTAR — Security Baseline & Controls Specification

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-SEC-BASE-010` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Upstream Specifications** | `PRODUCT_VISION.md` (`DOC-PRD-VISION-001`), `PRODUCT_REQUIREMENTS.md` (`DOC-PRD-REQ-002`), `SYSTEM_ARCHITECTURE.md` (`DOC-ARCH-SYS-003`) |
| **Status** | Active Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Security Engineers, System Architects, Penetration Testers, System Owner |

---

## 1. Threat Model & Security Posture

AIRA MOCHTAR operates as a single-tenant personal executive operating system. Its primary threat model addresses four critical attack vectors:

1. **Unauthorized Access & Identity Spoofing:** External parties attempting to discover and interact with the Telegram bot or local control APIs.
2. **Credential & Secret Exfiltration:** Leaking API keys, tokens, or broker credentials through prompts, error traces, or public Git commits.
3. **Indirect Prompt Injection:** Malicious instructions embedded in external web pages, emails, or academic papers attempting to hijack tool execution.
4. **Accidental Financial or Operational Harm:** Autonomous actions executing destructive data operations or unauthorized live trading.

---

## 2. Mandatory Security Controls Baseline

### Control 1: Strict Owner Authentication & Private-Chat Verification (`SEC-002`)
- **Telegram Perimeter Guard:** Every inbound Telegram update must pass the `OwnerAuthGuard` middleware before any parsing or dispatch occurs:
  $$\text{ALLOW} \iff (\text{update.from.id} \in \text{AUTHORIZED\_TELEGRAM\_USER\_IDS}) \land (\text{update.chat.type} == \text{"private"}) \land (\text{update.chat.id} == \text{update.from.id})$$
- **Rejection Policy:** Messages from non-whitelisted users or messages sent in group chats are dropped silently (returning zero diagnostic metadata to the sender) and immediately logged as a `SECURITY_UNAUTHORIZED_INGRESS` event.

### Control 2: Zero-Leakage Secret Vaulting & Automated Redaction (`SEC-001`)
- **Storage:** Secrets are stored exclusively in `.env` (file permissions `0600`) or macOS Keychain.
- **Pydantic `SecretStr` Enclosure:** Secrets are loaded into typed `SecretStr` objects; standard `str()`, `repr()`, or JSON dumps output `**********`.
- **Minimum Secret Length Validation:** All configured secrets must be $\ge 12$ characters to prevent accidental redaction of common short strings.
- **Pre-Output Redaction Filter:** All log lines, terminal outputs, error traces, and prompt payloads pass through `AuditLoggerPort.sanitize_text()`, replacing registered secret literals and common token regex patterns with `[REDACTED_SECRET]`.

### Control 3: Indirect Prompt Injection Defense & Data Taint Tracking (`SEC-003`, `ISS-05`)
- **XML Delimitation:** All external untrusted data (arXiv abstracts, inbound messages, scraped web pages) is sanitized of closing delimiter sequences and wrapped inside:
  ```xml
  <untrusted_external_data source="..." trust_level="untrusted">
  ...raw text...
  </untrusted_external_data>
  ```
- **System Prompt Hardening:** The system prompt instructs the model that text inside `<untrusted_external_data>` is passive reference data that must never be interpreted as commands or instructions.
- **Sink-Aware Taint Enforcement:** If untrusted data is present in the turn context, privileged control sinks (`set_user_preference`, cron scheduling, note overwriting) are escalated to **Tier C (Mandatory HITL Approval)**. Safe internal note-saving remains **Tier B** tagged as `source_trust = "external_derived"`.

### Control 4: Immutable Append-Only Audit Trail (`SEC-004`)
- **Forensic Table Constraints:** The `audit_logs` table records every turn, tool invocation, permission check, token count, and latency with a unique `trace_id`.
- **Database Engine Tamper Protection:** SQLite enforces database-level triggers blocking mutation and deletion:
  ```sql
  CREATE TRIGGER abort_audit_update BEFORE UPDATE ON audit_logs
  BEGIN SELECT RAISE(ABORT, 'Audit log records are immutable'); END;

  CREATE TRIGGER abort_audit_delete BEFORE DELETE ON audit_logs
  BEGIN SELECT RAISE(ABORT, 'Audit log records cannot be deleted'); END;
  ```

### Control 5: Hard Financial Isolation Gate (`PERM-004`)
- **Read-Only Telemetry Boundary:** The MetaTrader 5 bridge service in Stage 3 exposes strictly read-only endpoints (`GET /account`, `GET /positions`, `GET /history`, `GET /rates`).
- **Permanent Proscription:** Order-execution APIs (`order_send`, live trade placement) are omitted from tool manifests and permanently classified as **Tier D (PROHIBITED)**. Live trading is physically blocked at the bridge boundary.

### Control 6: Local IPC Control Socket Security (`ADR-008`, `ISS-02`)
- **Socket Permissions:** The Unix Domain Socket (`data/aira.sock`) used for CLI-to-daemon `/cancel` control enforces `0600` permissions.
- **Token Verification:** Every IPC command payload must include a shared local authentication token (`IPC_AUTH_TOKEN`) generated in memory at daemon startup.
