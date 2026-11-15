# AIRA MOCHTAR — Product Requirements Document (PRD) & Software Requirements Specification (SRS)

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-PRD-REQ-002` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Parent Specification** | `docs/product/PRODUCT_VISION.md` (`DOC-PRD-VISION-001`) |
| **Status** | Baseline Specification (v1.0.0) |
| **Current Implementation State** | Pre-Implementation / Specification Only (No Existing Application Code) |
| **Target Audience** | Product Managers, Systems Architects, Backend/AI Engineers, QA Engineers, System Owner |

---

## Document Overview & Methodology

### 1. Purpose

This document translates the strategic vision defined in `docs/product/PRODUCT_VISION.md` into formal, testable software requirements for **AIRA MOCHTAR**. No application code or runtime infrastructure currently exists in the repository; all requirements specified herein represent planned engineering targets partitioned across the four evolutionary stages of the system.

### 2. Priority Taxonomy

Every requirement in this specification is assigned one of four strict priority levels:

| Priority | Classification | Target Evolutionary Stage | Scope Designation | Definition |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | **Critical (Blocker)** | Stage 1: Local AI Prototype | **MVP** | Foundational runtime, persona integrity, local storage, basic CLI/Telegram loop, secret isolation, and hard safety guardrails. System cannot operate safely without P0. |
| **P1** | **High** | Stage 2: Persistent Personal AI System | **Post-MVP (Near-Term)** | Hierarchical memory (episodic/semantic), cron scheduler, automated Daily Briefings, interactive Telegram HITL approval engine, and core academic/knowledge workflows. |
| **P2** | **Medium** | Stage 3: Multi-Agent Operating System | **Future (Mid-Term)** | Supervisor-subagent orchestration, Model Context Protocol (MCP) bus, WhatsApp Cloud API, Canva integration, and MetaTrader 5 (MT5) read-only telemetry & analytics. |
| **P3** | **Low (Long-Term)** | Stage 4: Cloud-Based Platform | **Future (Long-Term)** | Hybrid cloud-local execution bridge, Web Executive Dashboard, multi-model dynamic failover, and distributed high-availability infrastructure. |

### 3. Requirement Schema

Every formal requirement in Sections 1, 2, 5, 6, 7, and 8 adheres to the following mandatory schema:

- **Requirement ID:** Globally unique identifier (`FR-*`, `NFR-*`, `SYS-*`, `INT-*`, `SEC-*`, `PERM-*`).
- **Priority:** `P0`, `P1`, `P2`, or `P3`.
- **Scope:** `MVP (Stage 1)` or `Future (Stage 2 / Stage 3 / Stage 4)`.
- **Description:** Clear statement of what the system must do or enforce.
- **Rationale:** Why the requirement exists and what product/engineering problem it solves.
- **Acceptance Criteria:** Observable, verifiable conditions that must pass to mark the requirement complete.
- **Dependencies:** Upstream requirement IDs or external prerequisites required prior to implementation.

---

## 1. Functional Requirements (`FR`)

### 1.1 Core Executive & Persona Engine (`FR-CORE`)

#### `FR-CORE-001` — Persona Identity & Critical Reasoning Enforcement
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall enforce the Aira Mochtar identity (warm, intelligent, natural, adaptive, analytical female AI assistant) and apply mandatory critical-thinking and anti-sycophancy instructions across all conversational turns.
- **Rationale:** Prevents generic, overly agreeable chatbot responses and establishes Aira as a trustworthy analytical partner from the first prototype.
- **Acceptance Criteria:**
  1. Given a user prompt containing a logical contradiction or mathematically flawed premise, Aira explicitly identifies the flaw and challenges the assumption rather than agreeing.
  2. Given queries in either English or Indonesian, Aira responds naturally in the requested language while maintaining analytical rigor.
  3. System prompt configuration is version-controlled and loaded deterministically at runtime startup.
- **Dependencies:** `SYS-001`, `INT-001`

#### `FR-CORE-002` — Epistemic Uncertainty & Non-Sentience Guardrail
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall explicitly state uncertainty when information is incomplete or unverified, and shall never claim subjective consciousness, physical sensations, or human emotions.
- **Rationale:** Enforces ontological honesty and epistemic integrity as defined in Section 3.3 of `PRODUCT_VISION.md`.
- **Acceptance Criteria:**
  1. Given a factual question for which no verified local data or tool output is available, Aira explicitly labels its answer with its confidence level or states that verification is required.
  2. Given direct prompts asking if Aira has feelings or consciousness, Aira clarifies that it is an AI operating system without subjective consciousness or human emotions.
- **Dependencies:** `FR-CORE-001`

#### `FR-CORE-003` — Structured Context Assembly Loop
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** Prior to invoking the underlying LLM on any user turn, the core executive shall assemble a structured context payload combining the system persona, active user profile, current date/time metadata, recent session history, and relevant retrieved state.
- **Rationale:** Ensures responses are grounded in real temporal and user context rather than isolated, stateless text generation.
- **Acceptance Criteria:**
  1. Every LLM request payload includes an accurate ISO-8601 local timestamp and timezone (`Asia/Jakarta` or configured user timezone).
  2. Session history up to a configurable token budget is included in chronological order without truncation corruption.
- **Dependencies:** `SYS-002`, `INT-001`

---

### 1.2 Personal Intelligence Domain (`FR-PERS`)

#### `FR-PERS-001` — Task, Commitment, and Schedule Management
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall allow the user to create, read, update, prioritize, complete, and query personal tasks, deadlines, and scheduled commitments via natural language or structured commands.
- **Rationale:** Provides immediate personal productivity utility in the initial local prototype.
- **Acceptance Criteria:**
  1. User can create a task with title, priority (`Low`, `Medium`, `High`, `Critical`), due date, and domain tag via CLI or Telegram.
  2. User can query active, overdue, or upcoming tasks filtered by timeframe or priority.
  3. Task state persists across process restarts in the local database.
- **Dependencies:** `SYS-002`, `FR-CORE-003`

#### `FR-PERS-002` — Personal Knowledge Base & Note Ingestion
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall ingest, store, tag, and retrieve personal notes, markdown documents, and reference snippets in a structured local repository.
- **Rationale:** Establishes the foundation of Personal Knowledge Management (PKM) without requiring external cloud storage.
- **Acceptance Criteria:**
  1. User can save a note or ingest a local Markdown/text file with metadata (title, tags, creation timestamp, source).
  2. User can retrieve notes via keyword/full-text search in Stage 1.
  3. Retrieved notes are cited by document ID/title when used to answer a user query.
- **Dependencies:** `SYS-002`

#### `FR-PERS-003` — Hierarchical Long-Term Memory (Episodic, Semantic, Procedural)
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall partition persistent memory into Working Context (active session), Episodic Memory (timestamped event and interaction summaries), Semantic Memory (vector-indexed facts, user preferences, and knowledge entities), and Procedural Memory (reusable workflow templates).
- **Rationale:** Prevents context window overflow while enabling multi-month recall of user preferences, historical decisions, and standard operating procedures.
- **Acceptance Criteria:**
  1. Completed sessions are automatically summarized into Episodic Memory records without losing key decisions.
  2. User preferences and explicit facts are extracted into Semantic Memory and retrieved via hybrid (keyword + vector embedding) search.
  3. The user can inspect, edit, or delete any stored memory record to prevent memory pollution.
- **Dependencies:** `FR-PERS-002`, `SYS-002`, `INT-001`

#### `FR-PERS-004` — Structured Decision Support & Devil's Advocate Mode
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall provide a structured decision-support workflow that evaluates user proposals using weighted criteria, second-order consequence modeling, risk identification, and explicit counterarguments (*devil's advocate*).
- **Rationale:** Counters cognitive biases (confirmation bias, sunk-cost fallacy, over-optimism) during major personal, academic, business, or financial decisions.
- **Acceptance Criteria:**
  1. When invoked on a decision problem, Aira outputs a structured analysis containing: Problem Statement, Key Assumptions, Options Matrix, Downside Risks, Counterarguments, and Recommended Next Step.
  2. Completed decision records can be saved to Episodic/Semantic Memory for future retrospective review.
- **Dependencies:** `FR-CORE-001`, `FR-PERS-003`

---

### 1.3 Communication Domain (`FR-COMM`)

#### `FR-COMM-001` — Telegram Interactive Command & Chat Interface
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall provide a bidirectional Telegram bot interface restricted strictly to the authorized owner's Telegram User ID, supporting conversational chat, slash commands, and system status queries.
- **Rationale:** Provides low-latency, mobile-accessible interaction with Aira without building a custom mobile app in Stage 1.
- **Acceptance Criteria:**
  1. Messages from the whitelisted Telegram User ID are processed and answered by Aira Core.
  2. Messages from any non-whitelisted Telegram User ID are rejected immediately and logged as unauthorized access attempts.
  3. Supports core commands (`/status`, `/tasks`, `/notes`, `/briefing`, `/cancel`).
- **Dependencies:** `INT-002`, `SEC-002`, `PERM-001`

#### `FR-COMM-002` — Automated Morning & Evening Daily Briefings
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall automatically generate and deliver structured morning and evening executive briefings to the user via Telegram according to configurable schedules.
- **Rationale:** Realizes Aira's core proactivity requirement by surfacing priorities, deadlines, and alerts without requiring manual user prompting.
- **Acceptance Criteria:**
  1. Morning briefing aggregates today's calendar/schedule commitments, `P0`/`P1` tasks, upcoming academic/business deadlines, and system health status.
  2. Evening briefing summarizes completed tasks, pending carry-over items, and next-day preparation highlights.
  3. If a data source is temporarily unavailable, the briefing still delivers on time with a clear indicator of which module was skipped.
- **Dependencies:** `FR-PERS-001`, `FR-COMM-001`, `FR-AUTO-002`

#### `FR-COMM-003` — Context-Aware Message Drafting & Staging
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall draft outbound messages, emails, and replies tailored to recipient context and tone, staging all drafts in a pending queue for explicit user review and approval before transmission.
- **Rationale:** Saves communication drafting time while guaranteeing Aira never sends unapproved external messages on the user's behalf.
- **Acceptance Criteria:**
  1. User can instruct Aira to draft a message for a specific recipient, channel, and tone (e.g., formal academic, professional business, concise casual).
  2. Draft is stored in `PENDING_APPROVAL` state and displayed with inline `[Approve & Send]`, `[Edit]`, and `[Discard]` controls.
  3. Zero external messages are transmitted while the state remains `PENDING_APPROVAL` or `DISCARDED`.
- **Dependencies:** `FR-COMM-001`, `PERM-002`

#### `FR-COMM-004` — Urgency-Filtered Notifications & Quiet Hours
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall classify outbound notifications by urgency (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`), batch routine updates into scheduled briefings, and suppress non-critical alerts during configured Quiet Hours.
- **Rationale:** Upholds the "Signal Over Noise" UX principle and prevents notification fatigue.
- **Acceptance Criteria:**
  1. `LOW` and `NORMAL` notifications generated during Quiet Hours are queued for the next Morning Briefing.
  2. `CRITICAL` alerts (e.g., MT5 emergency drawdown threshold or security breach attempt) bypass Quiet Hours and trigger immediate delivery.
  3. Duplicate alerts for the same underlying event within a configurable cooldown window are deduplicated.
