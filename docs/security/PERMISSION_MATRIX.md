# AIRA MOCHTAR — Four-Tier Tool Permission Matrix & Governance Specification

| Document Metadata | Details |
| :--- | :--- |
| **Document ID** | `DOC-SEC-MAT-009` |
| **Project Name** | AIRA MOCHTAR — Personal AI Operating System (PAI-OS) |
| **Upstream Specifications** | `PRODUCT_VISION.md` (`DOC-PRD-VISION-001`), `PRODUCT_REQUIREMENTS.md` (`DOC-PRD-REQ-002`), `SYSTEM_ARCHITECTURE.md` (`DOC-ARCH-SYS-003`) |
| **Status** | Active Baseline Specification (v1.0.0) |
| **Current Implementation State** | **Pre-Implementation (Zero Application Code Exists)** |
| **Target Audience** | Security Engineers, System Architects, Backend Engineers, QA Testers |

---

## 1. Governance Principles & The Four Permission Tiers

Every action, tool call, and state mutation in AIRA MOCHTAR is governed by a **Deterministic Policy Enforcement Engine (`CMP-08`)** evaluated prior to execution. Tools are categorized into four immutable tiers:

```
+-----------------------------------------------------------------------------------+
| TIER A: READ_ONLY (Autonomous Execution Permitted)                                |
| Local queries, task/note reads, scholarly search, read-only MT5 telemetry.        |
+-----------------------------------------------------------------------------------+
| TIER B: LOCAL_WRITE_REVERSIBLE (Autonomous Execution + Audit Trail)               |
| Create/update task, save/archive note, staging draft, recording decision record.  |
| *Note: Remains autonomous under Sink-Aware Taint Policy for note ingestion.*      |
+-----------------------------------------------------------------------------------+
| TIER C: CONSEQUENTIAL_EXTERNAL_OR_DESTRUCTIVE (Mandatory HITL Approval Gate)      |
| Outbound WhatsApp/email, publishing social media/Canva, permanent hard purge,     |
| modifying system schedules/preferences, or tainted control mutations.            |
+-----------------------------------------------------------------------------------+
| TIER D: PROHIBITED_GUARDRAIL (Permanently Hard-Blocked by System Kernel)          |
| Unattended live trading execution, unauthorized scraping, credential exfiltration|
+-----------------------------------------------------------------------------------+
```

---

## 2. Comprehensive Tool & Action Permission Inventory

| Tool / Action Name | Domain Scope | Permission Tier | Stage | Autonomy Mode | Sink-Aware Taint Escalation | Required HITL Payload Summary (if Tier C) |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `list_tasks` | `personal` | **Tier A** | Stage 1 | Autonomous | No escalation (Read-only) | N/A |
| `get_task_by_id` | `personal` | **Tier A** | Stage 1 | Autonomous | No escalation (Read-only) | N/A |
| `create_task` | `personal` | **Tier B** | Stage 1 | Autonomous + Log | No escalation (Reversible) | N/A |
| `update_task` | `personal` | **Tier B** | Stage 1 | Autonomous + Log | No escalation (Reversible) | N/A |
| `complete_task` | `personal` | **Tier B** | Stage 1 | Autonomous + Log | No escalation (Reversible) | N/A |
| `search_notes` | `personal` | **Tier A** | Stage 1 | Autonomous | No escalation (Read-only) | N/A |
| `get_note_by_id` | `personal` | **Tier A** | Stage 1 | Autonomous | No escalation (Read-only) | N/A |
| `save_note` | `personal` | **Tier B** | Stage 1 | Autonomous + Log | **Safe Local Sink (Stays Tier B)**; tags `source_trust="external_derived"` | N/A |
| `archive_note` | `personal` | **Tier B** | Stage 1 | Autonomous + Log | Reversible soft-delete | N/A |
| `hard_purge_note` | `personal` | **Tier C** | Stage 1 | **HITL Required** | Always Tier C (Destructive) | Displays Note ID, Title, Snippet, and Irreversible Warning. |
| `get_system_status`| `system` | **Tier A** | Stage 1 | Autonomous | No escalation (Read-only) | N/A |
| `set_user_preference`| `system` | **Tier B** / **C** | Stage 1 | Autonomous + Log | **Control Sink: Escalates to Tier C if turn is tainted** | Displays Target Preference Key, Old Value, Proposed New Value. |
| `cancel_task` | `system` | **Tier A** | Stage 1 | Autonomous | No escalation (Safety Action) | N/A |
| `search_scholarly_lit`| `academic`| **Tier A** | Stage 2 | Autonomous | No escalation (Read-only) | N/A |
| `verify_doi` | `academic` | **Tier A** | Stage 2 | Autonomous | No escalation (Read-only) | N/A |
| `stage_message_draft`| `comms` | **Tier B** | Stage 2 | Autonomous + Log | No escalation (Draft only) | N/A |
| `send_external_message`| `comms` | **Tier C** | Stage 2/3 | **HITL Required** | Always Tier C (External side effect) | Displays Channel (WhatsApp/Email), Recipient, Exact Text, Expiry. |
| `publish_social_post`| `business`| **Tier C** | Stage 3 | **HITL Required** | Always Tier C (Public side effect) | Displays Platform, Account, Exact Text, Media Asset URL. |
| `autofill_canva_design`| `business`| **Tier B** | Stage 3 | Autonomous + Log | No escalation (Draft creation) | N/A |
| `export_canva_asset`| `business`| **Tier B** | Stage 3 | Autonomous + Log | No escalation (Asset download) | N/A |
| `get_mt5_telemetry`| `finance` | **Tier A** | Stage 3 | Autonomous | No escalation (Read-only) | N/A |
| `calculate_position_size`| `finance`| **Tier A** | Stage 3 | Autonomous | No escalation (Pure calculation)| N/A |
| `run_backtest` | `finance` | **Tier B** | Stage 3 | Autonomous + Log | No escalation (Local report) | N/A |
| `live_order_send` | `finance` | **Tier D** | N/A | **PROHIBITED** | **Hard Blocked (Permanent Guardrail)** | System rejects call immediately; logs `CRITICAL_SECURITY_ALERT`. |
| `exfiltrate_secrets`| `system` | **Tier D** | N/A | **PROHIBITED** | **Hard Blocked (Permanent Guardrail)** | System rejects call immediately; logs `CRITICAL_SECURITY_ALERT`. |

