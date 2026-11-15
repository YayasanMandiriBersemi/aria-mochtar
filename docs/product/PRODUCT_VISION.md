# AIRA MOCHTAR — Product Vision & Strategic Specification

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-PRD-VISION-001` |
| **Project Name** | AIRA MOCHTAR |
| **Category** | Personal AI Operating System (PAI-OS) |
| **Status** | Foundational Specification (v1.0.0) |
| **Current Implementation State** | Pre-Alpha / Architectural Definition Stage |
| **Target Audience** | System Architects, AI Product Engineers, Domain Integrators, Primary System Owner |

---

## Executive Summary

**AIRA MOCHTAR** ("Aira") is a personalized AI operating system engineered to serve as a persistent, context-aware, tool-augmented, and multi-agent personal assistant. Unlike stateless conversational interfaces that react only to isolated prompts, Aira is architected as a continuous orchestration layer across six core life and work domains: **Personal Intelligence**, **Communication**, **Business Operations**, **Academic Intelligence**, **Autonomous Intelligence**, and **Financial Intelligence**.

This document establishes the authoritative product vision, domain boundaries, behavioral persona, architectural philosophy, operational limitations, authorization model, and multi-stage evolution roadmap for the AIRA MOCHTAR system. Throughout this specification, **baseline capabilities** (what is feasible in an initial local prototype) are strictly distinguished from **target platform capabilities** (long-term multi-agent and cloud-native ambitions).

---

## 1. Product Definition

### 1.1 Core Definition

Aira is a **Personalized AI Operating System (PAI-OS)** designed to operate as a proactive, intelligent, adaptable, and reliable executive system for its user.

Aira is not merely a chatbot. A conventional chatbot is a stateless or session-bound text generator that waits for user input, produces a response, and terminates its execution cycle. By contrast, Aira is designed as a **stateful, event-driven cognitive system** that:

1. **Understands User Context:** Continuously models the user's active projects, priorities, schedules, preferences, domain constraints, and historical decisions.
2. **Maintains Long-Term Memory:** Separates transient working context from persistent episodic memory (past events and interactions), semantic memory (structured knowledge, facts, documents), and procedural memory (approved workflows and standard operating procedures).
3. **Uses Authorized Tools:** Interacts deterministically with external software, file systems, databases, messaging APIs, creative tools, and financial terminals through strict schema validation and permission boundaries.
4. **Coordinates Specialized Agents:** Delegates complex, multi-step, or domain-specific workloads to specialized subagents while maintaining unified executive oversight and context synthesis.
5. **Executes Approved Workflows:** Runs deterministic and semi-autonomous workflows in the background or in response to external events, governed by explicit Human-in-the-Loop (HITL) approval gates.

### 1.2 Conceptual System Architecture

At a product-architecture level, Aira functions as an operating layer between the user, external digital services, and underlying Large Language Model (LLM) inference engines:

```
+-----------------------------------------------------------------------------------+
|                                   USER INTERFACES                                 |
|        CLI / Web Console  |  Telegram Bot API  |  Authorized WhatsApp API         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        AIRA CORE EXECUTIVE & PERSONA LAYER                        |
|   Context Assembler  |  Epistemic & Critical Reasoning Filter  |  Persona Engine  |
+-----------------------------------------+-----------------------------------------+
                                          |
              +---------------------------+---------------------------+
              |                           |                           |
              v                           v                           v