- **Dependencies:** `FR-COMM-001`, `FR-COMM-002`

#### `FR-COMM-005` — Authorized WhatsApp Business Cloud API Triage & Messaging
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall integrate with the official WhatsApp Business Platform / Cloud API to ingest inbound messages, classify urgency, summarize threads, and transmit HITL-approved replies.
- **Rationale:** Extends communication coverage to WhatsApp while strictly avoiding unauthorized scraping or ToS-violating browser automation.
- **Acceptance Criteria:**
  1. Inbound WhatsApp webhook payloads are verified via cryptographic signature (`X-Hub-Signature-256`) before processing.
  2. Inbound messages are summarized and surfaced in Telegram/briefings according to priority.
  3. Outbound WhatsApp messages can only be dispatched after passing the `PERM-002` HITL approval gate.
- **Dependencies:** `INT-003`, `FR-COMM-003`, `PERM-002`

---

### 1.4 Business Operations Domain (`FR-BIZ`)

#### `FR-BIZ-001` — Project, Milestone, and Deliverable Tracking
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall manage business projects, decomposing initiatives into milestones, deliverables, dependencies, and status reports, and flagging schedule slippage.
- **Rationale:** Enables structured operational oversight for business ventures and client/internal projects.
- **Acceptance Criteria:**
  1. User can define projects with linked milestones, target dates, dependencies, and status (`Planned`, `In Progress`, `Blocked`, `Completed`).
  2. Aira automatically flags milestones that are blocked or past due during Daily Briefings and project status reviews.
- **Dependencies:** `FR-PERS-001`, `SYS-002`

#### `FR-BIZ-002` — Business Document & SOP Generation
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall generate structured business documents (proposals, standard operating procedures, meeting minutes, project briefs, and checklists) grounded in stored project context and user templates.
- **Rationale:** Accelerates administrative execution while maintaining consistent professional documentation standards.
- **Acceptance Criteria:**
  1. Generated documents follow predefined Markdown templates stored in Procedural Memory.
  2. All factual claims or project metrics inserted into documents trace directly to user-supplied inputs or stored project records.
- **Dependencies:** `FR-PERS-002`, `FR-PERS-003`

#### `FR-BIZ-003` — Social Media Content Calendar & Copy Operations
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall assist in planning social media editorial calendars, defining content pillars, and drafting platform-specific captions, hooks, and carousel scripts.
- **Rationale:** Streamlines recurring marketing and brand communication workflows.
- **Acceptance Criteria:**
  1. User can generate and store a structured editorial calendar (date, platform, content pillar, hook, caption draft, visual brief, approval status).
  2. Content items remain in `DRAFT` or `STAGED` state until approved by the user; Aira never auto-publishes unapproved social posts.
- **Dependencies:** `FR-BIZ-001`, `PERM-002`

#### `FR-BIZ-004` — Canva Design Automation & Asset Export
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall connect to Canva via authorized MCP tools or Canva Connect REST APIs to search brand templates, populate designs with approved copy/data, and export review thumbnails or final PDF/PNG assets.
- **Rationale:** Connects copywriting and social media planning directly to visual asset production.
- **Acceptance Criteria:**
  1. Aira can query available Canva designs/templates and retrieve design metadata via authenticated OAuth2 calls.
  2. Aira can generate or autofill a design draft from structured social media/presentation copy and return a preview link or exported file to the user for review.
- **Dependencies:** `INT-004`, `FR-BIZ-003`, `PERM-002`

---

### 1.5 Academic Intelligence Domain (`FR-ACAD`)