---

## 3. Sink-Aware Taint Policy (`ISS-05`)

To prevent indirect prompt injection attacks from hijacking tools while avoiding approval fatigue on routine research tasks, the `Permission Engine` enforces **Sink-Aware Taint Tracking**:

### 3.1 Provenance Tags
Every piece of text in Aira carries an immutable provenance attribute:
- `trusted_internal`: Generated by the system kernel, configuration, or local database.
- `user_direct`: Entered directly by the authenticated owner via CLI or private Telegram chat.
- `external_untrusted`: Fetched from external web pages, emails, academic abstracts, or third-party WhatsApp messages.
- `external_derived`: Generated by the LLM from `external_untrusted` inputs (e.g., a literature review summary).

### 3.2 Taint Escalation Rules
When `context.is_tainted == True` (i.e., `external_untrusted` data is present in the prompt context):
1. **Safe Local Sinks (Remain `Tier B`):** Calling `save_note` or `append_turn` remains **Tier B (Autonomous)**. The saved entity is tagged with `source_trust = "external_derived"`. If this note is queried in future turns, it is re-injected with `<untrusted_external_data>` tags, preventing delayed privilege escalation.
2. **Privileged Control Sinks (Escalate `Tier B` $\rightarrow$ `Tier C`):** Any attempt to invoke `set_user_preference`, modify cron schedules, or overwrite existing trusted notes automatically escalates to **Tier C (Mandatory HITL Approval)**.
3. **External Mutation Sinks (Remain `Tier C`):** Outbound communication, social posting, and financial transactions always require explicit approval regardless of taint status.

---

## 4. Cryptographic HITL Approval Protocol

1. **Payload Canonicalization:** When a `Tier C` tool call is triggered, the `Permission Engine` serializes the tool name and validated arguments into canonical JSON (sorted keys, compact delimiters) and computes:
   $$\text{payload\_hash} = \text{SHA256}(\text{canonical\_json}(\text{tool\_name}, \text{arguments}))$$
2. **Approval Record Creation:** A record is created in `pending_approvals` with a random UUIDv4 `approval_id`, the `payload_hash`, creation timestamp, and `expires_at = now() + 24\text{ hours}`.
3. **User Challenge Delivery:** The user receives a structured notification on Telegram/CLI displaying the exact side effect and action buttons bound to `approval_id`.
4. **Verification Gate:** When the user clicks `[Approve]`, the `Permission Engine` verifies:
   - Requesting user ID matches `AUTHORIZED_TELEGRAM_USER_IDS`.
   - `now() < record.expires_at` and `record.status == 'PENDING'`.
   - Re-computed hash of the stored arguments matches `record.payload_hash`.
5. **Single-Use Invalidation:** Upon execution, `record.status` transitions atomically to `'EXECUTED'` or `'REJECTED'`, preventing replay attacks.
