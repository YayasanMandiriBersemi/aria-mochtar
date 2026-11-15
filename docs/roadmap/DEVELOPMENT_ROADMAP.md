# AIRA MOCHTAR — Phased Engineering & Development Roadmap

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-ROADMAP-DEV-007` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Upstream Specifications** | `PRODUCT_VISION.md` (`DOC-PRD-VISION-001`), `PRODUCT_REQUIREMENTS.md` (`DOC-PRD-REQ-002`) |
| **Status** | Active Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Project Owners, Software Engineers, Systems Architects, QA Engineers |

---

## 1. Roadmap Overview & Phasing Principles

AIRA MOCHTAR evolves incrementally across four distinct engineering stages. Each stage must satisfy strict **Quality Release Gates** before advancing to the next stage. No premature multi-agent, cloud, or financial execution features may be built in early stages.

```
+-----------------------------------------------------------------------------------+
| STAGE 1: LOCAL AI PROTOTYPE (Weeks 1 - 6)                                         |
| Foundational Persona, SQLite WAL/FTS5, Local CLI & Telegram Bot, 4-Tier Security  |
+-----------------------------------------+-----------------------------------------+
                                          | [GATE-MVP-01, GATE-MVP-02, GATE-MVP-03]
                                          v
+-----------------------------------------------------------------------------------+
| STAGE 2: PERSISTENT PERSONAL AI SYSTEM (Weeks 7 - 14)                             |
| Cron Briefings, Hierarchical Memory (pgvector), Academic Engine, SOP Management  |
+-----------------------------------------+-----------------------------------------+
                                          | [GATE-STG2-01, GATE-STG2-02]
                                          v
+-----------------------------------------------------------------------------------+
| STAGE 3: MULTI-AGENT OPERATING SYSTEM (Weeks 15 - 24)                             |
| Domain Subagents, MCP Bus, WhatsApp API, Canva API, MT5 Read-Only Telemetry Bridge|
+-----------------------------------------+-----------------------------------------+
                                          | [GATE-STG3-01]
                                          v
+-----------------------------------------------------------------------------------+
| STAGE 4: CLOUD-BASED PLATFORM (Weeks 25+)                                         |
| 24/7 Cloud Control Plane, mTLS Remote Bridges, Web Dashboard, Full Observability  |
+-----------------------------------------------------------------------------------+
                                            [GATE-STG4-01]