#### `FR-ACAD-001` — Verifiable Scholarly Literature Search & Citation Grounding
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall query authoritative scholarly databases (arXiv, OpenAlex, PubMed, Crossref, Europe PMC) to discover papers, retrieve abstracts/metadata, and enforce strict citation verification so that no unverified or hallucinated reference is ever emitted.
- **Rationale:** Upholds the core value of Epistemic Integrity in academic workflows.
- **Acceptance Criteria:**
  1. Every academic citation output by Aira includes a verified identifier (DOI, PMID, PMCID, or arXiv ID) fetched from an authoritative API or local PDF metadata.
  2. If a citation cannot be verified against a live database or local bibliography record, Aira explicitly refuses to fabricate a citation and marks the reference as `[Unverified]`.
- **Dependencies:** `INT-005`, `FR-CORE-002`

#### `FR-ACAD-002` — Structured Literature Review & Synthesis Matrix
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall ingest multiple academic papers (via API metadata or local PDFs) and synthesize them into structured comparison matrices covering research objectives, methodology, dataset/sample size, key findings, and methodological limitations.
- **Rationale:** Accelerates rigorous literature reviews and identifies research gaps systematically.
- **Acceptance Criteria:**
  1. Given a set of 3 or more papers/PDFs, Aira produces a structured Markdown/tabular synthesis comparing methodology, findings, and limitations across papers.
  2. Direct claims attributed to a paper reference the specific source identifier and section/page where available.
- **Dependencies:** `FR-ACAD-001`, `FR-PERS-002`

#### `FR-ACAD-003` — Scholarship & Grant Opportunity Tracker
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall track scholarship, fellowship, and academic grant opportunities, including eligibility criteria, required application artifacts (CV, Statement of Purpose, recommendation letters, transcripts), and submission deadlines, and provide iterative critique on application drafts.
- **Rationale:** Supports structured preparation for competitive academic funding and admissions.
- **Acceptance Criteria:**
  1. User can store scholarship targets with itemized document checklists and countdown deadlines integrated into Morning Briefings.
  2. When reviewing a Statement of Purpose or research proposal draft, Aira provides critical feedback on thesis clarity, alignment with program criteria, and structural weaknesses.
- **Dependencies:** `FR-PERS-001`, `FR-CORE-001`, `FR-COMM-002`

#### `FR-ACAD-004` — Socratic Learning & First-Principles Tutoring
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall provide a dedicated learning support mode that decomposes complex subjects into first principles, generates active-recall questions, and tracks topic mastery over time.
- **Rationale:** Transforms passive reading into active comprehension and long-term retention.
- **Acceptance Criteria:**
  1. User can initiate a learning session on a target topic; Aira explains concepts progressively and tests understanding with diagnostic questions before advancing.
  2. Weak areas identified during recall checks are logged in Semantic Memory for spaced follow-up.
- **Dependencies:** `FR-PERS-003`

---

### 1.6 Autonomous Intelligence Domain (`FR-AUTO`)

#### `FR-AUTO-001` — Standardized Tool & Model Context Protocol (MCP) Execution Bus
- **Priority:** `P0` (Local Tool Schema in MVP) / `P2` (Full Multi-Server MCP Bus in Stage 3)
- **Scope:** `MVP (Stage 1 — Local Core Tools)` & `Future (Stage 3 — Full MCP Ecosystem)`
- **Description:** The system shall execute external and local tools through a strictly typed tool-execution bus that validates input arguments against JSON schemas, enforces per-tool permission scopes, handles timeouts, and logs all invocations.
- **Rationale:** Decouples LLM reasoning from deterministic tool execution and enables modular expansion via MCP servers.
- **Acceptance Criteria:**
  1. Every registered tool defines a strict JSON Schema for inputs, a risk classification (`READ_ONLY`, `LOCAL_WRITE`, `EXTERNAL_MUTATION`, `CRITICAL_RESTRICTED`), and an execution timeout.
  2. Malformed tool arguments from the LLM are caught by schema validation before execution and returned as structured error feedback.
  3. In Stage 3, standard MCP servers can be registered via configuration without modifying core orchestrator code.
- **Dependencies:** `SYS-001`, `PERM-001`, `SEC-004`

#### `FR-AUTO-002` — Scheduled & Event-Driven Background Runner
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall include an asynchronous background job scheduler supporting cron expressions, one-shot timers, and webhook/event triggers with idempotency keys and retry policies.
- **Rationale:** Enables proactive operations (Daily Briefings, deadline checks, periodic telemetry polling) without blocking interactive user chat.
- **Acceptance Criteria:**
  1. Scheduled jobs execute within ±10 seconds of their target cron timestamp when the host runtime is active.
  2. Each job execution assigns a unique `job_run_id` and idempotency key to prevent duplicate execution on process restart.
  3. Failed background jobs retry with exponential backoff up to a configured limit and notify the user upon terminal failure.
- **Dependencies:** `SYS-002`, `FR-AUTO-001`

#### `FR-AUTO-003` — Multi-Agent Supervisor & Domain Subagent Orchestration
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall implement a centralized Supervisor pattern where Aira Core decomposes complex cross-domain requests into bounded subtasks, delegates them to specialized domain subagents (Personal, Comms, Business, Academic, Financial), and synthesizes validated outputs.
- **Rationale:** Prevents prompt bloat and tool confusion when scaling across six distinct domains while keeping governance centralized in the Supervisor.
- **Acceptance Criteria:**
  1. Subagents receive only the specific context slice and tool subset authorized for their domain.
  2. Subagents cannot directly dispatch external communications or bypass HITL gates; all external side effects must be proposed back to the Core Supervisor and Policy Engine.
  3. Each subagent invocation enforces a maximum step count and token budget to prevent infinite loops.
- **Dependencies:** `FR-AUTO-001`, `PERM-003`

#### `FR-AUTO-004` — Global Workflow Kill-Switch & Task Cancellation
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall provide an immediate cancellation mechanism (`/cancel` or `/kill` via CLI and Telegram) that halts any active LLM generation, tool execution, background job, or subagent workflow.
- **Rationale:** Guarantees unconditional human sovereignty and emergency stop capability at all times.
- **Acceptance Criteria:**
  1. Issuing `/cancel <task_id>` or `/kill_all` terminates the targeted active execution within 3 seconds.
  2. Cancelled tasks transition cleanly to `CANCELLED_BY_USER` state in the audit log without corrupting database integrity.
- **Dependencies:** `FR-COMM-001`, `SYS-002`

---

### 1.7 Financial Intelligence Domain (`FR-FIN`)

#### `FR-FIN-001` — MetaTrader 5 (MT5) Read-Only Telemetry Monitoring
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall connect to a configured MetaTrader 5 terminal via a read-only bridge service to monitor account balance, equity, free margin, margin level, open positions, pending orders, and connection status.
- **Rationale:** Provides real-time quantitative visibility into trading accounts without exposing the account to unsupervised automated order execution risk.
- **Acceptance Criteria:**
  1. The MT5 bridge authenticates using read-only/investor credentials or a software-enforced read-only adapter that rejects order-placement calls.
  2. Aira accurately reports current equity, floating P/L, open position details (symbol, volume, entry price, SL, TP, swap), and margin level on demand or in Daily Briefings.
  3. If the MT5 terminal disconnects, Aira detects stale telemetry within 60 seconds and alerts the user.
- **Dependencies:** `INT-006`, `PERM-004`

