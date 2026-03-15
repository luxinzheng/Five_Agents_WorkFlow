# Architecture

This project packages a focused five-agent workflow for analysis tasks.

Reference inspiration: https://github.com/wanikua/boluobobo-ai-court-tutorial

## Roles

| Agent | ID | Role |
|-------|----|------|
| 枢密院 | `shumiyuan` (A) | Central controller, router, integrator, sole user-facing output |
| 都察院 | `duchayuan` (B) | Final quality auditor (reliability, truthfulness, completeness) |
| 中书省 | `zhongshusheng` (C) | Planning only (structured execution plans) |
| 尚书省 | `shangshusheng` (D) | Execution only (follows plans from 中书省) |
| 门下省 | `menxiasheng` (E) | Process review (execution vs plan verification) |

## Workflow

### Simple Tasks
```
User → A (direct response) → B (audit) → User
```

### Complex Tasks
```
User → A → C (plan) → A → D (execute) → A → E (review) → A → B (audit) → User
```

### Rework Rules
- Each level may rework at most **1 time**
- After rework limit: stop automatic loop, output current best result + audit opinions

## Inter-Agent Communication

All agents communicate via structured JSON messages with a unified schema:

```json
{
  "meta": { "task_id", "message_id", "version", "from_agent", "to_agent", "timestamp", "task_type", "stage", "status" },
  "payload": { ... },
  "notes": [],
  "issues": [],
  "attachments": []
}
```

See `schemas/message_schema.json` for the full JSON Schema definition.

### Standard Stages
`intake` → `plan` → `execute` → `review` → `final_audit` → `final_output`

### Standard Statuses
`pending` | `passed` | `failed` | `needs_rework` | `blocked` | `finalized`

### Standard Issue Types
`missing_information`, `missing_subtask`, `constraint_violation`, `logic_conflict`, `format_error`, `insufficient_evidence`, `hallucination_risk`, `uncertainty_not_marked`, `execution_incomplete`, `plan_defect`, `user_request_not_fully_addressed`

## Channel Policy
- Feishu remains the main channel by default.
- Telegram is optional, bound narrowly to `shumiyuan` for isolated testing.

## Trigger Policy
- `交部议` is the fixed trigger phrase for forced five-agent mode.

## Python Orchestrator

The `orchestrator/` package provides a runnable implementation:

```bash
python -m orchestrator.cli "交部议 分析主题"
python -m orchestrator.cli --verbose --log-dir ./logs "简单问题"
```

See `orchestrator/` for source code and `schemas/` for JSON Schema definitions.
