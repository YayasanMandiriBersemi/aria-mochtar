# AIRA MOCHTAR — Memory Privacy & Data Retention Policy

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-SEC-POL-008` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Upstream Specifications** | `PRODUCT_VISION.md` (`DOC-PRD-VISION-001`), `PRODUCT_REQUIREMENTS.md` (`DOC-PRD-REQ-002`), `SYSTEM_ARCHITECTURE.md` (`DOC-ARCH-SYS-003`) |
| **Status** | Active Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Security Engineers, Privacy Reviewers, System Owner |

---

## 1. Privacy Principles & Governance Model

AIRA MOCHTAR operates on the foundational principle of **User Sovereignty & Privacy by Default**:

1. **Owner-Exclusive Ownership:** All personal notes, conversation logs, financial records, academic bibliographies, and decision histories belong exclusively to the human owner.
2. **Minimal Data Exposure (Least Context Necessary):** Only the specific context chunks required to answer the active turn are assembled and sent to external model providers. Raw database dumps are never sent over the wire.
3. **Zero Secret Leakage:** API credentials, broker account numbers, passwords, and private tokens are isolated from memory prompt assembly and scrubbed from all logs.
4. **Local-First Enclave:** In Stages 1 and 2, all persistent data resides strictly on the user's local hardware without mandatory cloud synchronization.

---

## 2. Data Classification Schema

All data ingested, stored, or processed by AIRA MOCHTAR is classified into one of six sensitivity tiers:

| Data Class | Description | Examples | Storage Location | Access Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Class 1: Secrets & Credentials** | Private keys, tokens, passwords | `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, MT5 bridge keys | `.env` (`0600`), OS Keychain | Injected into specific adapter constructors only. Never logged; never in prompts. |
| **Class 2: Financial Telemetry** | Account balance, equity, positions, trade deals | MT5 account balance, floating P/L, historical tickets | SQLite / PostgreSQL (encrypted volume) | Strictly private. Read-only in Stage 3. Never published externally. |
| **Class 3: Personal & Private Comms** | Journal notes, private drafts, personal goals | Daily reflections, unsent WhatsApp drafts, personal tasks | SQLite `knowledge_notes`, `tasks` | Injected into context only when domain-relevant. Purgeable by owner. |
| **Class 4: Business & Project Data** | Project milestones, SOPs, marketing calendars | Deliverable checklists, meeting minutes, Canva design drafts | SQLite / PostgreSQL | Accessible to Business subagents in Stage 3. Staged for HITL review before publishing. |
| **Class 5: Academic & Public Literature** | Published papers, citations, bibliographic metadata | arXiv abstracts, PubMed PMIDs, open-access PDFs | Local storage, SQLite FTS5 | Public domain. Delimited as `<untrusted_external_data>` when ingested. |
| **Class 6: System Audit & Telemetry** | Immutable action logs, latency, token usage | Correlation `trace_id`, tool names, permission outcomes | `audit_logs` table, `aira.jsonl` | Append-only. Automated secret redaction enforced. |

---

## 3. Storage Boundaries & Encryption

### 3.1 Local Storage Security (MacBook Air M2)
- **Filesystem Permissions:** The application root directory enforces user-only access (`chmod 700 ./data`). All `.env` and SQLite database files (`data/aira.db`, `data/aira.db-wal`) enforce read/write restricted to the owner (`chmod 600`).
- **Disk Encryption:** The system relies on macOS FileVault (XTS-AES 128/256-bit full disk encryption) for physical data-at-rest protection.

### 3.2 In-Transit Security
- **External API Traffic:** All egress connections to the Google Gemini API, Telegram Bot API, and scholarly REST APIs use **TLS 1.2+ / TLS 1.3** with strict certificate validation.
- **Local IPC Socket:** The Unix Domain Socket (`data/aira.sock`) enforces `0600` permissions, preventing other local macOS user accounts from issuing `/cancel` or inspection commands.

---

## 4. Retention, Rotation & Compaction Policies

| Data Category | Retention Limit | Compaction / Archival Strategy | Automated Purge Action |
| :--- | :--- | :--- | :--- |
| **Active Session History (`session_messages`)** | Last 30 days active turns | In Stage 2, turns older than 30 days are automatically summarized into episodic memory digests and raw messages are archived into compressed cold storage. | Archived after 90 days; deleted upon owner command. |
| **Structured Tasks & Notes** | Indefinite until deleted | Soft-delete (`is_archived = true`) by default. Active indexes exclude archived notes unless explicitly queried. | Hard purge upon explicit owner request (`Tier C` HITL). |
| **Application Log Files (`data/logs/aira.jsonl`)** | Max 50 MB total | Size-based log rotation: `maxBytes = 10 MB`, `backupCount = 5` rotating files. | Oldest log segment is overwritten automatically when total log size reaches 50 MB. |
| **Audit Logs (`audit_logs` table)** | 365 days minimum | Append-only database table. Truncation or deletion is blocked by database triggers during normal operations. | Exported to compressed encrypted archive annually. |
| **Pending HITL Approval Records** | 24 hours TTL | Single-use approval records. | Expired records (`status = EXPIRED`) are retained for 30 days in audit logs, then pruned. |

---

## 5. Memory Deletion & The "Right to Forget"

The owner retains full sovereign authority to inspect, correct, and purge any memory record:

1. **Soft Delete (Reversible — `Tier B`):** Marking a task, note, or preference as archived (`is_archived = true`). The record is immediately excluded from `ContextManager` assembly and FTS5 search queries, but can be restored via `/restore <id>`.
2. **Hard Purge (Irreversible — `Tier C` HITL Gate):**
   - Requires explicit Human-in-the-Loop confirmation via Telegram or CLI.
   - Deleting a note permanently executes an atomic cascade:
     ```sql
     DELETE FROM knowledge_notes WHERE id = :id;
     DELETE FROM knowledge_notes_fts WHERE rowid = :id;
     -- Stage 2: DELETE FROM semantic_embeddings WHERE note_id = :id;
     ```
   - Emits a sanitized `MEMORY_PURGE` event to `audit_logs` recording the deletion timestamp, record ID, and approving user.

---

## 6. Third-Party Data Exposure Guardrails

1. **No Outbound Training Consent:** All requests to the Google Gemini API must use paid/enterprise API tier endpoints or developer configurations that enforce Google's commitment that customer API prompt data is **not used to train foundation models**.
2. **Pre-Egress Sanitization:** The `ContextManager` and `AI Reasoning Provider` run all assembled context through the `RedactionFilter` before passing payloads to external network sockets.
3. **Zero Credential Inclusion:** Prompt templates are strictly forbidden from including API keys, passwords, or broker credentials.
