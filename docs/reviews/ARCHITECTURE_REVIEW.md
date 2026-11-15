# AIRA MOCHTAR — Independent Architecture Quality Review & Audit Report

| Review Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-REV-ARCH-001` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Reviewer Role** | Independent Principal Software Architect & Critical Architecture Reviewer |
| **Review Date** | 2026-11-15 |
| **Documents Audited** | `PRODUCT_VISION.md`, `PRODUCT_REQUIREMENTS.md`, `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md`, `TECH_STACK_DECISIONS.md`, `ARCHITECTURE_DECISIONS.md`, `DEVELOPMENT_ROADMAP.md`, `MEMORY_PRIVACY_POLICY.md`, `PERMISSION_MATRIX.md`, `SECURITY_BASELINE.md` |
| **Current Codebase State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Overall Verdict** | **CONDITIONAL APPROVAL (Blocked from Stage 1 Implementation until 5 `P1` Architectural Issues are Resolved)** |

---

## A. Executive Assessment

### 1. Summary of Findings

The foundational product and architectural specifications for **AIRA MOCHTAR** (`PRODUCT_VISION.md`, `PRODUCT_REQUIREMENTS.md`, `SYSTEM_ARCHITECTURE.md`, and `COMPONENT_OVERVIEW.md`) establish a well-structured **Local-First Modular Monolith** governed by a **4-Tier Permission Engine** and **Hexagonal (Ports & Adapters)** boundaries. The documents succeed in separating **Stage 1 MVP (`P0`)** scope from **Future Stages (`P1`–`P3`)**, correctly isolating **Antigravity IDE development-time models** from **production Gemini API runtime calls**, and prohibiting unsupervised live financial execution.

However, a rigorous, line-by-line cross-document audit reveals **zero `P0` fatal flaws, five `P1` major architectural problems, seven `P2` recommended improvements, and two `P3` optional enhancements** that must be addressed before writing application code:

1. **Six Tracked Specification Files Are Completely Empty (`P1`):** Six files tracked in Git (`docs/architecture/TECH_STACK_DECISIONS.md`, `docs/decisions/ARCHITECTURE_DECISIONS.md`, `docs/roadmap/DEVELOPMENT_ROADMAP.md`, `docs/security/MEMORY_PRIVACY_POLICY.md`, `docs/security/PERMISSION_MATRIX.md`, and `docs/security/SECURITY_BASELINE.md`) are 0-byte empty files.
2. **Broken Cross-Process `/cancel` Kill-Switch Architecture (`P1`):** `CMP-03` (`Aira Core Engine`) stores active turns in an **in-memory** `ActiveTurnRegistry`. If the Telegram Bot daemon runs in one OS process and the owner runs `aira cancel --all` from a separate CLI process, the CLI process cannot cancel the running Telegram turn.
3. **Contradictory Policy Enforcement Call Graph (`P1`):** `SYSTEM_ARCHITECTURE.md` Diagram B routes tool calls as `CoreEngine -> IntegrationManager -> PermissionEngine`, whereas Diagram C and `COMPONENT_OVERVIEW.md` route them as `CoreEngine -> PermissionEngine -> IntegrationManager`.
4. **Incomplete Traceability for Stage 2 `P1` Business & Communication Requirements (`P1`):** `FR-BIZ-001` (Project/Milestone tracking), `FR-BIZ-002` (SOP/Document generation from Procedural Memory), and `FR-COMM-003` (Message Drafting staging queue) are defined as `P1` (Stage 2) in `PRODUCT_REQUIREMENTS.md`, but lack concrete repository methods and component mappings in `COMPONENT_OVERVIEW.md`.
5. **Unaddressed SQLite-to-PostgreSQL Data & Dialect Migration (`P1`):** The architecture assumes a zero-friction switch from Stage 1 SQLite (`FTS5`, `?` parameters, SQLite-specific `RAISE(ABORT)` triggers) to Stage 2 PostgreSQL (`pgvector`, `$1` parameters, PL/pgSQL triggers) without defining a dialect abstraction strategy or a data export/embedding ETL pipeline.

### 2. Document Inventory & Completeness Audit

| File Path | Status | Line Count | Audit Finding |
| :--- | :--- | :--- | :--- |
| `docs/product/PRODUCT_VISION.md` | Complete | 471 lines | Coherent strategic baseline (`DOC-PRD-VISION-001`). |
| `docs/product/PRODUCT_REQUIREMENTS.md` | Complete | 759 lines | Comprehensive requirements (`DOC-PRD-REQ-002`). |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Complete | 862 lines | Detailed architecture (`DOC-ARCH-SYS-003`); contains internal diagram contradictions. |
| `docs/architecture/COMPONENT_OVERVIEW.md` | Complete | 498 lines | Detailed 17-component spec (`DOC-ARCH-CMP-004`); missing `FR-BIZ-001/002` port methods. |
| `docs/architecture/TECH_STACK_DECISIONS.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P1`).** Tech stack trade-offs exist only in Section 10 of `SYSTEM_ARCHITECTURE.md`. |
| `docs/decisions/ARCHITECTURE_DECISIONS.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P2`).** No formal ADR log populated yet. |
| `docs/roadmap/DEVELOPMENT_ROADMAP.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P2`).** Roadmap exists only as high-level sections in Vision/Component docs. |
| `docs/security/MEMORY_PRIVACY_POLICY.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P2`).** Data retention, archival, and privacy rules are unpopulated. |
| `docs/security/PERMISSION_MATRIX.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P1`).** Per-tool permission matrix is not yet documented in its dedicated file. |
| `docs/security/SECURITY_BASELINE.md` | **EMPTY** | **0 lines (0 B)** | **Missing (`P1`).** Security baseline controls are only summarized in `SYSTEM_ARCHITECTURE.md`. |

---

## B. Architecture Scorecard

Each review dimension is scored objectively on a scale of **1 (Defective) to 5 (Production-Grade Specification)**:

| # | Review Dimension | Score (1–5) | Highest Severity Issue | Assessment Summary |
| :--- | :--- | :---: | :---: | :--- |
| **1** | **Requirements Traceability** | **3.5 / 5.0** | `P1` | 100% of `P0` (Stage 1) requirements trace cleanly to `CMP-01`–`CMP-10`, but `P1` requirements `FR-BIZ-001`, `FR-BIZ-002`, and `FR-COMM-003` lack explicit component interfaces. |
| **2** | **Architectural Consistency** | **3.5 / 5.0** | `P1` | Contradiction between Diagram B and Diagram C on who invokes `Permission Engine`; ambiguity in CLI vs. Daemon IPC for `/cancel`; 6 empty tracked files in `docs/`. |
| **3** | **Complexity & Overengineering** | **4.0 / 5.0** | `P2` | Modular Monolith choice is sound, but 12+ formal `Port` interfaces for internal non-swappable modules and a separate `CMP-10` in Stage 1 add unnecessary boilerplate. |
| **4** | **Database Decisions** | **3.5 / 5.0** | `P1` | SQLite (`WAL` + `FTS5`) is ideal for Stage 1, but SQL dialect divergence (SQLite vs. PostgreSQL) and Stage 1 $\rightarrow$ Stage 2 data migration ETL are unspecified. |
| **5** | **AI Provider Architecture** | **4.5 / 5.0** | `P2` | Excellent separation between Antigravity IDE and runtime Gemini API (`google-genai`). Minor issues: outdated `text-embedding-004` reference and missing local token estimation strategy. |
| **6** | **Memory Architecture** | **4.0 / 5.0** | `P2` | Strong 5-store hierarchy and RRF hybrid search design. Needs explicit FTS5 sync trigger definitions and session/log retention policies. |
| **7** | **Security & Permissions** | **4.0 / 5.0** | `P1` | Strong 4-Tier model and SHA-256 HITL tokens, but blanket taint escalation breaks Stage 2 note-saving workflows, and Telegram group-chat rejection is missing. |
| **8** | **Local Development Feasibility (MacBook Air M2)** | **4.5 / 5.0** | `P2` | Stage 1 is ultra-lightweight (< 100 MB RAM, fanless-safe). Stage 2 should avoid heavy Docker Desktop VMs on MacBook Air M2 in favor of native PostgreSQL or `sqlite-vec`. |
| **9** | **Future Cloud Migration** | **4.0 / 5.0** | `P2` | Hybrid Cloud Control Plane + mTLS Windows VPS Bridge for MT5 is well-reasoned; requires resolving the SQLite-to-PostgreSQL SQL dialect gap first. |
| **10** | **Stage 1 Scope Control** | **5.0 / 5.0** | `P3` | Strictly excludes multi-agent subagents, WhatsApp, Canva, Web Dashboard, and MT5 from Stage 1 MVP. |
| | **OVERALL COMPOSITE SCORE** | **4.05 / 5.0** | **`P1`** | **Solid architectural foundation requiring targeted corrections before coding.** |

---

## C. Requirements Traceability Matrix (`P0` and `P1` Audit)

Every `P0` (Stage 1 MVP) and `P1` (Stage 2 Persistent System) requirement from `docs/product/PRODUCT_REQUIREMENTS.md` is audited below against `docs/architecture/COMPONENT_OVERVIEW.md`:

| Req ID | Priority | Requirement Summary | Mapped Component(s) | Interface / Method | Traceability Status |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`FR-CORE-001`** | `P0` | Persona identity & critical reasoning | `CMP-03` Core Engine | `InboundRequestPort.handle_user_request()` | **PASS (Complete)** |
| **`FR-CORE-002`** | `P0` | Epistemic uncertainty & non-sentience | `CMP-03` Core Engine | Persona System Prompt + `GATE-MVP-01` | **PASS (Complete)** |
| **`FR-CORE-003`** | `P0` | Structured context assembly loop | `CMP-04` Context Mgr | `ContextAssemblerPort.assemble_context()` | **PASS (Complete)** |
| **`FR-PERS-001`** | `P0` | Task, commitment & schedule CRUD | `CMP-06`, `CMP-07` | `MemoryStorePort.Tasks.*`, local task tools | **PASS (Complete)** |
| **`FR-PERS-002`** | `P0` | Personal knowledge base & note ingestion | `CMP-06`, `CMP-07` | `MemoryStorePort.Notes.*` (SQLite FTS5) | **PASS (Complete)** |
| **`FR-PERS-003`** | `P1` | Hierarchical memory (Episodic/Semantic/Procedural) | `CMP-12` Semantic Mem | `SemanticMemoryPort.hybrid_search()`, `summarize_episode()` | **PARTIAL (`F-TRACE-01`: Procedural template methods missing)** |
| **`FR-PERS-004`** | `P1` | Decision support & Devil's Advocate mode | `CMP-03`, `CMP-12` | `SemanticMemoryPort.save_decision_record()` | **PASS (Complete)** |
| **`FR-COMM-001`** | `P0` | Telegram interactive command & chat | `CMP-02`, `CMP-10` | `InboundRequestPort`, `ChannelDeliveryPort` | **PASS (Complete)** |
| **`FR-COMM-002`** | `P1` | Automated Morning & Evening Briefings | `CMP-11`, `CMP-10` | `WorkflowEnginePort.schedule_job()` | **PASS (Complete)** |
| **`FR-COMM-003`** | `P1` | Context-aware message drafting & staging | `CMP-08` (Partial) | *Missing explicit staging repository & tool* | **GAP (`F-TRACE-02`: No `MessageDraftRepository` or tool in Stage 2)** |
| **`FR-COMM-004`** | `P1` | Urgency-filtered notifications & Quiet Hours | `CMP-10` Notif Service | `NotificationPort.notify_owner()` | **PASS (Complete)** |
| **`FR-BIZ-001`** | `P1` | Project, milestone & deliverable tracking | *Unmapped in `CMP-06`* | *Missing from `MemoryStorePort` (`CMP-06`)* | **GAP (`F-TRACE-01`: Project & Milestone CRUD missing from `CMP-06`)** |
| **`FR-BIZ-002`** | `P1` | Business document & SOP generation | *Unmapped in `CMP-12`* | *Missing SOP template tool/port* | **GAP (`F-TRACE-01`: SOP generator & Procedural store methods missing)** |
| **`FR-ACAD-001`** | `P1` | Verifiable scholarly search & DOI grounding | `CMP-13` Academic Mod | `AcademicServicePort.search_literature()`, `verify_citation()` | **PASS (Complete)** |
| **`FR-ACAD-002`** | `P1` | Structured literature review matrix | `CMP-13` Academic Mod | `AcademicServicePort.build_synthesis_matrix()` | **PASS (Complete)** |
| **`FR-AUTO-001`** | `P0` | Standardized tool execution bus & validation | `CMP-07` Int Manager | `ToolRegistryPort`, `ToolExecutionPort` | **PASS (Complete)** |
| **`FR-AUTO-002`** | `P1` | Scheduled & event-driven background runner | `CMP-11` Workflow Eng | `WorkflowEnginePort` | **PASS (Complete)** |
| **`FR-AUTO-004`** | `P0` | Global workflow kill-switch (`/cancel`) | `CMP-02`, `CMP-03` | `InboundRequestPort.handle_cancel()` | **PARTIAL (`C-01`: Fails across separate CLI/Daemon processes)** |
| **`NFR-001`** | `P0` | Interactive latency (<1.5s ack, <300ms ctx) | `CMP-02`, `CMP-04` | Typing indicator + local context budget | **PARTIAL (`F-AI-01`: Needs local token estimator to stay <300ms)** |
| **`NFR-002`** | `P0` | Deterministic numerical & financial math | `CMP-07`, `CMP-16` | Native Python math tools, `QuantRiskEnginePort` | **PASS (Complete)** |
| **`NFR-003`** | `P1` | Graceful degradation & fault isolation | `CMP-07`, `CMP-11` | Per-tool timeouts (`10s`/`15s`) & partial briefing fallback | **PASS (Complete)** |
| **`NFR-004`** | `P0` | Observability & structured audit logging | `CMP-09` Audit Logger | `AuditLoggerPort.log_event()` with `trace_id` | **PASS (Complete)** |
| **`NFR-005`** | `P1` | Data durability & 24h backup recovery | `CMP-11` (Partial) | `DailyDatabaseBackupJob` | **PARTIAL (`F-TRACE-03`: Backup encryption & restore script unmapped)** |
| **`NFR-006`** | `P0` | Modularity & provider agnosticism | `CMP-05`, `CMP-06` | `LLMProviderPort`, `MemoryStorePort` | **PASS (Complete)** |
| **`SYS-001`** | `P0` | Local-first runtime environment | `CMP-01` Config Mgr | `ConfigLoaderPort.load_config()` | **PASS (Complete)** |
| **`SYS-002`** | `P0` | Structured local persistence (SQLite WAL) | `CMP-06` Memory Store | SQLite `WAL` + `FTS5` + SQL migrations | **PASS (Complete)** |
| **`INT-001`** | `P0` | Multi-provider LLM & embedding gateway | `CMP-05` AI Provider | `LLMProviderPort`, `EmbeddingProviderPort` | **PASS (Complete)** |
| **`INT-002`** | `P0` | Telegram Bot API adapter | `CMP-02`, `CMP-10` | Long-polling + 4,096-char pagination | **PASS (Complete)** |
| **`INT-005`** | `P1` | Scholarly & research database APIs | `CMP-13` Academic Mod | `AcademicServicePort` | **PASS (Complete)** |
| **`SEC-001`** | `P0` | Secret isolation & credential vaulting | `CMP-01`, `CMP-09` | `SecretVaultPort`, `AuditLoggerPort.sanitize_text()` | **PASS (Complete)** |
| **`SEC-002`** | `P0` | Strict owner authentication & whitelisting | `CMP-02` Ingress | `OwnerAuthGuard` | **PARTIAL (`F-SEC-03`: Missing private-chat-only check)** |
| **`SEC-003`** | `P0` | Prompt injection & untrusted isolation | `CMP-04`, `CMP-08` | `<untrusted_external_data>` + taint flag | **PARTIAL (`F-SEC-02`: Blanket taint escalation breaks local note saving)** |
| **`SEC-004`** | `P0` | Immutable append-only audit log | `CMP-09`, `CMP-06` | `audit_logs` table + SQLite `RAISE(ABORT)` triggers | **PASS (Complete)** |
| **`PERM-001`** | `P0` | Four-Tier tool permission engine | `CMP-08` Perm Engine | `PermissionEnginePort.evaluate()` | **PASS (Complete)** |
| **`PERM-002`** | `P1` | Stateful HITL approval workflow | `CMP-08`, `CMP-02` | `PermissionEnginePort.resolve_approval()` | **PASS (Complete)** |

---

## D. Contradiction & Inconsistency Report

### `[C-01]` (`P1` Major) — In-Memory `/cancel` Registry Fails Between CLI and Telegram Daemon Processes
- **Evidence:**
  - `SYSTEM_ARCHITECTURE.md` Section 3.1 (line 245) states that the CLI *"Invokes the `IngressPort` directly in-process when running locally, or communicates via a local Unix domain socket / loopback HTTP port (`127.0.0.1`) when the background daemon is active."*
  - `COMPONENT_OVERVIEW.md` (`CMP-03`, line 79) specifies that active turns are tracked in an **in-memory** `ActiveTurnRegistry`.
- **Architectural Defect:**
  - If the user runs the Telegram bot daemon (`aira serve`) in Terminal Tab 1, and then runs `aira cancel --all` in Terminal Tab 2, invoking `InboundRequestPort` in-process in Tab 2 will only inspect Tab 2's empty memory space. It cannot cancel a runaway LLM loop or tool call inside Tab 1 unless either:
    1. All CLI commands communicate with the running daemon over a local Unix socket (`./data/aira.sock`), **or**
    2. Cancellation signals are written to a shared SQLite table (`cancellation_signals`) polled by active turns, **or**
    3. Stage 1 runs a single unified interactive process (Telegram background task + interactive CLI REPL in one `asyncio` event loop) while `/cancel` on Telegram cancels Telegram turns and `Ctrl+C` / `/cancel` in the REPL cancels CLI turns.
- **Required Resolution:** Standardize Stage 1 on a single unified process (plus SQLite-backed task state) rather than building a Unix-socket daemon IPC layer in Stage 1.

### `[C-02]` (`P1` Major) — Conflicting Call Graph Between `Aira Core Engine`, `Integration Manager`, and `Permission Engine`
- **Evidence:**
  - In `SYSTEM_ARCHITECTURE.md` Section 9 Diagram B (lines 619–622): `CoreEngine --> IntManager` and `IntManager --> PermEngine`.
  - In `SYSTEM_ARCHITECTURE.md` Section 9 Diagram C (lines 665–669) and `COMPONENT_OVERVIEW.md` (`CMP-03` line 84, `CMP-07` line 152, and Matrix rows `INT-CMP-08`/`INT-CMP-09`): `CoreEngine` calls `PermissionEngine.evaluate()` first, obtains `PolicyClearance`, and then calls `IntegrationManager.execute_tool()`.
- **Architectural Defect:**
  - If `CoreEngine` is responsible for calling `PermissionEngine` before calling `IntegrationManager`, any future caller of `IntegrationManager` (such as a Stage 3 subagent in `CMP-14` or a background workflow in `CMP-11`) could accidentally bypass `PermissionEngine` if the check is not enforced inside `IntegrationManager` itself, OR cause double-evaluation if both call it.
- **Required Resolution:** Make `IntegrationManager.execute_tool()` the **mandatory Policy Enforcement Point (PEP)** that internally calls `PermissionEngine.evaluate()` (the **Policy Decision Point / PDP**) on every invocation, OR require a cryptographically unforgeable/private `PolicyClearance` token that only `PermissionEngine` can instantiate. Align Diagram B, Diagram C, and `COMPONENT_OVERVIEW.md` to one canonical flow.

### `[C-03]` (`P2` Moderate) — Stage 1 HITL Approval UX Ambiguity on Telegram
- **Evidence:**
  - `PRODUCT_REQUIREMENTS.md` (`PERM-002`, line 685) states: *"CLI confirmation in Stage 1 MVP; Interactive Telegram state machine in Stage 2."*
  - `SYSTEM_ARCHITECTURE.md` Diagram C (line 680) and `COMPONENT_OVERVIEW.md` (`CMP-02` line 62, `CMP-10` line 205) include Telegram `callback_query` inline approval buttons in Stage 1 component descriptions.
- **Architectural Defect:**
  - If a user interacts with Aira via Telegram in Stage 1 and triggers a `Tier C` action (e.g., hard-deleting a note), waiting for a CLI prompt on the MacBook while the user is on their phone via Telegram is a broken user experience.
- **Required Resolution:** Either clarify that Stage 1 exposes only `Tier A` (`READ_ONLY`) and `Tier B` (`LOCAL_WRITE_REVERSIBLE`, including soft-archive of notes) tools on Telegram while `Tier C` hard-purge is CLI-only in Stage 1, or explicitly include basic Telegram inline `[Approve] / [Reject]` callbacks in Stage 1 (`CMP-02`/`CMP-08`).

### `[C-04]` (`P3` Minor) — Python Version Specification Drift
- **Evidence:**
  - `PRODUCT_REQUIREMENTS.md` (`SYS-001`, line 519) and `SYSTEM_ARCHITECTURE.md` Section 10.2 (line 818) specify `Python 3.11+`, while `SYSTEM_ARCHITECTURE.md` Section 10.5 (line 857) specifies `Python 3.12+`.
- **Required Resolution:** Standardize all documents on `Python 3.12+` (or `Python 3.11+` with `3.12` recommended).

---

## E. Complexity & Overengineering Analysis

### 1. Evaluation of the 17-Component Decomposition
- **Positive Finding:** The architecture properly designates `CMP-01` through `CMP-10` as **in-process logical packages** inside a single Python Modular Monolith, and strictly defers `CMP-11` through `CMP-17` to Stages 2–4. There are no premature microservices, message brokers (Kafka/RabbitMQ), or Kubernetes clusters in Stage 1.
- **Overengineering Finding `[O-01]` (`P2` — Excessive Formal `Port` Interfaces for Internal Core Logic):**
  - `COMPONENT_OVERVIEW.md` defines formal abstract `*Port` interfaces for almost every internal class: `ConfigLoaderPort`, `SecretVaultPort`, `InboundRequestPort`, `ContextAssemblerPort`, `PermissionEnginePort`, `NotificationPort`, etc.
  - **Critique:** In Hexagonal Architecture, abstract `Ports` exist to decouple the application core from **external infrastructure or swappable I/O adapters** (Databases, LLM APIs, Messaging APIs, External Tool Bridges). Creating abstract base classes (`ABC` / `Protocol`) for single-implementation internal domain modules like `ContextManager`, `ConfigLoader`, or `PermissionEngine` adds ceremony, boilerplate files, and indirection without architectural benefit.
  - **Simplification:** Restrict formal `Port` interfaces in `src/aira/ports/` to the **four true external boundaries**:
    1. `LLMProviderPort` / `EmbeddingProviderPort` (swaps Gemini $\leftrightarrow$ Mock $\leftrightarrow$ Ollama)
    2. `MemoryStorePort` (swaps SQLite in-memory/file $\leftrightarrow$ PostgreSQL)
    3. `ChannelDeliveryPort` (swaps CLI $\leftrightarrow$ Telegram $\leftrightarrow$ Mock)
    4. `ToolAdapterPort` (standard contract for executable tools)
- **Overengineering Finding `[O-02]` (`P2` — Premature Separation of `CMP-10` Notification Service in Stage 1):**
  - In Stage 1, Quiet Hours, urgency batching, and alert deduplication (`FR-COMM-004`) are not active (scheduled for Stage 2). In Stage 1, `CMP-10` only splits 4,096-character strings and calls `CMP-02`.
  - **Simplification:** Keep `src/aira/communication/notifications.py` as a lightweight formatting/pagination module in Stage 1 rather than a multi-layer service, and expand it into a stateful queuing service in Stage 2 when `FR-COMM-004` is implemented.

---

## F. Database & Migration Assessment

### 1. Stage 1 SQLite (`WAL` + `FTS5`) Evaluation
- Using SQLite 3 with `PRAGMA journal_mode = WAL;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA foreign_keys = ON;`, `PRAGMA busy_timeout = 5000;`, and `FTS5` virtual tables is **architecturally optimal** for a single-user local MVP. It provides ACID durability and sub-millisecond full-text search with zero background daemon memory overhead.

### 2. Critical Database Migration Findings

#### `[F-DB-01]` (`P1` Major) — Unaddressed SQL Dialect Divergence & Missing Stage 1 $\rightarrow$ Stage 2 Data Migration Pipeline
- **Evidence:**
  - `SYSTEM_ARCHITECTURE.md` Section 8.1 claims that switching from Stage 1 SQLite to Stage 2 PostgreSQL + `pgvector` is a simple adapter swap via `DATABASE_URL`.
  - However, `CMP-06` and `CMP-09` rely on SQLite-specific features:
    1. `CREATE VIRTUAL TABLE ... USING fts5(...)` and `BM25()` ranking syntax (PostgreSQL uses `GIN` indexes with `to_tsvector` / `ts_rank_cd`).
    2. SQLite `BEFORE UPDATE` / `BEFORE DELETE` triggers using `SELECT RAISE(ABORT, 'Audit logs are append-only')` (PostgreSQL requires a `CREATE FUNCTION ... RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION ...; END; $$`).
    3. Parameter placeholder syntax (`?` in `sqlite3`/`aiosqlite` vs. `$1` in `asyncpg`).
  - Furthermore, **no data migration tool is specified** to transfer the owner's accumulated Stage 1 SQLite data (`tasks`, `knowledge_notes`, `user_preferences`, `session_messages`, `audit_logs`) into PostgreSQL and back-populate vector embeddings when upgrading to Stage 2.
- **Required Resolution:**
  1. Explicitly keep migration scripts engine-specific (`migrations/sqlite/` for Stage 1; `migrations/postgres/` for Stage 2) behind `MemoryStorePort` (`SQLiteMemoryStoreAdapter` vs. `PostgresMemoryStoreAdapter`), rather than pretending raw SQL migrations are portable across both engines.
  2. Define a Stage 2 migration utility requirement (`aira db migrate-sqlite-to-pg`) that exports all Stage 1 SQLite tables, inserts them into PostgreSQL, and batch-generates `pgvector` embeddings for existing `knowledge_notes`.

#### `[F-DB-02]` (`P2` Moderate) — Missing FTS5 Synchronization Triggers in `CMP-06`
- **Architectural Defect:** If `knowledge_notes` and `tasks` are stored in standard relational tables alongside an FTS5 virtual table (`knowledge_notes_fts`), updating or deleting a row in `knowledge_notes` will leave stale ghost entries in `knowledge_notes_fts` unless SQLite `AFTER INSERT`, `AFTER UPDATE`, and `AFTER DELETE` triggers are explicitly defined in the initial SQL migration.

---

## G. AI Provider & Memory Architecture Findings

### 1. AI Provider Architecture (`CMP-05`)
- **Verification of IDE vs. Runtime Separation:** **PASS (5/5).** Section 5.1 of `SYSTEM_ARCHITECTURE.md` and `CMP-05` of `COMPONENT_OVERVIEW.md` clearly distinguish the Antigravity IDE environment from Aira's standalone runtime (`google-genai` SDK + `GEMINI_API_KEY`).
- **Finding `[F-AI-01]` (`P2` — Pre-Call Token Estimation Latency vs. `NFR-001` 300ms Budget):**
  - `CMP-04` (`Context Manager`) must assemble and trim context within `< 300 ms` (`NFR-001`). Calling Gemini's remote `client.models.count_tokens()` API over HTTPS adds `150–400 ms` of network round-trip latency before the actual `generate_content()` call even starts.
  - **Recommendation:** Use a fast, deterministic local token estimator in `CMP-04` (e.g., $\lceil \text{len(utf8\_bytes)} / 3.5 \rceil$ with a 15% safety buffer) for `< 1 ms` pre-call context trimming, and rely on `LLMResponse.usage_metadata` from `generate_content()` for exact post-call ledger accounting in `CMP-05`.
- **Finding `[F-AI-02]` (`P3` — Embedding Model Identifier Update):**
  - Replace hardcoded mentions of `text-embedding-004` in `SYSTEM_ARCHITECTURE.md` Section 5.3 with configurable `GEMINI_EMBEDDING_MODEL` defaulting to `gemini-embedding-001`.

### 2. Memory Architecture (`CMP-06`, `CMP-12`)
- **Finding `[F-MEM-01]` (`P2` — Missing Retention & Compaction Policy):**
  - `docs/security/MEMORY_PRIVACY_POLICY.md` is currently empty (`0 bytes`). Neither `SYSTEM_ARCHITECTURE.md` nor `COMPONENT_OVERVIEW.md` defines log rotation limits for `data/logs/aira.jsonl` (e.g., `maxBytes = 10 MB`, `backupCount = 5`) or archival policies for old raw `session_messages`.

---

## H. Security & Governance Findings

### `[F-SEC-01]` (`P1` Major) — Blanket Taint Escalation (`Tier B -> Tier C`) Breaks Legitimate Stage 2 Workflows
- **Evidence:**
  - `SYSTEM_ARCHITECTURE.md` Section 6.4 (line 445) and `CMP-08` (line 169) state: *"If the current turn context contains `<untrusted_external_data>`, the `Permission Engine` marks the turn as `tainted = True` and automatically escalates any non-read-only tool invocation (`Tier B`) to require explicit `Tier C` human confirmation."*
- **Security & Usability Defect:**
  - In Stage 2 (`UC-004` Academic Literature Review), Aira fetches paper abstracts from arXiv/PubMed (which are wrapped in `<untrusted_external_data>`) and then saves the synthesized literature review or bibliography note to the local knowledge base (`save_note`, a `Tier B` tool) or writes an episodic session summary (`Tier B`).
  - Under a blanket taint-escalation rule, **every single note save or session summary following an external search will halt and require manual `Tier C` approval**, causing severe approval fatigue (violating the UX principle *Signal Over Noise*).
- **Required Resolution:** Replace blanket taint escalation with **Sink-Aware Taint Policy** in `CMP-08`:
  - **Safe Local Sinks (Remain `Tier B` when tainted):** `save_note` and `append_turn` / `summarize_episode`, provided the saved record itself is tagged with `source_trust = "external_derived"` so its contents remain delimited if re-injected into future prompts.
  - **Privileged / Control Sinks (Escalate to `Tier C` when tainted):** Modifying `user_preferences`, modifying system schedules/workflows, deleting/overwriting existing trusted notes, or invoking any external communication/API mutation tool.

### `[F-SEC-02]` (`P2` Moderate) — Missing Telegram Private-Chat Enforcement (`chat.type == "private"`)
- **Evidence:**
  - `CMP-02` (`Ingress Adapters`, line 61) checks `message.from.id` against `AUTHORIZED_TELEGRAM_USER_IDS`.
- **Security Vulnerability:**
  - In Telegram, `message.from.id` is the sender's user ID, while `message.chat.id` and `message.chat.type` identify the conversation room. If the owner accidentally adds the bot to a shared Telegram group or supergroup and sends a command, `message.from.id` will match the owner's ID, and Aira will reply with private personal notes or financial status **inside the group chat** visible to all group members.
- **Required Resolution:** `OwnerAuthGuard` in `CMP-02` must enforce:
  `message.from.id in AUTHORIZED_TELEGRAM_USER_IDS and message.chat.type == "private" and message.chat.id == message.from.id`.

### `[F-SEC-03]` (`P2` Moderate) — Secret Redactor Minimum-Length & Encoding Guard
- **Evidence:**
  - `CMP-09` registers all literal secret strings loaded by `CMP-01` for substring replacement (`[REDACTED_SECRET]`).
- **Security Defect:**
  - If a configured secret variable is accidentally set to a short string (e.g., `"test"` or `"123"` during development), literal replacement will corrupt every occurrence of `"test"` or `"123"` across all logs and user messages. Additionally, URL-encoded secrets in HTTP error traces (e.g., `httpx.HTTPStatusError` containing request URLs) could evade literal matching if special characters are percent-encoded.
- **Required Resolution:** Enforce a minimum secret length validation ($\ge 12$ characters) in `CMP-01`, redact both raw and `urllib.parse.quote()` forms of registered secrets in `CMP-09`, and configure `httpx` / SDK loggers to never log full query strings containing API keys.

### `[F-SEC-04]` (`P2` Moderate) — Canonical JSON Serialization for `PERM-002` SHA-256 Approval Hashes
- **Required Resolution:** Explicitly mandate RFC 8785 / deterministic JSON serialization (`json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`) in `CMP-08` so dictionary key ordering differences between Python dicts and SQLite JSON storage never cause false-positive `PayloadTamperedError` rejections.

---

## I. Local Development Feasibility (MacBook Air M2 Evaluation)

The target local development machine is a **MacBook Air M2** (ARM64 `arm64` Apple Silicon, passive fanless cooling, unified memory architecture).

| Stage & Workload | Estimated RAM Usage | CPU / Thermal Impact on MacBook Air M2 | Feasibility Verdict |
| :--- | :---: | :--- | :--- |
| **Stage 1 MVP (`CMP-01`–`CMP-10`):** Python 3.12 + SQLite `WAL`/`FTS5` + Telegram Long-Polling + Cloud Gemini API | **~55 – 90 MB RAM** | Negligible (`< 1%` idle CPU, zero thermal throttling, minimal battery drain). | **EXCELLENT (5/5)** |
| **Stage 2 (Option A — Docker Desktop + PostgreSQL + Local Ollama):** | **4.5 – 8.0 GB RAM** | **High Risk:** Docker Linux VM (`~2 GB` idle) + local LLM inference causes thermal throttling on fanless M2 Air and memory pressure on 8 GB / 16 GB models. | **POOR ON 8GB/16GB M2 AIR** |
| **Stage 2 (Option B — Recommended for M2 Air):** Native Homebrew PostgreSQL 16 (or SQLite + `sqlite-vec`) + Gemini Embedding API (`gemini-embedding-001`) | **~120 – 180 MB RAM** | Low CPU/thermal impact; vector embeddings computed via Gemini API (`Tier-Embed`) with local vector storage. | **EXCELLENT (5/5)** |

**Key Architectural Recommendation for MacBook Air M2 (`[F-MAC-01]`, `P2`):**
Do **not** require Docker Desktop or local Ollama inference on the MacBook Air M2 for Stage 1 or Stage 2. In Stage 1, run pure native Python + SQLite. In Stage 2, support either **`sqlite-vec`** (keeping everything in a single zero-daemon SQLite file!) or native macOS **Homebrew `postgresql@16`**, using the Gemini Embedding API for vector generation so the MacBook Air M2 remains cool, fast, and battery-efficient.

---

## J. Consolidated Recommendations, Required Document Corrections & Approval Verdict

### 1. Prioritized Issue Register

| Issue ID | Severity | Category | Summary of Required Correction | Target Document(s) |
| :--- | :---: | :--- | :--- | :--- |
| **`ISS-01`** | **`P1`** | Completeness | Populate or formally stub/deprecate the 6 empty 0-byte tracked files in `docs/` (`TECH_STACK_DECISIONS.md`, `PERMISSION_MATRIX.md`, `SECURITY_BASELINE.md`, `MEMORY_PRIVACY_POLICY.md`, `ARCHITECTURE_DECISIONS.md`, `DEVELOPMENT_ROADMAP.md`). | All 6 empty `docs/` files |
| **`ISS-02`** | **`P1`** | Consistency / Runtime | Resolve the cross-process `/cancel` defect (`C-01`) by specifying that Stage 1 runs as a single unified process (`asyncio` event loop running Telegram polling + CLI) and persists task/turn state in SQLite. | `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md` |
| **`ISS-03`** | **`P1`** | Consistency / Security | Resolve the `Permission Engine` call-graph contradiction (`C-02`): align Diagram B, Diagram C, and `CMP-03`/`CMP-07`/`CMP-08` so `PermissionEngine` is invoked deterministically before `IntegrationManager` executes any tool, with `IntegrationManager` verifying the unforgeable `PolicyClearance` object. | `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md` |
| **`ISS-04`** | **`P1`** | Traceability | Add missing `P1` Stage 2 port methods and component responsibilities for `FR-BIZ-001` (Project/Milestone repository), `FR-BIZ-002` (Procedural SOP templates), and `FR-COMM-003` (Message Drafting staging queue). | `COMPONENT_OVERVIEW.md` |
| **`ISS-05`** | **`P1`** | Security / Usability | Replace blanket taint escalation (`F-SEC-01`) with a **Sink-Aware Taint Policy** in `CMP-08` so saving external research notes (`save_note` tagged `external_derived`) remains `Tier B` while privileged mutations escalate to `Tier C`. | `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md` |
| **`ISS-06`** | **`P1`** | Database Migration | Acknowledge SQLite vs. PostgreSQL SQL dialect differences (`F-DB-01`), mandate separate adapter implementations behind `MemoryStorePort`, and add a Stage 2 data migration + embedding backfill utility (`aira db migrate-to-pg`) or evaluate `sqlite-vec`. | `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md` |
| **`ISS-07`** | **`P2`** | Security | Enforce `message.chat.type == "private"` alongside `message.from.id` in `CMP-02` `OwnerAuthGuard` (`F-SEC-02`) to prevent accidental data leaks in Telegram group chats. | `SYSTEM_ARCHITECTURE.md`, `COMPONENT_OVERVIEW.md` |
| **`ISS-08`** | **`P2`** | Overengineering | Consolidate internal `src/aira/ports/` to the 4 true external I/O boundaries (`LLMProviderPort`, `MemoryStorePort`, `ChannelDeliveryPort`, `ToolAdapterPort`) instead of creating abstract interfaces for internal-only classes (`O-01`). | `COMPONENT_OVERVIEW.md` |
| **`ISS-09`** | **`P2`** | Latency & Database | Specify local token estimation heuristic in `CMP-04` (`F-AI-01` for `<300ms` assembly), FTS5 sync triggers in `CMP-06` (`F-DB-02`), and canonical sorted JSON hashing in `CMP-08` (`F-SEC-04`). | `COMPONENT_OVERVIEW.md` |
| **`ISS-10`** | **`P3`** | Hygiene | Standardize Python version to `Python 3.12+` across all docs (`C-04`) and update embedding model example to `gemini-embedding-001` (`F-AI-02`). | `PRODUCT_REQUIREMENTS.md`, `SYSTEM_ARCHITECTURE.md` |

---

### 2. Final Architecture Approval Verdict

> **VERDICT: CONDITIONAL APPROVAL (`SCORE: 4.05 / 5.0`)**
>
> The **AIRA MOCHTAR** architecture is fundamentally sound in its selection of a **Local-First Modular Monolith**, **Python 3.12 + SQLite (WAL + FTS5)** for Stage 1 on the MacBook Air M2, **Hexagonal adapter isolation for the Google Gemini API**, and **4-Tier Permission governance**.
>
> However, **Stage 1 implementation must NOT begin** until the owner approves resolving the **`P1` architectural contradictions, traceability gaps, taint-policy refinement, and empty documentation files** identified in Section J.1 (`ISS-01` through `ISS-06`). Once those targeted documentation updates are applied, the architecture will be fully ready for **Stage 1 MVP implementation**.