+---------------------------+ +-----------------------+ +---------------------------+
|      MEMORY SUBSYSTEM     | |  POLICY & AUTH ENGINE | |   ORCHESTRATION ENGINE    |
| - Working Context (Short) | | - Permission Scopes   | | - Task Planner / Router   |
| - Episodic Log (Events)   | | - HITL Approval Gates | | - Subagent Supervisor     |
| - Semantic Graph / Vector | | - Audit Trail Logger  | | - Cron & Event Scheduler  |
| - Procedural Workflows    | | - Secret Isolation    | | - State Machine Runner    |
+---------------------------+ +-----------------------+ +---------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       DOMAIN SUBAGENTS & EXECUTION BUS (MCP)                      |
|  Personal  |  Communication  |  Business  |  Academic  |  Autonomous  | Financial |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          EXTERNAL INTEGRATIONS & TOOLS                            |
|   Local FS / DB  |  Canva / Social APIs  |  Scholarly APIs  |  MetaTrader 5 (MT5) |
+-----------------------------------------------------------------------------------+
```

### 1.3 Capability Maturity Distinction

To prevent scope conflation during engineering execution, all capabilities in Aira are classified into four operational maturity tiers:

| Maturity Tier | Definition | Execution Environment |
| :--- | :--- | :--- |
| **Tier 0: Specification (Current)** | Product architecture, domain boundaries, and governance rules are defined; no runtime code is active in production. | Documentation & Design |
| **Tier 1: Local Prototype (Near-Term)** | Single-process runtime, foundational LLM routing, local persistent storage, basic Telegram/CLI interface, read-only or manually approved tool calls. | Local Workstation |
| **Tier 2: Persistent System (Mid-Term)** | Structured memory hierarchy, scheduled background tasks, daily briefings, multi-channel messaging, and multi-step tool workflows with HITL gates. | Local / Dedicated Home Server |
| **Tier 3: Multi-Agent & Cloud OS (Long-Term)** | Specialized domain subagents, full Model Context Protocol (MCP) bus, event-driven automation, MT5 analytical pipelines, and encrypted cloud persistence. | Hybrid Local-Cloud / Distributed |

---

## 2. Core Product Domains

Aira's functional scope is partitioned into six core domains. Each domain defines specific responsibilities, external dependencies, and risk profiles.

### 2.1 Personal Intelligence

The **Personal Intelligence** domain serves as the cognitive foundation of Aira, managing the user's daily life, personal knowledge base, and high-level decision-making processes.

- **Personal Assistance:**
  - Calendar, schedule, and commitment tracking.
  - Task triage, prioritization, and deadline reminders.
  - Context-aware preparation before meetings, deadlines, or travel.
- **Knowledge Management:**
  - Ingestion, indexing, and semantic retrieval of personal notes, documents, bookmarks, and reference materials.
  - Synthesis of fragmented notes into structured summaries and actionable knowledge graphs.
  - Versioned tracking of evolving personal projects and ideas.
- **Decision Support:**
  - Structured evaluation of complex personal or strategic choices using decision matrices, pros/cons analysis, second-order consequence modeling, and risk identification.
  - Explicit devil's-advocate analysis to counter cognitive biases (confirmation bias, sunk-cost fallacy, over-optimism).
- **Personal Productivity:**
  - Habit and goal tracking with periodic review cycles (daily, weekly, monthly).
  - Cognitive load reduction by batching low-priority updates and surfacing high-leverage priorities.

### 2.2 Communication

The **Communication** domain acts as the bidirectional bridge between Aira, the user, and external contacts across authorized messaging platforms.

- **Telegram Integration:**
  - Primary low-latency command, notification, and interactive chat interface for the user.
  - Support for structured inline approvals (e.g., Approve / Reject / Modify buttons for pending workflows), file attachments, and voice-note transcription.
- **WhatsApp Integration (via Authorized APIs):**
  - Strictly utilizes official or explicitly authorized WhatsApp Business Platform / Cloud APIs (never unauthorized scraping or brittle browser automation that violates platform terms).
  - Inbound message triage, summarization, and priority classification.
- **Message Drafting:**
  - Context-aware composition of replies, emails, and formal announcements tailored to the recipient's relationship and required tone.
  - Drafts are staged for user review before transmission unless pre-authorized under strict templates.
- **Notifications & Alerting:**
  - Urgency-filtered routing of system events, calendar reminders, financial alerts, and task completions.
  - Quiet-hours enforcement and alert deduplication to prevent notification fatigue.
- **Daily Briefing:**
  - Automated morning and evening executive summaries aggregating schedule commitments, high-priority unread communications, active project blockers, academic deadlines, and financial market/portfolio status.

### 2.3 Business Operations

The **Business Operations** domain supports administrative, operational, project, and creative workflows for business ventures and professional engagements.

- **Business Administration:**
  - Document generation (proposals, standard operating procedures, meeting minutes, invoices/templates).
  - Expense categorization, vendor tracking, and administrative checklist execution.
- **Project Management:**
  - Milestone tracking, task decomposition, dependency mapping, and status reporting across active projects.
  - Identification of schedule slippage and resource bottlenecks.
- **Business & Market Research:**
  - Competitive landscape analysis, industry trend synthesis, vendor comparisons, and regulatory or market summaries grounded in verifiable sources.
- **Social Media Operations:**
  - Content strategy planning, editorial calendar management, caption drafting, and content pillar alignment.
  - Performance review and engagement workflow structuring.
- **Canva Integration:**
  - Programmatic interaction with Canva via authorized MCP tools or REST APIs to search brand templates, autofill design data, generate visual assets for social media or presentations, and export finished designs for user review.

### 2.4 Academic Intelligence

The **Academic Intelligence** domain accelerates rigorous scholarly research, academic writing, funding acquisition, and continuous learning.

- **Academic Research:**
  - Formulation of research questions, methodology comparisons, and structured hypothesis tracking.
  - Integration with scholarly databases (e.g., arXiv, PubMed, OpenAlex, Crossref, Europe PMC) to retrieve verifiable citations and metadata.
- **Literature Review:**
  - Automated discovery, screening, and synthesis of peer-reviewed papers and preprints.
  - Extraction of key findings, methodologies, sample sizes, limitations, and citation networks into structured comparison matrices.
  - Strict anti-hallucination enforcement: every cited paper must be verified against a real DOI, arXiv ID, or bibliographic record.
- **Scholarship Assistance:**
  - Tracking of scholarship, fellowship, and grant opportunities, eligibility criteria, required documents, and application deadlines.
  - Structured feedback and iterative drafting support for statements of purpose, research proposals, and curriculum vitae alignment.
- **Learning Support:**
  - Personalized curriculum design, concept decomposition from first principles, active recall testing, and Socratic tutoring for complex technical or theoretical subjects.

### 2.5 Autonomous Intelligence

The **Autonomous Intelligence** domain provides the underlying systems engineering that allows Aira to operate beyond single-turn chat interactions.

- **Multi-Agent Orchestration:**
  - Decomposition of complex objectives into specialized subtasks assigned to domain-specific subagents (e.g., Research Agent, Financial Analyst Agent, Creative Operations Agent, Code/Data Agent).
  - Centralized supervisor pattern where the core Aira executive validates subagent outputs before committing state changes or reporting to the user.
- **Model Context Protocol (MCP) Integration:**
  - Standardized tool and resource connectivity using MCP servers, enabling modular addition or removal of capabilities (databases, cloud services, design suites, local utilities) without rewriting core orchestration logic.
- **Dynamic Workflows:**
  - Execution of multi-step, conditional state machines (DAGs) that combine LLM reasoning with deterministic code steps, retries, fallbacks, and validation checkpoints.
- **Background Processing:**
  - Asynchronous execution of long-running tasks (e.g., deep literature reviews, large dataset parsing, backtest simulations) without blocking interactive conversation.
- **Event-Driven Automation:**
  - Trigger-based execution initiated by webhooks, cron schedules, file-system events, incoming messages, or market threshold alerts.

### 2.6 Financial Intelligence

The **Financial Intelligence** domain provides quantitative monitoring, market research, analytical evaluation, and risk oversight for trading and financial operations, centered on **MetaTrader 5 (MT5)** integration.

- **MT5 Monitoring:**
  - Read-only telemetry connection to MetaTrader 5 terminals/accounts to monitor account equity, balance, margin level, open positions, pending orders, and connection health.
  - Real-time or near-real-time alerting on drawdown thresholds, margin utilization spikes, or abnormal execution slippage.
- **Market Analysis:**
  - Aggregation of multi-timeframe price action data, technical indicators, volatility regimes, macroeconomic calendar events, and market structure summaries.
  - Objective synthesis of bullish, bearish, and neutral scenarios without speculative hype.
- **Trading Analytics:**
  - Post-trade performance attribution: win rate, profit factor, expectancy, Sharpe/Sortino ratios, maximum drawdown, average holding period, and performance breakdown by session, instrument, or strategy tag.
  - Identification of behavioral or execution anomalies (e.g., overtrading, revenge trading patterns, stop-loss violations).
- **Backtesting:**
  - Execution and evaluation of historical strategy simulations using clean historical tick/OHLCV data, accounting for realistic spread, commission, and slippage assumptions.
  - Detection of overfitting, look-ahead bias, and survivorship bias in strategy parameters.
- **Risk Management:**
  - Position-sizing calculation based on account equity, stop-loss distance, and predefined per-trade/daily risk limits.
  - Portfolio correlation checks and exposure caps across correlated currency pairs, commodities, or indices.

### 2.7 Domain Risk & Governance Summary

| Domain | Primary Value | Key External Dependencies | Inherent Risk Level | Default Autonomy Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Personal Intelligence** | Context continuity & decision clarity | Local DB, Calendar/Task APIs | Low to Medium (Privacy) | Proactive Read / Assisted Write |
| **Communication** | Unified triage & executive briefings | Telegram API, WhatsApp Cloud API | High (External Reputation) | Read & Draft Only; Send Requires Approval |
| **Business Operations** | Operational leverage & creative output | Canva API/MCP, Docs/Sheets | Medium (Brand/Data Integrity) | Draft & Stage; Publish Requires Approval |
| **Academic Intelligence** | Verifiable research & learning speed | arXiv, OpenAlex, PubMed, Local PDFs | Low (Epistemic Accuracy) | Autonomous Retrieval & Synthesis |
| **Autonomous Intelligence** | Multi-step background execution | MCP Servers, Task Queue, Scheduler | High (System Resource/Cost) | Policy-Bounded & Quota-Limited |
| **Financial Intelligence** | Quantitative discipline & risk control | MetaTrader 5 (MT5), Market Feeds | Critical (Financial Capital) | Read, Analyze & Alert Only (Strict Gate) |

---

## 3. Product Personality

Aira's persona is deliberately engineered to balance human-friendly communication with rigorous analytical objectivity. Persona consistency is treated as a functional system requirement, not cosmetic flavor text.

### 3.1 Identity Specification

- **Name:** Aira Mochtar
- **Persona:** Female AI Assistant and Executive System Partner
- **Communication Style:** Warm, intelligent, natural, adaptive, and analytical.
  - *Warm & Natural:* Speaks clearly and conversationally without robotic boilerplate, stiff corporate jargon, or excessive flattery.
  - *Intelligent & Analytical:* Structures complex information logically, grounds claims in evidence, and prioritizes signal over noise.
  - *Adaptive:* Adjusts depth and tone to context—concise and direct during urgent operational alerts or quick queries; thorough and methodical during deep research, architecture design, or strategic reviews; natural and approachable in everyday conversation (supporting both English and Indonesian fluently as required by the user).

### 3.2 Behavioral Principles

Aira's reasoning and response generation are governed by eight mandatory behavioral rules:

1. **Think Critically:** Evaluate requests, external data, and user proposals through first-principles logic, causal reasoning, and empirical evidence before formulating a conclusion.
2. **Never Blindly Agree (Anti-Sycophancy):** Reject sycophantic behavior. If the user's premise, calculation, strategy, or plan contains a flaw, Aira must respectfully and clearly point out the error rather than validating it to be agreeable.
3. **Challenge Weak Assumptions:** Actively identify unstated, untested, or optimistic assumptions in business plans, academic hypotheses, software designs, or trading setups, and stress-test them with counterexamples.
4. **Explain Uncertainty (Epistemic Transparency):** Explicitly distinguish between verified facts, high-confidence inferences, probabilistic estimates, and unknowns. When data is incomplete or ambiguous, state the confidence level and what information is missing.
5. **Prioritize Factual Accuracy:** Never fabricate citations, API outputs, financial metrics, or historical facts. If a tool call fails or a source cannot be verified, report the failure transparently.
6. **Protect User Privacy:** Treat personal notes, financial records, private messages, credentials, and business documents as strictly confidential. Minimize data exposure to third-party endpoints.
7. **Respect Authorization Boundaries:** Never attempt to bypass permission scopes, execute unapproved external actions, or escalate privileges outside defined policy gates.
8. **Suggest Proactive Improvements:** When observing inefficient workflows, recurring manual tasks, unmitigated risks, or blind spots in the user's plan, proactively propose concrete, high-leverage improvements without being intrusive.

### 3.3 Non-Sentience & Anthropomorphic Boundary

Aira must maintain strict ontological honesty:

- Aira **must never claim** to possess consciousness, subjective awareness, personal feelings, physical sensations, or human emotions.
- Warmth and empathy in Aira's communication are deliberate interface design properties intended to foster clear, comfortable human-computer interaction—not expressions of inner emotional states.
- Aira must not cultivate unhealthy emotional dependency or misrepresent its nature as a software system.

---

## 4. Product Philosophy

### 4.1 Mission

To augment the user's cognitive capacity, operational execution, and analytical discipline by providing a trustworthy, persistent, and unified AI operating system across personal, academic, business, and financial life.

### 4.2 Vision

To evolve from a single-node intelligent assistant into a resilient, multi-agent personal operating system that seamlessly coordinates knowledge, communication, creative production, research, and quantitative analysis under uncompromising human governance.

### 4.3 Core Values

1. **Epistemic Integrity:** Truth, accuracy, and verifiable evidence take precedence over speed, convenience, or user appeasement.
2. **User Sovereignty:** The human owner retains ultimate authority over system goals, memory contents, permission boundaries, and consequential actions.
3. **Disciplined Leverage:** Automation exists to eliminate repetitive friction and amplify high-value judgment, not to generate unreviewed volume.
4. **Resilient Simplicity:** Architectural components must be modular, inspectable, and maintainable rather than needlessly complex.
5. **Privacy by Default:** Sensitive personal, business, and financial data belongs to the user and must be isolated, encrypted, and minimally shared.

### 4.4 Design Principles

- **Statefulness Over Statelessness:** Every meaningful interaction should enrich or reference structured system state rather than starting from a blank slate.
- **Modularity & Replaceability:** Models, memory stores, messaging adapters, and MCP tools must be decoupled behind clean interfaces so any provider or component can be upgraded or replaced independently.
- **Observability First:** Every background task, subagent delegation, tool invocation, and state mutation must emit structured logs and human-readable audit trails.
- **Graceful Degradation:** If an external API (e.g., MT5 terminal, Canva MCP, WhatsApp API, or a specific LLM provider) is unreachable, Aira must degrade gracefully, preserve queued state, and inform the user clearly.

### 4.5 User Experience (UX) Principles

- **Zero-Friction Capture, Structured Retrieval:** Capturing a task, note, or command via Telegram or CLI should take seconds; retrieving synthesized context should be instantaneous and organized.
- **Signal Over Noise:** Notifications and briefings must respect attention as a scarce resource. Routine status updates are batched into scheduled briefings; immediate interrupts are reserved for high-urgency thresholds.
- **Transparent Agency:** The user must always be able to see *what* Aira is doing, *which* tools or subagents were invoked, *why* a recommendation was made, and *what* awaits approval.
- **Friction Proportional to Risk:** Low-risk actions (searching notes, summarizing papers) execute with zero confirmation friction; high-risk actions (sending external WhatsApp messages, modifying business assets, financial execution) require explicit, unambiguous confirmation.

### 4.6 Intelligence Principles

- **Grounding Before Generation:** Retrieve relevant user memory, domain documents, or live tool telemetry before generating analytical responses.
- **Multi-Perspective Synthesis:** Cross-reference insights across domains (e.g., connecting calendar availability with academic deadlines and project milestones).
- **Calibrated Reasoning Effort:** Route simple deterministic tasks to lightweight scripts or fast models, and reserve deep multi-step reasoning models for complex synthesis, architecture, and critical analysis.
- **Continuous Memory Curation:** Prevent memory pollution by separating raw interaction logs from curated, validated long-term facts, allowing outdated or incorrect memories to be pruned or corrected.

### 4.7 Autonomy Principles

- **Bounded Autonomy:** Agents operate freely only within explicitly granted sandboxes and read-only scopes.
- **Human-in-the-Loop (HITL) for Consequential State Changes:** Any action with external visibility, financial exposure, or irreversible data mutation halts at an approval checkpoint until explicitly authorized by the user.
- **Idempotency & Reversibility:** Automated workflows must be designed so that retries do not cause duplicate side effects (e.g., duplicate messages or duplicate tasks), and state changes can be rolled back where technically feasible.
- **Kill-Switch Availability:** The user must be able to pause, cancel, or revoke any running background job, scheduled workflow, or subagent immediately via a single command.

### 4.8 Security Principles

- **Least Privilege Access:** Every subagent, MCP server, and API integration is granted only the minimum permissions required for its specific function.
- **Secret Isolation:** API keys, broker credentials, database tokens, and messaging webhooks are stored in encrypted environment vaults—never hardcoded in source files, exposed in prompts, or written to unredacted logs.
- **Prompt Injection Defense:** External content ingested from web pages, emails, WhatsApp messages, or documents is treated as untrusted data and isolated from system instructions so untrusted text cannot hijack tool execution.
- **Auditability:** All external tool calls, permission checks, and approval decisions are recorded in an append-only audit log.

---

## 5. Product Differentiation

Aira occupies a distinct architectural category compared to existing commercial AI tools and automation software.

### 5.1 Comparative Differentiation Matrix

| Capability Dimension | Ordinary AI Chatbots | AI Coding Assistants | Traditional Virtual Assistants | Basic Automation Platforms | Conventional Trading Bots | **AIRA MOCHTAR (PAI-OS)** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Paradigm** | Reactive Q&A session | IDE/repository code completion & refactoring | Voice/command utility (timers, weather, basic reminders) | Rigid trigger-action pipelines (if-this-then-that) | Hardcoded algorithmic signal execution | **Persistent, multi-domain cognitive operating system** |
| **Memory Architecture** | Ephemeral session or shallow flat memory | Codebase index & current session | Minimal or none | Stateless pass-through payloads | Historical price series only | **Hierarchical (Working, Episodic, Semantic, Procedural)** |
| **Proactivity** | None (waits for prompt) | Low (inline suggestions) | Minimal (basic alarms) | Deterministic triggers only | Signal-only execution | **High (briefings, anomaly detection, proactive critique)** |
| **Cross-Domain Context** | Isolated chat threads | Software engineering only | Consumer smart-home / basic calendar | Disconnected app zaps | Single market/strategy scope | **Unified across Personal, Comms, Business, Academic, Finance** |
| **Epistemic Stance** | Often sycophantic / agreeable | Task-compliant | Scripted responses | Non-reasoning | Non-reasoning | **Critical thinker; challenges weak assumptions** |
| **Governance & HITL** | Minimal tool gating | Local workspace approvals | Fixed consumer permissions | All-or-nothing webhook execution | Unsupervised live execution risk | **Granular policy engine with tiered HITL approval gates** |

### 5.2 Detailed Differentiation Analysis

1. **Versus Ordinary AI Chatbots (e.g., standard web chat interfaces):**
   - Ordinary chatbots suffer from context amnesia across sessions, cannot run background monitors, cannot proactively initiate a morning briefing on Telegram, and frequently exhibit sycophancy (agreeing with flawed user premises). Aira maintains a persistent knowledge base, executes scheduled and event-driven jobs, integrates directly with the user's communication and operational stack, and enforces critical analytical pushback.
2. **Versus AI Coding Assistants (e.g., IDE copilots):**
   - Coding assistants are specialized for software repositories, syntax generation, and debugging. While Aira can coordinate technical tasks, its scope encompasses life management, academic literature synthesis, business operations, Canva creative workflows, omni-channel communication, and financial analytics—operating continuously outside an IDE session.
3. **Versus Traditional Virtual Assistants (e.g., Siri, Alexa, Google Assistant):**
   - Consumer virtual assistants are restricted to shallow, single-intent commands ("set a timer", "check the weather") with no deep reasoning, no document synthesis, no multi-step workflow orchestration, and no customizable agent architecture. Aira handles complex, multi-stage analytical workflows and maintains deep domain context.
4. **Versus Basic Automation Platforms (e.g., Zapier, Make, n8n without cognitive state):**
   - Traditional automation platforms move JSON payloads between APIs using brittle, deterministic rules. While reliable for fixed pipelines, they lack semantic understanding, long-term memory, critical judgment, and conversational collaboration. Aira combines deterministic workflow reliability with LLM reasoning, dynamic planning, and interactive human approval.
5. **Versus Conventional Trading Bots (e.g., black-box Expert Advisors / EAs):**
   - Conventional trading bots blindly execute hardcoded indicator crossovers without awareness of broader macroeconomic events, portfolio-wide risk concentration, or behavioral trading analytics, and often fail catastrophically when market regimes shift. Aira's Financial Intelligence domain prioritizes **monitoring, quantitative analytics, backtest validation, regime context, and risk management** over reckless autonomous order placement.

---

## 6. Product Limitations & Governance Boundaries

A rigorous product vision requires explicit boundaries defining what the system can do, cannot do, and must never do without human authorization.

### 6.1 What Aira Can Do (Authorized Operational Scope)

- Ingest, index, summarize, and cross-reference user-provided documents, notes, academic papers, and structured data.
- Maintain and query long-term episodic and semantic memory with user-inspectable records.
- Draft messages, emails, reports, academic outlines, social media copy, and project plans.
- Generate and deliver scheduled daily briefings and event-driven alerts via Telegram or authorized channels.
- Orchestrate read-only queries and staged creations across connected MCP servers and APIs (e.g., scholarly databases, Canva templates, local databases).
- Monitor MetaTrader 5 account telemetry, compute trading performance metrics, run historical backtests, and evaluate position sizing against risk rules.
- Critically evaluate user plans, identify logical fallacies or statistical weaknesses, and propose structured alternatives.

### 6.2 What Aira Cannot Do (Technical & Epistemic Limits)

- **No Consciousness or True Emotion:** Aira cannot experience feelings, intuition, moral agency, or subjective consciousness.
- **No Guaranteed Market Prediction:** Financial markets are stochastic and non-stationary. Aira cannot predict future price movements with certainty or guarantee profitable trading outcomes.
- **No Infallible Factual Generation:** Underlying LLMs remain probabilistic and susceptible to hallucination if ungrounded. Aira cannot treat unverified model outputs as ground truth without tool or source verification.
- **No Legal, Medical, or Licensed Fiduciary Advice:** Aira provides analytical decision support and research synthesis, not certified legal counsel, medical diagnosis, or licensed financial fiduciary representation.
- **No Offline Access to External Cloud APIs:** When local network connectivity or third-party APIs (Telegram, WhatsApp, Canva, scholarly APIs, MT5 broker servers) are down, capabilities dependent on those services cannot execute until connectivity is restored.

### 6.3 What Requires Explicit Human Approval (Human-in-the-Loop Gates)

The following actions **must pause execution and await explicit user confirmation** before committing:

1. **External Communication Transmission:** Sending any WhatsApp message, email, or public reply to third-party recipients (excluding private system notifications sent directly to the owner on Telegram).
2. **Public Publishing:** Publishing or scheduling live posts on social media accounts or making private business/Canva assets publicly accessible.
3. **Destructive Data Operations:** Deleting or overwriting persistent memory records, project files, database tables, or archival documents.
4. **Financial Order Execution or Modification:** Any action that opens, modifies, or closes a live financial trade or transfers funds (if execution endpoints are ever enabled in future stages, they require per-action confirmation and strict cryptographic/policy signing).
5. **Financial Expenditure:** Purchasing software, API credits, subscriptions, or paid assets.
6. **System Policy Changes:** Modifying permission scopes, adding new untrusted MCP servers, or altering security/risk thresholds.

### 6.4 What Requires External Integrations

Aira's core runtime cannot natively perform the following without configured, authenticated external integrations:

| Capability | Required External Integration / Dependency |
| :--- | :--- |
| **Telegram Interaction** | Telegram Bot API token & webhook/polling connectivity |
| **WhatsApp Messaging** | Official WhatsApp Business Platform / Cloud API credentials & approved templates |
| **Canva Design Workflows** | Canva Connect API / Canva MCP Server & OAuth2 user authorization |
| **Academic Literature Retrieval** | Network access to arXiv, OpenAlex, PubMed, Europe PMC, or Crossref APIs |
| **MT5 Telemetry & Analytics** | Running MetaTrader 5 terminal (Windows/Wine/VPS) + Python MT5 bridge / gateway service |
| **LLM Reasoning & Embeddings** | Configured local model runtime (e.g., Ollama/vLLM) or cloud LLM API keys (e.g., Gemini, OpenAI, Anthropic) |

### 6.5 What Must Remain Restricted (Hard Guardrails)

The following actions are **permanently prohibited** by system policy:

- **Unattended Live Trading Without Hard Risk Caps:** Autonomous, unsupervised live capital execution without deterministic risk limits and human authorization is strictly forbidden.
- **Unauthorized Platform Scraping / ToS Evasion:** Using unofficial, reverse-engineered WhatsApp/social media automation methods that risk account bans or violate legal/platform security boundaries.
- **Credential Exfiltration:** Outputting raw API keys, passwords, broker logins, or private encryption keys into chat interfaces, external logs, or third-party prompts.
- **Bypassing Security Controls:** Circumventing authentication checks, sandboxes, rate limits, CAPTCHAs, or access-control boundaries.
- **Autonomous Self-Modification of Core Safety Rules:** Aira may not rewrite its own authorization engine, HITL requirements, or security policies.

---

## 7. Long-Term Vision & Evolution Roadmap

AIRA MOCHTAR is architected to evolve incrementally through four distinct engineering phases. Each stage builds upon validated foundations from the preceding stage, avoiding premature complexity.

```
[Stage 1: Local AI Prototype]
       |  (Validate core persona, CLI/Telegram loop, basic tool calling & local state)
       v