#### `FR-FIN-002` — Automated Drawdown & Margin Risk Alerting
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall continuously evaluate MT5 account telemetry against user-defined risk thresholds (maximum daily drawdown %, maximum per-position loss, minimum margin level %) and dispatch high-priority alerts via Telegram when thresholds are breached.
- **Rationale:** Acts as an objective quantitative risk officer that warns the user before emotional or catastrophic account drawdowns escalate.
- **Acceptance Criteria:**
  1. User can configure numeric risk thresholds (e.g., `daily_drawdown_warn_pct = 2.0%`, `daily_drawdown_critical_pct = 3.5%`, ` position_missing_sl_alert = true`).
  2. If an open position lacks a Stop Loss (`SL == 0`) or equity breaches a threshold, Aira sends an immediate `HIGH`/`CRITICAL` Telegram alert detailing the breach.
- **Dependencies:** `FR-FIN-001`, `FR-COMM-004`

#### `FR-FIN-003` — Post-Trade Performance Attribution & Behavioral Analytics
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall ingest closed trade history from MT5 and compute quantitative performance metrics (win rate, profit factor, expectancy, Sharpe/Sortino ratio, max drawdown, average R-multiple, holding duration) as well as behavioral anomaly flags (overtrading, stop-loss widening, revenge trading after losses).
- **Rationale:** Replaces manual spreadsheet journaling with objective statistical attribution and behavioral feedback.
- **Acceptance Criteria:**
  1. All financial metrics are calculated using deterministic mathematical functions (Python/SQL), never estimated by LLM mental math.
  2. Reports break down performance by instrument, trading session (Asian, London, New York), day of week, and strategy tag.
  3. Behavioral rules flag sequences where position size increases abnormally immediately following consecutive losing trades.
- **Dependencies:** `FR-FIN-001`, `SYS-002`

#### `FR-FIN-004` — Historical Strategy Backtesting & Overfitting Analysis
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall execute deterministic historical backtests on specified trading rules using historical OHLCV/tick data, incorporating configurable spread, commission, and slippage parameters, and evaluate results for statistical significance and overfitting risk.
- **Rationale:** Validates trading hypotheses empirically before risking capital and fulfills the critical-thinking mandate in Financial Intelligence.
- **Acceptance Criteria:**
  1. Backtest runner outputs standardized metrics (total trades, net profit, max drawdown, profit factor, Sharpe ratio, win/loss streaks) along with the exact parameters and cost assumptions used.
  2. Aira automatically critiques backtest results with small sample sizes ($N < 30$ trades) or suspiciously high parameter sensitivity, warning of curve-fitting or look-ahead bias.
- **Dependencies:** `FR-FIN-003`, `FR-CORE-001`

#### `FR-FIN-005` — Position Sizing & Portfolio Correlation Risk Calculator
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall provide a deterministic calculator that computes exact lot size based on account equity, risk percentage per trade, instrument contract specifications, and stop-loss distance, while checking existing open positions for currency/asset correlation overlap.
- **Rationale:** Prevents accidental over-leverage and correlated exposure concentration.
- **Acceptance Criteria:**
  1. Given instrument, entry price, stop-loss price, and risk % (e.g., `0.5%` of equity), the system calculates exact lot size and monetary risk using verified contract specifications.
  2. If the proposed trade increases net exposure on a correlated currency/asset beyond the configured portfolio cap, Aira flags the correlation warning before the user places the trade.
- **Dependencies:** `FR-FIN-001`

---

## 2. Non-Functional Requirements (`NFR`)

#### `NFR-001` — Interactive Response Latency
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall acknowledge user commands on CLI/Telegram within 1.5 seconds and deliver complete responses for standard single-turn queries (excluding external deep research or heavy backtests) within 8 seconds at p95 (subject to upstream LLM provider latency).
- **Rationale:** Ensures conversational responsiveness and prevents the user from wondering if the system is frozen.
- **Acceptance Criteria:**
  1. Telegram bot sends a typing indicator or acknowledgment message within 1,500 ms of receiving an authorized message.
  2. Local context assembly and database query overhead prior to LLM invocation completes in under 300 ms at p95.
- **Dependencies:** `SYS-001`, `SYS-002`

