# AIRA MOCHTAR — Technology Stack Decisions & Evaluation

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-ARCH-TECH-005` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Upstream Specifications** | `PRODUCT_VISION.md` (`DOC-PRD-VISION-001`), `PRODUCT_REQUIREMENTS.md` (`DOC-PRD-REQ-002`), `SYSTEM_ARCHITECTURE.md` (`DOC-ARCH-SYS-003`) |
| **Status** | Approved Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Principal Architects, Software Engineers, DevOps/SREs, System Owner |

---

## 1. Executive Summary & Selection Principles

This document formalizes the technology stack selections for **AIRA MOCHTAR** across its four evolution stages. Every technology decision is evaluated against five core criteria:

1. **Local-First Feasibility on Apple Silicon (MacBook Air M2):** Must operate silently with low memory pressure, zero thermal throttling on fanless hardware, and fast local boot time.
2. **Deterministic Governance & Safety:** Must support strict type safety, schema validation, immutable audit trails, and deterministic Human-in-the-Loop (HITL) execution controls.
3. **Single-Language Cohesion:** Must eliminate polyglot codebase friction across Core OS logic, Academic literature synthesis, and future Financial (MetaTrader 5) quantitative analytics.
4. **Hexagonal Modularity (Ports & Adapters):** Core domain business logic must depend only on clean external interfaces, allowing infrastructure swaps (e.g., SQLite $\rightarrow$ PostgreSQL) without rewriting application services.
5. **No Premature Complexity:** Avoids distributed microservices, container daemon overhead, and unmaintained third-party agent frameworks during early stages.

---

## 2. Core Technology Stack Matrix

| Architectural Layer | Stage 1 (MVP Local Prototype) | Stage 2 (Persistent System) | Stage 3 (Multi-Agent OS) | Stage 4 (Cloud Platform) | Decision Driver |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Runtime & Language** | **Python 3.12+** (`asyncio`) | Python 3.12+ (`asyncio`) | Python 3.12+ (`asyncio`) | Python 3.12+ (Linux Container) | Single language across Core, Academic, and MT5 Quant. |
| **Type & Schema Validation** | **Pydantic v2** (`pydantic-settings`) | Pydantic v2 | Pydantic v2 | Pydantic v2 | Fast C-core validation, JSON Schema generation. |
| **AI Reasoning Provider** | **Official Google GenAI SDK** (`google-genai`) | Official `google-genai` + Local Ollama fallback | Official `google-genai` + Ollama | Multi-Model Gateway (Gemini, Claude, Local) | First-class structured outputs, tool calling, vendor isolation. |
| **Primary Database** | **SQLite 3** (`WAL` mode + `FTS5`) | **PostgreSQL 16** (`pgvector`) or SQLite (`sqlite-vec`) | PostgreSQL 16 (`pgvector`) | Managed PostgreSQL (`pgvector`, encrypted) | Zero background daemon in Stage 1; vector search in Stage 2+. |
| **Database Access Layer** | **SQLAlchemy 2.0 (Async)** or **aiosqlite** + raw parameterized SQL | SQLAlchemy 2.0 (Async) + `asyncpg` | SQLAlchemy 2.0 (Async) + `asyncpg` | SQLAlchemy 2.0 (Async) + Connection Pooler | Parameterized queries, schema migrations via Alembic. |
| **CLI Framework** | **Typer** + **Rich** | Typer + Rich | Typer + Rich | Typer + Rich (Admin CLI) | Clean command ergonomics, colored ANSI terminal output. |
| **Telegram Bot Client** | **httpx** / **aiogram 3.x** (Outbound Long-Polling) | aiogram 3.x (Long-Polling) | aiogram 3.x (Long-Polling) | aiogram 3.x (HTTPS Webhook) | No public IP/open ports needed on local MacBook. |
| **Local IPC & Control Socket** | **Unix Domain Socket** (`data/aira.sock`) | Unix Domain Socket | Unix Domain Socket | Cloud HTTPS API + mTLS Bridge | Cross-process `/cancel` and CLI-to-Daemon control. |
| **Testing Framework** | **pytest** + **pytest-asyncio** | pytest + pytest-asyncio | pytest + pytest-asyncio | pytest + CI/CD automated test harness | Async test support, fixture isolation, mock adapters. |

---

## 3. Detailed Technology Evaluations

### 3.1 Runtime Language: Python 3.12+ (`asyncio`)

- **Selected:** Python 3.12+ with native `asyncio` and strict typing (`mypy` / `pyright`).
- **Rejected Alternatives:**
  - *TypeScript / Node.js (LTS):* Excellent for web services, but poor for scientific literature processing (`PyPDF`, `pandas`, `numpy`) and lacks native bindings for MetaTrader 5 (which exclusively provides a Windows C-extension for Python). Choosing TypeScript in Stage 1 would force a messy polyglot rewrite or RPC microservice bridge in Stage 3.
  - *Rust / Go:* Exceptional concurrency and memory efficiency, but significantly slower development velocity for rapid AI prompt iteration, complex JSON schema manipulation, and scientific data manipulation.
- **Benefits:**
  - Standardized runtime across all six product domains (Personal, Comms, Business, Academic, Autonomous, Financial).
  - First-class async I/O handles simultaneous Telegram polling, CLI commands, and Gemini streaming responses without thread locking.
  - Python 3.12 provides measurable performance improvements (faster interpreter startup, specialized bytecode, improved traceback ergonomics).

### 3.2 AI Integration Strategy: Direct Official Google GenAI SDK (`google-genai`)

- **Selected:** Official Google GenAI SDK (`google-genai`) wrapped inside an internal `LLMProviderPort`.
- **Rejected Alternatives:**
  - *LangChain / CrewAI / AutoGen:* Rejected due to severe architectural anti-patterns: brittle abstractions, frequent breaking changes, obscured prompt payloads, bloated dependency trees, and high friction when integrating deterministic SHA-256 HITL approval gates.
  - *Raw `requests` / `urllib3`:* Rejected because maintaining raw HTTP serialization for multipart media, tool-calling schemas, and SSE streaming adds maintenance overhead without performance benefit over the official SDK.
- **Benefits:**
  - Direct access to native Gemini capabilities: structured JSON schema enforcement (`response_schema`), native `FunctionDeclaration`, thinking budgets, and token usage metadata.
  - Application code remains decoupled from the vendor SDK via the `LLMProviderPort` abstraction.

### 3.3 Database Strategy: SQLite 3 (`WAL` + `FTS5`) in Stage 1 $\rightarrow$ PostgreSQL (`pgvector`) in Stage 2

- **Stage 1 (Local MVP):** SQLite 3 with Write-Ahead Logging (`WAL`), `foreign_keys = ON`, `busy_timeout = 5000`, and `FTS5` virtual tables.
  - *Rationale:* Ships built into Python and macOS. Operates as a single local file (`data/aira.db`) with zero RAM overhead when idle. FTS5 provides fast, sub-millisecond BM25 keyword search over personal notes and tasks without needing an external vector database.
- **Stage 2+ (Persistent System):** Managed PostgreSQL 16+ with the `pgvector` extension (or local Homebrew PostgreSQL / `sqlite-vec`).
  - *Rationale:* Vector embeddings require cosine similarity indexing (`HNSW` / `IVFFlat`) which vanilla SQLite does not support. PostgreSQL enables ACID-compliant concurrent multi-agent access, native JSONB querying, and enterprise-grade backup tooling.
- **Portability Guardrail:** All database access is encapsulated behind `MemoryStorePort`. Raw SQL is strictly partitioned into dialect-specific folders (`migrations/sqlite/` for Stage 1; `migrations/postgres/` for Stage 2) to prevent syntax bleed.

### 3.4 Ingress & Interface Strategy: Dual CLI and Telegram Long-Polling

- **Selected:** Local interactive CLI (Typer/Rich) + Telegram Bot API using outbound long-polling (`getUpdates`).
- **Rejected Alternatives:**
  - *Local Web App / Frontend in Stage 1:* Premature. Building a React/Next.js dashboard in Stage 1 diverts engineering effort away from core intelligence, memory, and governance logic.
  - *Telegram Webhooks on MacBook:* Requires exposing an inbound port, configuring DDNS, or running insecure third-party tunnels (e.g., ngrok).
- **Benefits:**
  - Outbound HTTPS long-polling works behind home Wi-Fi and mobile hotspots with zero open firewall ports.
  - Mobile Telegram interface gives the user instant mobile access to Aira anywhere, while the local CLI allows offline terminal execution.

---

## 4. Benchmark Targets & Performance Realism

To maintain strict engineering integrity, performance numbers in all specifications are defined as **Design Budgets & Empirical Targets**, never guaranteed without benchmarking:

| Metric | Target Budget | Deterministic Bounds / Variance Factors |
| :--- | :--- | :--- |
| **Idle Process Memory (Stage 1)** | **< 100 MB RAM** | Expected range: 55 MB – 90 MB on macOS ARM64. Excludes OS disk cache. |
| **Context Assembly Latency** | **< 300 ms (p95)** | Local SQLite queries + in-memory prompt assembly. *Requires local token estimation* ($\lceil \text{bytes} / 3.5 \rceil$); calling remote `count_tokens` over HTTPS will violate this SLA. |
| **Interactive Turn Latency** | **< 8.0 s (p95)** | Dominated by external Google Gemini API network latency and generation time (typically 1.5s – 5.0s for Flash; 3.0s – 7.0s for Pro). Aira acknowledges Telegram updates within 1.5s via `sendChatAction("typing")`. |
| **Emergency Kill-Switch Latency** | **< 3.0 s** | Target time from user `/cancel` command to aborting active `asyncio.Task` and closing open HTTP connections. |