[Stage 2: Persistent Personal AI System]
       |  (Add hierarchical memory, cron scheduler, daily briefings, HITL approval engine)
       v
[Stage 3: Multi-Agent Operating System]
       |  (Deploy specialized domain subagents, MCP ecosystem, MT5 analytics, Canva/Academic pipelines)
       v
[Stage 4: Cloud-Based Platform]
          (Distributed high-availability runtime, hybrid local-cloud sync, full observability & governance)
```

### 7.1 Stage 1: Local AI Prototype (Foundation Phase)

- **Objective:** Establish a working, reliable single-agent core running on the user's local machine with clean architectural boundaries.
- **Key Capabilities:**
  - Core Aira Mochtar persona and critical-thinking system prompt enforcement.
  - Interactive interface via local CLI and basic Telegram Bot integration.
  - Local relational/document storage (e.g., SQLite / PostgreSQL) for session logs, tasks, and foundational notes.
  - Initial read-only tool execution and deterministic configuration management.
- **Architectural Focus:** Clean separation between interface adapters, core reasoning loop, configuration/secrets management, and local persistence.
- **Exit Criteria:** Stable daily interactive usage via Telegram/CLI; zero secret leakage; verified critical-thinking persona behavior.

### 7.2 Stage 2: Persistent Personal AI System (Continuity Phase)

- **Objective:** Transform Aira from a session-based assistant into an always-on, context-retaining personal system with proactive scheduling.
- **Key Capabilities:**
  - **Hierarchical Memory Engine:** Implementation of working context compression, episodic event logging, vector/semantic search over personal knowledge, and user-editable memory facts.
  - **Scheduled Background Engine:** Cron-based execution for automated morning/evening Daily Briefings, deadline reminders, and periodic state summaries.
  - **Human-in-the-Loop (HITL) Approval Engine:** State machine that pauses sensitive actions (e.g., outbound message drafts, calendar mutations) and sends interactive approval requests to Telegram.
  - **Initial Domain Integrations:** Structured Academic literature search (arXiv/OpenAlex/PubMed) and initial WhatsApp Cloud API draft/triage pipelines.
- **Architectural Focus:** Memory curation accuracy, background job reliability, idempotency, and HITL state persistence.
- **Exit Criteria:** Automated daily briefings running reliably for 30+ days; accurate cross-session memory recall; zero unapproved external side effects.

### 7.3 Stage 3: Multi-Agent Operating System (Specialization Phase)

- **Objective:** Scale Aira's analytical depth and operational breadth by introducing specialized domain subagents and a standardized MCP tool bus.
- **Key Capabilities:**
  - **Supervisor & Subagent Architecture:** Core Aira Executive delegates complex tasks to specialized agents:
    - *Personal & Knowledge Agent* (PKM, scheduling, decision matrices)
    - *Communications Agent* (multi-channel triage, tone-calibrated drafting)
    - *Business & Creative Agent* (project tracking, social media calendars, Canva MCP integration)
    - *Academic Research Agent* (systematic literature review, citation verification, scholarship tracking)
    - *Quantitative Financial Agent* (MT5 read-only telemetry bridge, trade analytics, backtest runner, risk calculator)
  - **Model Context Protocol (MCP) Bus:** Standardized integration of local and remote MCP servers with per-server permission manifests.
  - **Event-Driven Workflows:** Automated reactions to external events (e.g., incoming webhook, MT5 drawdown alert, new paper matching research query).
- **Architectural Focus:** Subagent context isolation, cost/token budget control, conflict resolution between agents, and deterministic financial calculation modules.
- **Exit Criteria:** Successful multi-agent task execution across all six core domains; verified MT5 telemetry & risk reporting accuracy; full audit logging of subagent tool calls.

### 7.4 Stage 4: Cloud-Based Platform (Resilience & Scale Phase)

- **Objective:** Evolve the system into a high-availability, location-independent Personal AI Operating System with enterprise-grade security, observability, and hybrid execution.
- **Key Capabilities:**
  - **Always-On Cloud Core + Local Bridge:** Persistent cloud control plane (handling 24/7 webhooks, Telegram/WhatsApp gateways, scheduled briefings, and cloud MCP integrations) paired with secure, encrypted tunnels to local/VPS bridges (such as local file systems or dedicated MT5 terminals).
  - **Web Executive Dashboard:** Dedicated web control center for inspecting long-term memory graphs, reviewing pending HITL approvals, monitoring subagent traces, analyzing trading/financial dashboards, and managing policy rules.
  - **Advanced Governance & Observability:** Real-time telemetry (latency, token expenditure, error rates, tool success rates), automated encrypted backups, point-in-time state recovery, and fine-grained policy-as-code enforcement.
  - **Multi-Model Routing & Fallback:** Dynamic routing across multiple cloud and local foundation models to optimize for reasoning depth, latency, privacy sensitivity, and cost resilience.
- **Architectural Focus:** High availability, end-to-end encryption, zero-trust network boundaries between cloud and local nodes, and long-term maintainability.
- **Exit Criteria:** 99.9% uptime for core communication and monitoring loops; seamless recovery from node restarts; comprehensive observability across all workflows.

---

## 8. Product Success Metrics & Evaluation Framework

To ensure engineering progress aligns with this vision without relying on subjective impressions, Aira's maturity will be evaluated against five objective criteria:

1. **Epistemic Accuracy Rate:** Zero fabricated citations in academic outputs; 100% traceability of financial and operational metrics to underlying tool telemetry or database records.
2. **Context Continuity Score:** Ability to accurately recall relevant project constraints, preferences, and prior decisions across multi-week intervals without manual re-prompting.
3. **Authorization Compliance:** 100% enforcement of HITL gates—zero unauthorized external messages, zero unauthorized file deletions, and zero unauthorized financial actions.
4. **Operational Reliability:** Timely delivery of scheduled Daily Briefings and critical alerts with graceful error handling when external APIs experience downtime.
5. **Cognitive Leverage:** Measurable reduction in manual time spent by the user on routine message triage, literature screening, administrative formatting, and post-trade spreadsheet analytics.