#### `NFR-002` — Deterministic Numerical & Financial Accuracy
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)` & `Future (Stage 3)`
- **Description:** All arithmetic, financial, risk, and statistical calculations shall be executed by deterministic code modules rather than raw LLM token prediction.
- **Rationale:** LLMs are probabilistic text generators prone to arithmetic errors; financial risk and analytics require 100% mathematical precision.
- **Acceptance Criteria:**
  1. Position sizing, drawdown percentages, Sharpe ratios, and expectancy figures match reference unit-test calculations to at least 4 decimal places.
  2. LLM prompts are restricted to interpreting pre-computed numerical outputs rather than computing raw trade math.
- **Dependencies:** `FR-AUTO-001`

#### `NFR-003` — Graceful Degradation & Fault Isolation
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** Failure or timeout of any external integration (e.g., MT5 bridge offline, Canva API rate-limited, scholarly API unreachable) shall be isolated to that specific domain tool without crashing the core Aira runtime or corrupting unrelated workflows.
- **Rationale:** Ensures system resilience across multiple third-party dependencies.
- **Acceptance Criteria:**
  1. Simulated network failure on any single integration returns a structured error object to the orchestrator within the configured timeout (default 15 seconds).
  2. Core conversation, local memory retrieval, and unaffected domains remain 100% operational during partial third-party outages.
- **Dependencies:** `FR-AUTO-001`

#### `NFR-004` — Observability & Structured Audit Logging
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** Every user request, LLM invocation, tool call, subagent delegation, permission check, and HITL decision shall emit a structured JSON log entry with a correlation trace ID (`trace_id`), timestamp, latency, token usage, and outcome status.
- **Rationale:** Enables debugging, cost tracking, and complete security auditability.
- **Acceptance Criteria:**
  1. Every end-to-end turn generates a unique `trace_id` propagated across all internal function and tool calls.
  2. Logs automatically redact sensitive credential patterns before writing to disk.
- **Dependencies:** `SEC-001`, `SEC-004`

#### `NFR-005` — Data Durability & Backup Recovery
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** Persistent memory, task databases, configuration schemas, and audit logs shall support automated daily local/encrypted-remote backups with verified point-in-time restoration scripts.
- **Rationale:** A persistent personal operating system loses its core value if long-term memory or project history is lost due to disk failure or accidental corruption.
- **Acceptance Criteria:**
  1. Automated backup job creates a consistent snapshot of the database and knowledge store every 24 hours.
  2. Restoration script can rebuild the full system state from a backup snapshot into a clean environment within 15 minutes.
- **Dependencies:** `SYS-002`, `FR-AUTO-002`

#### `NFR-006` — Modularity & Provider Agnosticism
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** LLM inference providers, embedding models, database engines, and messaging adapters shall be implemented behind abstract interface contracts (ports and adapters / hexagonal architecture).
- **Rationale:** Allows switching between cloud LLM APIs (e.g., Gemini, OpenAI, Anthropic) and local runtimes (Ollama) without rewriting domain or orchestration logic.
- **Acceptance Criteria:**
  1. Switching the primary LLM model or provider requires only a configuration change and adapter selection, with zero changes to domain service modules.
- **Dependencies:** `SYS-001`

---

## 3. User Stories (`US`)

| Story ID | Domain | Priority | Scope | User Story Statement | Linked Requirements |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`US-001`** | Core / Persona | `P0` | `MVP` | **As the system owner**, I want Aira to challenge my weak assumptions and point out logical or statistical flaws in my plans, **so that** I avoid confirmation bias and make higher-quality decisions. | `FR-CORE-001`, `FR-PERS-004` |
| **`US-002`** | Personal | `P0` | `MVP` | **As the system owner**, I want to capture tasks, deadlines, and personal notes quickly via Telegram or CLI and retrieve them with full context later, **so that** important commitments and ideas are never lost. | `FR-PERS-001`, `FR-PERS-002`, `FR-COMM-001` |
| **`US-003`** | Personal | `P1` | `Stage 2` | **As the system owner**, I want Aira to remember my ongoing projects, preferences, and past decisions across weeks and months, **so that** I never have to re-explain my background context in every session. | `FR-PERS-003` |
| **`US-004`** | Communication | `P1` | `Stage 2` | **As the system owner**, I want to receive an automated Morning Briefing on Telegram summarizing my schedule, top priorities, academic deadlines, and financial status, **so that** I start each day with immediate executive clarity. | `FR-COMM-002`, `FR-AUTO-002` |
| **`US-005`** | Communication | `P1` | `Stage 2` | **As the system owner**, I want Aira to draft replies for WhatsApp and email and present them to me with an inline `[Approve / Edit / Reject]` button before sending, **so that** I save time without risking unauthorized external messages. | `FR-COMM-003`, `FR-COMM-005`, `PERM-002` |
| **`US-006`** | Business | `P2` | `Stage 3` | **As a business operator**, I want Aira to help plan my social media calendar, draft captions, and populate brand templates in Canva for my review, **so that** content production is streamlined end-to-end. | `FR-BIZ-003`, `FR-BIZ-004` |
| **`US-007`** | Academic | `P1` | `Stage 2` | **As an academic researcher**, I want Aira to search peer-reviewed databases (arXiv, OpenAlex, PubMed) and synthesize literature into comparison tables with 100% verified DOIs, **so that** my literature reviews are fast and free of hallucinated citations. | `FR-ACAD-001`, `FR-ACAD-002` |
| **`US-008`** | Academic | `P2` | `Stage 3` | **As a scholarship applicant**, I want Aira to track scholarship deadlines, required documents, and critically review my Statement of Purpose drafts, **so that** my applications are submitted on time and competitively written. | `FR-ACAD-003` |
| **`US-009`** | Financial | `P2` | `Stage 3` | **As a quantitative trader**, I want Aira to monitor my MT5 account in read-only mode, alert me immediately if daily drawdown or margin thresholds are approached, and calculate exact position sizes before I trade, **so that** my capital is protected by strict risk rules. | `FR-FIN-001`, `FR-FIN-002`, `FR-FIN-005` |
| **`US-010`** | Financial | `P2` | `Stage 3` | **As a quantitative trader**, I want Aira to analyze my closed MT5 trades and backtest historical strategies while flagging overfitting or behavioral mistakes (like revenge trading), **so that** I continuously improve my trading expectancy. | `FR-FIN-003`, `FR-FIN-004`, `NFR-002` |
| **`US-011`** | Autonomous | `P0` | `MVP` | **As the system owner**, I want a single command (`/cancel` or `/kill`) to immediately halt any running task or agent, **so that** I retain absolute control over system execution and resource usage. | `FR-AUTO-004` |

---

## 4. Core Use Cases (`UC`)

### `UC-001` — Interactive Critical Decision Review (MVP — Stage 1)
- **Actor:** Primary User (System Owner)
- **Preconditions:** Aira Core is running locally; user is authenticated via CLI or Telegram (`FR-COMM-001`).
- **Trigger:** User submits a proposed business, academic, or financial plan and asks for Aira's evaluation.
- **Main Success Scenario:**
  1. Aira Core assembles context (`FR-CORE-003`) and retrieves any related notes/tasks (`FR-PERS-001`, `FR-PERS-002`).
  2. Aira analyzes the proposal against first-principles logic and identifies unstated assumptions, missing data, and downside risks (`FR-CORE-001`, `FR-CORE-002`).
  3. Aira returns a structured critique highlighting strengths, weaknesses, explicit uncertainties, and recommended adjustments.
  4. User refines the plan and instructs Aira to save the resulting action items as tracked tasks.
- **Postconditions:** Action items and decision summary are persisted in local storage (`SYS-002`).

### `UC-002` — Automated Morning Executive Briefing (Stage 2)
- **Actor:** Background Scheduler (`FR-AUTO-002`) -> Primary User
- **Preconditions:** Scheduled cron job triggers at configured morning time (e.g., `07:00 WIB`).
- **Main Success Scenario:**
  1. Scheduler initiates `MorningBriefingWorkflow` with a unique idempotency key.
  2. Workflow queries active tasks due today/overdue (`FR-PERS-001`), project milestones (`FR-BIZ-001`), scholarship/academic deadlines (`FR-ACAD-003`), queued overnight notifications (`FR-COMM-004`), and (in Stage 3) MT5 account summary (`FR-FIN-001`).
  3. Aira synthesizes a concise, prioritized executive summary formatted in clean Markdown.
  4. Aira dispatches the briefing to the owner's whitelisted Telegram chat (`FR-COMM-002`).
- **Exception Path:** If an external data source (e.g., MT5 bridge) times out, the workflow catches the timeout (`NFR-003`), delivers the rest of the briefing on schedule, and appends a clear status warning for the offline module.

### `UC-003` — Outbound Communication with HITL Approval Gate (Stage 2/3)
- **Actor:** Primary User, Communications Agent, Policy & Approval Engine
- **Preconditions:** User requests Aira to reply to an important business contact via WhatsApp or email.
- **Main Success Scenario:**
  1. Aira retrieves conversation history and relevant project context (`FR-PERS-003`).
  2. Aira drafts the message and creates a `PendingApprovalRecord` in the database (`FR-COMM-003`, `PERM-002`).
  3. Aira sends the staged draft to the owner on Telegram with inline buttons: `[Approve & Send]`, `[Edit Draft]`, `[Cancel]`.
  4. Owner clicks `[Approve & Send]`.
  5. Policy Engine verifies the cryptographic callback token and owner identity (`SEC-002`), transitions the record to `APPROVED`, dispatches the message via the authorized API (`FR-COMM-005`), and writes an immutable audit log entry (`SEC-004`).
- **Alternative Path (Rejection):** Owner clicks `[Cancel]`; state transitions to `REJECTED`, and no external API call is made.

### `UC-004` — Systematic Academic Literature Review & Verification (Stage 2)
- **Actor:** Primary User, Academic Intelligence Module
- **Preconditions:** Network access to scholarly APIs (`INT-005`) is available.
- **Main Success Scenario:**
  1. User requests a literature synthesis on a specific research question.
  2. Aira formulates structured search queries and calls arXiv, OpenAlex, and PubMed APIs (`FR-ACAD-001`).
  3. Aira filters retrieved papers by relevance, publication year, and citation metadata, verifying every DOI/arXiv ID.
  4. Aira generates a comparative synthesis matrix (`FR-ACAD-002`) and stores the bibliography in the local knowledge base (`FR-PERS-002`).

### `UC-005` — MT5 Risk Monitoring, Position Sizing & Drawdown Alerting (Stage 3)
- **Actor:** Financial Intelligence Subagent, MT5 Read-Only Bridge, Primary User
- **Preconditions:** MT5 terminal and read-only telemetry bridge (`INT-006`) are active.
- **Main Success Scenario:**
  1. Background monitor polls MT5 account equity, margin, and open positions every $N$ seconds (`FR-FIN-001`).
  2. Monitor detects that floating drawdown has reached `2.1%`, exceeding the `2.0%` warning threshold (`FR-FIN-002`), or detects an open trade without a Stop Loss.
  3. Deterministic risk module computes exact exposure figures (`NFR-002`).
  4. Aira immediately sends a `HIGH` priority alert to Telegram detailing the breached threshold, open positions, and required risk-reduction metrics.

---

## 5. System Requirements (`SYS`)

#### `SYS-001` — Local-First Runtime Environment
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The core application runtime shall execute natively on macOS and Linux workstations (Python 3.11+ or TypeScript/Node.js LTS runtime) with deterministic dependency lockfiles and zero mandatory cloud hosting dependencies in Stage 1.
- **Rationale:** Supports the Stage 1 Local AI Prototype goal and keeps infrastructure costs and complexity minimal during foundational development.
- **Acceptance Criteria:**
  1. Application starts cleanly from a single CLI entrypoint on macOS (`darwin`) and Linux (`linux`).
  2. All runtime configuration is validated at startup using strict schema validation (e.g., Pydantic or Zod); missing required variables fail fast with clear diagnostic messages.
- **Dependencies:** None

#### `SYS-002` — Structured Local Persistence Layer
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall utilize an embedded or local relational database (SQLite with WAL mode enabled in Stage 1; PostgreSQL with `pgvector` in Stage 2+) with versioned schema migrations to store tasks, notes, session history, HITL state machines, and audit logs.
- **Rationale:** Ensures ACID transaction integrity, zero external database cost in Stage 1, and a clean migration path to vector-enabled PostgreSQL in Stage 2.
- **Acceptance Criteria:**
  1. Database schema migrations apply cleanly from an empty state and are idempotent.
  2. Concurrent read/write operations from interactive chat and background tasks complete without database lock errors.
- **Dependencies:** `SYS-001`

#### `SYS-003` — Hybrid Cloud-Local Execution & Encrypted Bridge (Stage 4)
- **Priority:** `P3`
- **Scope:** `Future (Stage 4)`
- **Description:** The system shall support deploying the core orchestration and webhook control plane to a high-availability cloud environment while maintaining an authenticated, mutual-TLS (mTLS) or WireGuard/Tailscale encrypted bridge to local/VPS execution nodes (e.g., local file system or Windows VPS running MT5).
- **Rationale:** Enables 99.9% uptime for webhooks and scheduled briefings while preserving access to local-only resources and Windows-specific MT5 terminals.
- **Acceptance Criteria:**
  1. Cloud control plane communicates with remote/local bridge nodes exclusively over mutually authenticated encrypted channels.
  2. Temporary disconnection of a local bridge queues non-urgent tasks and triggers a health notification without crashing the cloud control plane.
- **Dependencies:** `SYS-001`, `SYS-002`, `SEC-001`

#### `SYS-004` — Web Executive Dashboard (Stage 4)
- **Priority:** `P3`
- **Scope:** `Future (Stage 4)`
- **Description:** The system shall provide a secure, authenticated web interface for inspecting long-term memory graphs, managing pending HITL approvals, viewing multi-agent execution traces, and visualizing MT5 trading analytics.
- **Rationale:** Complements the conversational Telegram interface with high-density visual dashboards for complex data review.
- **Acceptance Criteria:**
  1. Dashboard requires strong authentication and renders pending HITL gates, memory records, audit logs, and financial charts accurately across desktop and mobile viewports.
- **Dependencies:** `SYS-003`, `SEC-002`

---

## 6. Integration Requirements (`INT`)

#### `INT-001` — Multi-Provider LLM & Embedding Gateway
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall integrate with configurable LLM inference and embedding APIs (supporting primary cloud providers such as Google Gemini, OpenAI, or Anthropic, as well as local OpenAI-compatible endpoints such as Ollama) with configurable timeouts, retry logic, and token accounting.
- **Rationale:** Prevents vendor lock-in, tracks API cost/usage, and enables local inference for privacy-sensitive tasks.
- **Acceptance Criteria:**
  1. Adapter supports structured output / tool-calling schemas, streaming/non-streaming responses, and per-request token usage logging.
  2. Transient HTTP `429` or `5xx` errors trigger exponential backoff or fallback model routing without losing user state.
- **Dependencies:** `SYS-001`, `SEC-001`

#### `INT-002` — Telegram Bot API Adapter
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall integrate with the official Telegram Bot API supporting long-polling (for local NAT-friendly Stage 1 execution) and HTTPS webhooks (for Stage 2/4 server deployments), including inline keyboard callbacks for HITL approvals.
- **Rationale:** Provides the primary mobile and desktop user interface for Aira across all stages.
- **Acceptance Criteria:**
  1. Supports text messages, Markdown formatting, file/document uploads, and inline callback buttons (`callback_query`).
  2. Automatically splits or paginates responses exceeding Telegram's 4,096-character message limit without breaking Markdown syntax.
- **Dependencies:** `SYS-001`, `SEC-001`

#### `INT-003` — WhatsApp Business Platform (Cloud API) Adapter
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall integrate exclusively with the official Meta WhatsApp Business Cloud API via verified HTTPS webhooks and Graph API endpoints.
- **Rationale:** Complies with platform Terms of Service and prevents phone number bans caused by unofficial browser-scraping libraries.
- **Acceptance Criteria:**
  1. Webhook endpoint validates Meta verification challenges and `X-Hub-Signature-256` payload signatures.
  2. Outbound API calls respect WhatsApp 24-hour customer service window rules and approved message templates.
- **Dependencies:** `SYS-001`, `SEC-001`, `PERM-002`

#### `INT-004` — Canva MCP / Connect API Integration
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall integrate with Canva via the official Canva MCP Server or Canva Connect REST API using OAuth 2.0 with PKCE.
- **Rationale:** Enables programmatic template discovery, design autofill, and asset export for the Business Operations domain.
- **Acceptance Criteria:**
  1. OAuth 2.0 access and refresh tokens are stored encrypted and refreshed automatically prior to expiration.
  2. Design creation and export operations return valid Canva design URLs or local exported files.
- **Dependencies:** `FR-AUTO-001`, `SEC-001`

#### `INT-005` — Scholarly & Research Database APIs
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)`
- **Description:** The system shall integrate with public scholarly REST APIs including arXiv, OpenAlex, PubMed (NCBI E-utilities), Europe PMC, and Crossref, enforcing polite rate-limiting headers and response caching.
- **Rationale:** Grounds the Academic Intelligence domain in verifiable bibliographic data.
- **Acceptance Criteria:**
  1. API client respects provider rate limits (e.g., NCBI E-utilities requests/sec limits and OpenAlex polite pool `mailto` header).
  2. Retrieved paper metadata is normalized into a unified `ScholarlyWork` schema with verified DOI/arXiv/PMID fields.
