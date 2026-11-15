# AIRA MOCHTAR — Architecture Decision Records (ADR)

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-ADR-LOG-006` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Status** | Active Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Principal Architects, Software Engineers, Code Reviewers, Future Maintainers |

---

## Index of Decisions

- [ADR-001: Modular Monolith Topology for Stage 1 MVP & Stage 2](#adr-001-modular-monolith-topology-for-stage-1-mvp--stage-2)
- [ADR-002: Python 3.12+ with `asyncio` as the Unified Runtime Language](#adr-002-python-312-with-asyncio-as-the-unified-runtime-language)
- [ADR-003: SQLite 3 (`WAL` + `FTS5`) for Stage 1 with Dedicated Stage 2 PostgreSQL Migration](#adr-003-sqlite-3-wal--fts5-for-stage-1-with-dedicated-stage-2-postgresql-migration)
- [ADR-004: Direct Official Google GenAI SDK over Third-Party Agent Frameworks](#adr-004-direct-official-google-genai-sdk-over-third-party-agent-frameworks)
- [ADR-005: Four-Tier Deterministic Permission Engine with SHA-256 Payload-Bound HITL Tokens](#adr-005-four-tier-deterministic-permission-engine-with-sha-256-payload-bound-hitl-tokens)
- [ADR-006: Outbound Long-Polling for Telegram Bot Ingress in Stage 1](#adr-006-outbound-long-polling-for-telegram-bot-ingress-in-stage-1)
- [ADR-007: Consolidation to Four Principal External Ports (Preventing Internal Port Overengineering)](#adr-007-consolidation-to-four-principal-external-ports-preventing-internal-port-overengineering)
- [ADR-008: Dual-Channel In-Process and Control-Socket IPC Cancellation Model](#adr-008-dual-channel-in-process-and-control-socket-ipc-cancellation-model)

---

## ADR-001: Modular Monolith Topology for Stage 1 MVP & Stage 2

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** AIRA MOCHTAR coordinates ten logical components (Ingress, Core, Context, Memory, Policy, Tools, Audit, Notifications, AI Provider, Scheduler). The architecture must decide whether to deploy these as independent microservices (e.g., via Docker Compose) or as a unified Modular Monolith on the user's MacBook Air M2.
- **Decision:** Build AIRA MOCHTAR as a **single-process Modular Monolith** for Stage 1 and Stage 2. Enforce strict package boundaries (`src/aira/core`, `src/aira/memory`, etc.) with in-memory asynchronous calls. Prohibit cross-module database access outside public repository contracts.
- **Consequences:**
  - *Positive:* Ultra-low memory footprint (< 100 MB RAM), sub-millisecond in-process call latency, single stack-trace debugging, zero Docker daemon requirement on MacBook Air M2, atomic ACID database transactions.
  - *Negative:* All modules share a single OS process memory space. If the process crashes, all components restart together. Requires developer discipline to maintain module boundaries.

---

## ADR-002: Python 3.12+ with `asyncio` as the Unified Runtime Language

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** The system requires asynchronous I/O (handling simultaneous Telegram updates and streaming LLM responses), rigorous schema validation, scientific literature processing (Stage 2), and MetaTrader 5 quantitative analytics (Stage 3).
- **Decision:** Standardize on **Python 3.12+** using native `asyncio`, strict type hinting (`mypy` / `pyright`), and `Pydantic v2`.
- **Consequences:**
  - *Positive:* Single unified language across Core OS, Academic intelligence (`PyPDF`, `Crossref`), and Financial intelligence (MetaTrader 5 Python C-extension, `pandas`, `numpy`). Eliminates polyglot multi-service complexity. Python 3.12 provides faster startup and optimized async execution.
  - *Negative:* Slightly higher runtime memory overhead than Go/Rust (though well within MacBook Air M2 budgets). Requires strict linting to enforce type safety.

---

## ADR-003: SQLite 3 (`WAL` + `FTS5`) for Stage 1 with Dedicated Stage 2 PostgreSQL Migration

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** Stage 1 requires lightweight, durable local persistence with zero external service installation. Stage 2 requires vector embeddings (`pgvector`) for semantic search.
- **Decision:** Use **SQLite 3 with WAL mode and FTS5** for Stage 1. Encapsulate all database queries behind `MemoryStorePort`. Defer PostgreSQL + `pgvector` to Stage 2, and provide a dedicated data export and embedding backfill utility (`aira db migrate-to-pg`) rather than pretending SQL is universally portable.
- **Consequences:**
  - *Positive:* Zero background server installation on macOS. Single-file backup (`aira.db`). Sub-millisecond BM25 keyword search.
  - *Negative:* SQLite syntax differs from PostgreSQL. Requires maintaining distinct SQL migration folders (`migrations/sqlite/` vs. `migrations/postgres/`) behind the repository adapter.

---

## ADR-004: Direct Official Google GenAI SDK over Third-Party Agent Frameworks

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** Orchestrating LLM calls can be done via third-party frameworks (LangChain, CrewAI, AutoGen) or via direct integration with the official provider SDK.
- **Decision:** Implement a custom lightweight orchestrator using the **official Google GenAI SDK (`google-genai`)** wrapped behind an internal `LLMProviderPort`. Reject third-party agent wrapper frameworks.
- **Consequences:**
  - *Positive:* 100% visibility into exact prompts and token budgets. Native structured JSON schema outputs (`response_schema`). Zero unmaintained wrapper dependencies. Clean integration with deterministic SHA-256 HITL approval gates.
  - *Negative:* Requires authoring ~300 lines of clean orchestration loop and tool-calling validation logic in-house.

---

## ADR-005: Four-Tier Deterministic Permission Engine with SHA-256 Payload-Bound HITL Tokens

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** An autonomous AI system must never execute high-risk external side effects, destructive data mutations, or live financial transactions without human authorization.
- **Decision:** Classify all tools into **4 Tiers**:
  - `Tier A (READ_ONLY)`: Autonomous execution.
  - `Tier B (LOCAL_WRITE_REVERSIBLE)`: Autonomous execution + audit log (unless tainted control sink).
  - `Tier C (CONSEQUENTIAL_HITL)`: Halts execution, computes `SHA256(canonical_json(tool, args))`, stores approval record with TTL, and requires user confirmation.
  - `Tier D (PROHIBITED)`: Permanently hard-blocked.
  Enforce permissions in deterministic code before invoking any tool adapter.
- **Consequences:**
  - *Positive:* Guarantees human sovereignty. Mitigates accidental damage, prompt injection hijacking, and financial loss.
  - *Negative:* Introduces stateful pauses in asynchronous workflows while awaiting user approval.

---

## ADR-006: Outbound Long-Polling for Telegram Bot Ingress in Stage 1

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** The Telegram bot can receive messages via webhooks or outbound long-polling (`getUpdates`).
- **Decision:** Use **outbound HTTPS long-polling** for Stage 1 on the local MacBook. Defer HTTPS webhooks to Stage 4 when a cloud control plane with static domain and TLS is established.
- **Consequences:**
  - *Positive:* Operates behind NAT, dynamic home Wi-Fi, and mobile hotspots with zero open firewall ports. Requires no public domain or third-party tunnels (ngrok).
  - *Negative:* Slightly higher idle outbound polling traffic (negligible on broadband/Wi-Fi).

---

## ADR-007: Consolidation to Four Principal External Ports (Preventing Internal Port Overengineering)

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** Architecture review identified overengineering in proposing 12+ abstract `*Port` interfaces for internal classes that will never be swapped (e.g., `ConfigLoaderPort`, `ContextAssemblerPort`, `PermissionEnginePort`).
- **Decision:** Restrict formal abstract `Port` interfaces exclusively to the **Four Principal External I/O Boundaries**:
  1. `LLMProviderPort` (swappable AI provider: Gemini, Mock, Ollama)
  2. `MemoryStorePort` (swappable persistence: SQLite, Postgres, Memory)
  3. `ChannelDeliveryPort` (swappable delivery: CLI, Telegram, Mock)
  4. `ToolAdapterPort` (swappable tool execution contract)
  All other internal modules (`ContextManager`, `PermissionEngine`, `NotificationHelper`, `ProjectService`, `DocumentService`, `MessageDraftService`) are implemented as clean concrete domain services.
- **Consequences:**
  - *Positive:* Eliminates hundreds of lines of boilerplate interfaces. Makes code readable, maintainable, and pragmatic for a beginner-accessible codebase while preserving clean hexagonal testability.
  - *Negative:* None; internal refactoring remains straightforward within concrete classes.

---

## ADR-008: Dual-Channel In-Process and Control-Socket IPC Cancellation Model

- **Status:** **APPROVED**
- **Date:** 2026-11-15
- **Context:** The architecture review identified that storing active task tokens in-memory prevents a separate CLI command (`aira cancel --all`) from aborting a task running inside the Telegram daemon process.
- **Decision:** Implement a **Dual-Channel Cancellation Model**:
  1. *In-Process Channel:* Every active turn receives an `asyncio.Event` / `CancelToken` passed down to cooperative checkpoints and cancellable I/O (`asyncio.wait_for`).
  2. *Cross-Process IPC Channel:* The running application process listens on a local, authenticated Unix Domain Socket (`data/aira.sock`, permissions `0600`). When the user runs `aira cancel <task_id>` from another terminal, the CLI client connects to the socket, sends an authenticated cancellation command, and receives immediate confirmation. Additionally, cancellation signals are logged in the SQLite `cancellation_signals` table for persistent auditing.
  3. *Uninterruptible External Calls:* In-flight HTTP requests to external APIs (Gemini, tools) are wrapped in timeouts and cancelled via `asyncio.Task.cancel()`. If an external socket cannot be immediately severed, the orchestrator abandons the call and discards late responses, ensuring local state is never corrupted.
- **Consequences:**
  - *Positive:* Fast, reliable cross-process cancellation from CLI and Telegram. Guarantees the system halts runaway turns within 3 seconds without database polling lag.
  - *Negative:* Requires managing a local Unix domain socket lifecycle (cleanup on process exit).