```

---

## 2. Stage Breakdown & Deliverables

### Stage 1: Local AI Prototype (Weeks 1 – 6) — `MVP Target`

- **Goal:** Deliver a working, single-process, local-first assistant on the user's MacBook Air M2 that can converse via CLI and Telegram, manage tasks and notes, challenge flawed assumptions, enforce 4-tier security, and shut down cleanly via `/cancel`.
- **Milestones & Deliverables:**
  - **M1.1 (Environment & Config):** Repository setup, Python 3.12+ project configuration, Pydantic settings schema (`CMP-01`), `.env.example`, and test harness (`pytest`).
  - **M1.2 (Persistence & Audit):** SQLite 3 schema migrations (`WAL` mode + `FTS5` virtual tables), repository layer for tasks, notes, sessions, and preferences (`CMP-06`), append-only `audit_logs` table with SQLite `RAISE(ABORT)` triggers, and secret redaction filter (`CMP-09`).
  - **M1.3 (AI Provider & Context Assembly):** Abstract `LLMProviderPort`, official `google-genai` Gemini adapter with token ledger accounting (`CMP-05`), and `ContextManager` (`CMP-04`) with local token estimation ($\lceil \text{bytes} / 3.5 \rceil$) and `<untrusted_external_data>` delimiters.
  - **M1.4 (Governance & Core Engine):** 4-Tier `PermissionEngine` (`CMP-08`) with SHA-256 payload approval records, local tool registry (`CMP-07`), canonical persona system prompt, and `AiraCoreEngine` (`CMP-03`) turn loop.
  - **M1.5 (Interfaces & Control Socket):** Dual-channel cancellation model (`ADR-008`): in-process `CancelToken` + local Unix Domain Socket control (`data/aira.sock`) + SQLite cancellation table. Interactive CLI REPL (`aira chat`) and Telegram bot long-polling adapter (`CMP-02`) with `OwnerAuthGuard` enforcing `chat.type == "private"` and whitelisted owner IDs.
- **Stage 1 Exit Gates:**
  - `GATE-MVP-01`: Passes 20-prompt adversarial persona evaluation suite (anti-sycophancy, epistemic uncertainty, non-sentience).
  - `GATE-MVP-02`: 100% rejection of unauthorized Telegram IDs; zero secrets leaked in logs or prompts.
  - `GATE-MVP-03`: Persistent state survives process restart; `/cancel` halts active execution in $< 3.0$ seconds.

---

### Stage 2: Persistent Personal AI System (Weeks 7 – 14)

- **Goal:** Enable persistent cross-session memory, scheduled proactive briefings, structured decision records, SOP document generation, and verified academic literature reviews.
- **Milestones & Deliverables:**
  - **M2.1 (Workflow & Cron Scheduler):** Implement `WorkflowEngine` (`CMP-11`) with persistent cron jobs (`MorningBriefingJob`, `EveningBriefingJob`, `DailyBackupJob`), idempotency keys, and Telegram inline approval callbacks.
  - **M2.2 (Hierarchical Memory Upgrade):** Deploy PostgreSQL + `pgvector` (or `sqlite-vec`), migrate Stage 1 data via `aira db migrate-to-pg`, implement `SemanticMemory` hybrid search (BM25 + cosine RRF), and build `DecisionRecord` tracking (`FR-PERS-004`).
  - **M2.3 (Academic Intelligence Engine):** Implement `AcademicModule` (`CMP-13`) querying arXiv, OpenAlex, PubMed, and Crossref with mandatory DOI verification (`FR-ACAD-001`) and literature review comparison tables (`FR-ACAD-002`).
  - **M2.4 (Business & Message Staging):** Implement `ProjectService` (`FR-BIZ-001`), `DocumentService` for SOP templates (`FR-BIZ-002`), and `MessageDraftService` staging queue (`FR-COMM-003`).
  - **M2.5 (Notification Refinement):** Enforce Quiet Hours batching, alert deduplication, and Sink-Aware Taint Policy (`ISS-05`).
- **Stage 2 Exit Gates:**
  - `GATE-STG2-01`: Morning and Evening briefings execute automatically on schedule for 14 consecutive days without duplication.
  - `GATE-STG2-02`: 100% of academic literature outputs contain verified DOIs/arXiv IDs with zero fabricated citations.

---

### Stage 3: Multi-Agent Operating System (Weeks 15 – 24)

- **Goal:** Scale across domains with specialized subagents, Model Context Protocol (MCP) bus, WhatsApp Business Cloud API, Canva design automation, and MetaTrader 5 (MT5) quantitative telemetry.
- **Milestones & Deliverables:**
  - **M3.1 (Agent Runtime & Sandboxes):** Supervisor-subagent decomposition (`CMP-14`), declarative subagent manifests (`PERM-003`), step limits (15 steps), and token budgets.
  - **M3.2 (Model Context Protocol Bus):** Standardized MCP client bus (`CMP-15`) over `stdio` and `SSE`/HTTP.
  - **M3.3 (External Communication & Creative Integrations):** Official WhatsApp Business Cloud API adapter (`INT-003`) with webhook signature verification, and Canva Connect API/MCP integration (`INT-004`).
  - **M3.4 (Financial Intelligence & MT5 Bridge):** Standalone read-only `aira-mt5-bridge` on Windows/VPS (`INT-006`, `CMP-16`), automated drawdown/margin risk alerts (`FR-FIN-002`), deterministic trading analytics (`FR-FIN-003`), historical backtester (`FR-FIN-004`), and position sizing calculator (`FR-FIN-005`). Hard financial isolation gate enforced (`PERM-004`).
- **Stage 3 Exit Gates:**
  - `GATE-STG3-01`: Subagents respect least-privilege boundaries; MT5 telemetry and risk calculations match mathematical benchmarks to 4 decimal places; zero live trade execution capabilities exposed.

---

### Stage 4: Cloud-Based Platform (Weeks 25+)

- **Goal:** Evolve into a 24/7 high-availability cloud control plane with encrypted remote bridges and a Web Executive Dashboard.
- **Milestones & Deliverables:**
  - **M4.1 (Cloud Control Plane):** Containerized deployment on managed cloud runtime (Cloud Run / VPS), managed PostgreSQL + `pgvector`, and cloud secret management.
  - **M4.2 (Encrypted Bridge Coordinator):** Mutual-TLS (mTLS) or WireGuard encrypted tunnels connecting Cloud Control Plane to the Windows MT5 VPS and local MacBook workspace.
  - **M4.3 (Web Executive Dashboard):** Authenticated web interface (`CMP-17`) for memory graphs, pending HITL approvals, subagent traces, and financial risk charts.
  - **M4.4 (Enterprise Observability):** Distributed telemetry, automated encrypted backups, point-in-time recovery, and multi-model dynamic failover routing.
- **Stage 4 Exit Gates:**
  - `GATE-STG4-01`: $\ge 99.9\%$ availability for core messaging and monitoring loops; automated recovery from node restarts.