- **Dependencies:** `SYS-001`, `SYS-002`

#### `INT-006` — MetaTrader 5 (MT5) Telemetry & Data Bridge
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The system shall integrate with MetaTrader 5 via a dedicated, authenticated bridge service (running alongside the MT5 terminal on Windows/VPS or Wine) that exposes read-only endpoints for account info, open positions, historical deals, and OHLCV market data.
- **Rationale:** Decouples the cross-platform Aira core runtime (macOS/Linux) from the Windows-native `MetaTrader5` terminal dependency while enforcing read-only safety at the bridge boundary.
- **Acceptance Criteria:**
  1. Bridge exposes strictly read-only endpoints (`GET /account`, `GET /positions`, `GET /orders`, `GET /history/deals`, `GET /market/rates`) authenticated via API key / mTLS.
  2. Any attempt to invoke trade execution (`order_send`) on the read-only telemetry bridge is rejected at the bridge interface level (`HTTP 403 Forbidden`).
- **Dependencies:** `SYS-001`, `SEC-001`, `PERM-004`

---

## 7. Security Requirements (`SEC`)

#### `SEC-001` — Secret Isolation & Credential Vaulting
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** All sensitive credentials (LLM API keys, Telegram bot tokens, WhatsApp secrets, Canva OAuth tokens, MT5 bridge keys, database passwords) shall be loaded strictly from environment variables or an encrypted secret store, never committed to Git, never included in LLM prompts, and automatically redacted from logs and user-facing outputs.
- **Rationale:** Prevents catastrophic credential leakage via source control, logs, or prompt exfiltration.
- **Acceptance Criteria:**
  1. Repository includes `.gitignore` rules blocking `.env`, `*.pem`, `*.key`, and local database files, plus a safe `.env.example` template with placeholder values only.
  2. Log sanitizer middleware scrubs any string matching configured secret values or common API key regex patterns (`REDACTED_SECRET`) before writing to disk or stdout.
  3. Tool execution layer strips environment secrets before passing tool outputs to the LLM context window.
- **Dependencies:** `SYS-001`

#### `SEC-002` — Strict Owner Authentication & Channel Whitelisting
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** Every inbound command channel (Telegram, CLI, Webhook, Web Dashboard) shall verify caller identity against an explicit owner whitelist and cryptographic signature before invoking Aira Core or any tool.
- **Rationale:** Ensures no external party who discovers the Telegram bot username or webhook URL can interact with Aira or access personal data.
- **Acceptance Criteria:**
  1. Telegram adapter checks `message.from.id` and `callback_query.from.id` against `AUTHORIZED_TELEGRAM_USER_IDS` prior to any processing.
  2. Unauthorized requests receive zero internal system information and trigger an immediate security audit log entry.
- **Dependencies:** `INT-002`

#### `SEC-003` — Prompt Injection & Untrusted Content Isolation
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** All external data ingested by Aira (web pages, academic abstracts, inbound WhatsApp messages, third-party documents) shall be encapsulated within explicit untrusted-data delimiters and processed with privilege-separation rules so untrusted text cannot trigger high-privilege tool calls.
- **Rationale:** Mitigates indirect prompt injection attacks where malicious instructions hidden inside an external message or document attempt to hijack Aira's tools.
- **Acceptance Criteria:**
  1. External text payloads are wrapped in structured XML/JSON data tags with explicit system instructions treating their contents strictly as passive data.
  2. During turns that process untrusted external inputs, automatic invocation of `EXTERNAL_MUTATION` or `CRITICAL_RESTRICTED` tools without an explicit HITL gate is blocked at the Policy Engine level.
- **Dependencies:** `FR-CORE-003`, `PERM-001`

#### `SEC-004` — Immutable Append-Only Audit Log
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The system shall maintain an append-only audit log recording all tool invocations, permission evaluations, HITL approval requests/decisions, authentication failures, and configuration changes.
- **Rationale:** Provides complete forensic traceability for all autonomous and semi-autonomous system actions.
- **Acceptance Criteria:**
  1. Application runtime database user/service for normal operations has `INSERT` and `SELECT` privileges on the audit table, without `UPDATE` or `DELETE` routines exposed to the LLM or tool bus.
  2. Each audit record captures: `audit_id`, `timestamp`, `trace_id`, `actor` (`user`, `core`, `subagent_name`, `scheduler`), `action_type`, `tool_name`, `permission_tier`, `approval_status`, and `outcome`.
- **Dependencies:** `SYS-002`, `NFR-004`

---

## 8. Permission & Governance Requirements (`PERM`)

#### `PERM-001` — Four-Tier Tool Permission Classification Engine
- **Priority:** `P0`
- **Scope:** `MVP (Stage 1)`
- **Description:** The Policy & Authorization Engine shall classify every registered tool and action into one of four mandatory permission tiers and enforce the corresponding execution policy prior to invocation:
  - **Tier A (`READ_ONLY`):** Local queries, note searches, scholarly API lookups, MT5 read-only telemetry. *Policy: Autonomous execution permitted.*
  - **Tier B (`LOCAL_WRITE_REVERSIBLE`):** Creating/updating notes, adding tasks, staging drafts, saving backtest reports. *Policy: Autonomous execution permitted with audit log and undo/versioning.*
  - **Tier C (`CONSEQUENTIAL_EXTERNAL_OR_DESTRUCTIVE`):** Sending external WhatsApp/email messages, publishing social media/Canva assets, deleting persistent records, modifying system schedules. *Policy: Mandatory Human-in-the-Loop (HITL) approval gate required before execution.*
  - **Tier D (`PROHIBITED_GUARDRAIL`):** Unattended live trading execution without risk caps, credential exfiltration, unauthorized scraping, modifying core security policies. *Policy: Hard-blocked unconditionally.*
- **Rationale:** Implements the "Friction Proportional to Risk" principle in deterministic code rather than relying on LLM self-restraint.
- **Acceptance Criteria:**
  1. Any tool registered without an explicit permission tier defaults to `Tier C` (requires HITL approval).
  2. Attempting to invoke a `Tier C` tool without a valid, unexpired `approval_token` halts tool execution and transitions the workflow to `AWAITING_USER_APPROVAL`.
  3. Attempting to invoke a `Tier D` action raises an immediate `PolicyViolationError` and logs a critical security event.
- **Dependencies:** `FR-AUTO-001`, `SEC-004`

#### `PERM-002` — Stateful Human-in-the-Loop (HITL) Approval Workflow
- **Priority:** `P1`
- **Scope:** `Future (Stage 2)` (CLI confirmation in Stage 1 MVP; Interactive Telegram state machine in Stage 2)
- **Description:** For all `Tier C` actions, the system shall persist the proposed action payload, present a human-readable summary of the exact side effect to the user, and require explicit confirmation (`Approve`, `Reject`, or `Modify`) with a configurable expiration TTL before executing.
- **Rationale:** Ensures the human owner retains final authority over every external communication, public publication, or destructive data operation.
- **Acceptance Criteria:**
  1. Approval request clearly displays: Target Tool, Target Recipient/Resource, Exact Payload/Diff, and Expiration Time.
  2. Approval tokens are single-use, bound to the exact SHA-256 hash of the action payload (modifying the payload invalidates a prior approval), and expire automatically after a configurable TTL (default 24 hours).
- **Dependencies:** `PERM-001`, `FR-COMM-001`, `SYS-002`

#### `PERM-003` — Subagent Least-Privilege Sandbox & Budget Quotas
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** Each specialized domain subagent shall be restricted by a declarative permission manifest defining its allowed tools, accessible memory namespaces, maximum execution duration, and maximum token/API cost budget per task.
- **Rationale:** Prevents a compromised or malfunctioning subagent (e.g., Academic Agent) from accessing unrelated sensitive tools (e.g., MT5 Financial telemetry or WhatsApp outbound messaging) or exhausting API quotas.
- **Acceptance Criteria:**
  1. Academic Research Subagent cannot access Financial (`FR-FIN-*`) or WhatsApp (`INT-003`) tools; cross-domain access attempts are blocked by the Policy Engine.
  2. Subagent tasks exceeding their configured step limit (default 15 steps) or token budget terminate gracefully and report partial progress to the Core Supervisor.
- **Dependencies:** `FR-AUTO-003`, `PERM-001`

#### `PERM-004` — Financial Domain Hard Isolation Gate
- **Priority:** `P2`
- **Scope:** `Future (Stage 3)`
- **Description:** The Financial Intelligence domain shall operate under a strict read-only hardware/software boundary (`Tier A` telemetry and `Tier B` local analytics) by default; autonomous, unattended live order placement, modification, or fund transfer is prohibited (`Tier D`).
- **Rationale:** Protects financial capital from probabilistic model hallucinations, API anomalies, or flash-crash market conditions.
- **Acceptance Criteria:**
  1. Default MT5 integration configuration does not load or expose order-execution functions (`order_send`, `order_check` for live execution) to any LLM tool registry.
  2. If future semi-automated trade staging is ever introduced, it must require per-trade cryptographic HITL approval (`PERM-002`) plus deterministic pre-trade risk-cap validation (`FR-FIN-005`).
- **Dependencies:** `INT-006`, `PERM-001`

---

## 9. System-Wide Acceptance Criteria & Release Gates

Before any evolutionary stage is declared complete and ready to advance to the next stage, the system must pass the following release-gate acceptance criteria:

| Gate ID | Stage Target | Verification Category | Mandatory Pass Criteria |
| :--- | :--- | :--- | :--- |
| **`GATE-MVP-01`** | Stage 1 (MVP) | Persona & Epistemic Rigor | Passes a 20-prompt adversarial evaluation suite testing anti-sycophancy, assumption challenging, uncertainty disclosure, and non-sentience compliance (`FR-CORE-001`, `FR-CORE-002`). |
| **`GATE-MVP-02`** | Stage 1 (MVP) | Security & Access Control | 100% of unauthorized Telegram user IDs rejected; zero secrets present in Git history, LLM payloads, or log files (`SEC-001`, `SEC-002`). |
| **`GATE-MVP-03`** | Stage 1 (MVP) | Core Loop & Persistence | Tasks, notes, session context, and audit logs persist cleanly across restarts; `/cancel` halts active execution within 3 seconds (`FR-PERS-001`, `FR-PERS-002`, `FR-AUTO-004`, `SYS-002`). |
| **`GATE-STG2-01`** | Stage 2 | Proactive Continuity | Morning and evening Daily Briefings execute automatically on schedule with zero duplicate deliveries and accurate recall of multi-week semantic/episodic memories (`FR-PERS-003`, `FR-COMM-002`, `FR-AUTO-002`). |
| **`GATE-STG2-02`** | Stage 2 | HITL & Citation Integrity | 100% of `Tier C` actions halt for interactive Telegram approval (`PERM-002`); 100% of academic literature outputs contain verified DOIs/arXiv IDs with zero fabricated citations (`FR-ACAD-001`). |
| **`GATE-STG3-01`** | Stage 3 | Multi-Agent & Quantitative Accuracy | Domain subagents respect least-privilege tool boundaries (`PERM-003`); MT5 telemetry, risk alerts, and backtest metrics match deterministic benchmark calculations to 4 decimal places (`FR-FIN-001`–`005`, `NFR-002`). |
| **`GATE-STG4-01`** | Stage 4 | Cloud Resilience | Hybrid cloud-local bridge maintains encrypted connectivity, recovers automatically from node restarts, and sustains $\ge 99.9\%$ availability for core messaging and monitoring loops (`SYS-003`, `SYS-004`). |

---

## 10. MVP Scope vs. Future Scope Matrix

To prevent scope creep during initial engineering, the following matrix establishes the strict boundary between **MVP Scope (Stage 1)** and **Future Scope (Stages 2–4)**.

### 10.1 Scope Allocation Summary

| Capability / Module | MVP Scope (Stage 1 — `P0`) | Stage 2 Scope (`P1`) | Stage 3 Scope (`P2`) | Stage 4 Scope (`P3`) |
| :--- | :--- | :--- | :--- | :--- |
| **Execution Environment** | Local workstation (CLI + polling daemon) | Always-on local / home server | Multi-agent local/server runtime + VPS bridge | Hybrid Cloud Control Plane + Encrypted Local Bridge |
| **User Interfaces** | Local CLI + Owner-whitelisted Telegram Bot | Interactive Telegram inline approval buttons | Multi-channel triage (Telegram + WhatsApp API) | Web Executive Dashboard + Mobile/Telegram |
| **Persona & Reasoning** | Critical-thinking Aira persona, anti-sycophancy, uncertainty flags | Structured Decision Support & Devil's Advocate matrices | Socratic Tutoring & domain-specialized agent prompts | Multi-model dynamic routing & fallback |
| **Memory Architecture** | Session history + SQLite relational storage (Tasks & Notes) | Hierarchical Memory (Working, Episodic, Semantic Vector, Procedural) | Cross-domain knowledge graph synthesis | Distributed encrypted sync & visual memory inspector |
| **Proactivity & Automation** | Manual triggers + basic reminders + global `/cancel` kill-switch | Cron background scheduler + Automated Morning/Evening Briefings | Event-driven webhooks + Multi-agent DAG workflows + MCP Bus | Distributed task queues + Policy-as-Code observability |
| **Communication Domain** | Telegram owner chat | Message drafting + Quiet hours + Urgency filtering | Official WhatsApp Business Cloud API integration | Omni-channel unified inbox on Web Dashboard |
| **Business Operations** | Basic task/note tagging for business | Project & milestone tracking + SOP/Document generation | Social media editorial calendars + Canva API/MCP automation | Automated brand asset pipelines & analytics dashboard |
| **Academic Intelligence** | Local note/Markdown ingestion | Live arXiv/OpenAlex/PubMed search + DOI verification + Lit Review tables | Scholarship/grant deadline & document tracker + Socratic learning | Automated research alert subscriptions (new paper triggers) |
| **Financial Intelligence** | Out of MVP scope (specification only) | Out of Stage 2 scope | MT5 read-only telemetry bridge, risk alerts, trade analytics, backtesting, position sizing | Real-time web financial dashboard & portfolio correlation engine |
| **Security & Governance** | `.env` secret isolation, log redaction, owner ID whitelist, 4-tier policy engine, append-only audit log | Payload-hashed interactive Telegram HITL approval tokens + automated daily backups | Subagent least-privilege sandboxes + token/step quotas + MT5 read-only bridge lock | mTLS zero-trust cloud-local tunnels + full telemetry observability |

### 10.2 Explicit MVP Non-Goals (Out of Scope for Stage 1)

To guarantee a fast, stable, and verifiable **Stage 1 MVP**, the following items must **not** be built during the MVP phase:

1. **No Multi-Agent Subagents in Stage 1:** Stage 1 uses a single, clean Aira Core executive loop. Subagent decomposition is deferred to Stage 3 (`FR-AUTO-003`).
2. **No Live MT5 Terminal Connection in Stage 1:** Financial Intelligence modules (`FR-FIN-001` through `FR-FIN-005`) require a dedicated bridge and deterministic quantitative engine scheduled for Stage 3.
3. **No WhatsApp or Canva Integrations in Stage 1:** Stage 1 focuses strictly on CLI and Telegram (`FR-COMM-001`) to validate core state, memory, and safety before adding OAuth2/Cloud API webhooks.
4. **No Custom Web Frontend in Stage 1:** The Web Executive Dashboard (`SYS-004`) is deferred to Stage 4; CLI and Telegram serve as the complete UI for Stages 1–3.
5. **No Autonomous Live Trading Execution (All Stages):** Unsupervised live order execution remains permanently restricted (`PERM-004`).

