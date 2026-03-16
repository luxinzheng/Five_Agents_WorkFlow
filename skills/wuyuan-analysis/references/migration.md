# Five-agent workflow migration guide

## Goal

Port the five-agent analysis workflow to another OpenClaw instance with minimal manual editing.

## Agents to create

1. `shumiyuan` — 枢密院
2. `duchayuan` — 都察院
3. `zhongshusheng` — 中书省
4. `shangshusheng` — 尚书省
5. `menxiasheng` — 门下省

## ⚠️ Critical: Subagent Depth Constraint

OpenClaw enforces a **subagent depth limit of 1**. This means only depth-0 agents can spawn subagents.

**Correct allowAgents configuration:**
- `shumiyuan` may call: `duchayuan`, `zhongshusheng`, `shangshusheng`, `menxiasheng`
- All other agents: **no allowAgents** (empty)

> Previous documentation listed zhongshusheng→[shangshusheng] and shangshusheng→[menxiasheng].
> This is incorrect under the depth=1 constraint. Only 枢密院 orchestrates the chain.

## Workflow Orchestration

枢密院 (depth 0) directly orchestrates the entire chain by serial spawning:

```
枢密院 → spawn(zhongshusheng)  → receive plan JSON
枢密院 → spawn(shangshusheng)  → receive execution result JSON
枢密院 → spawn(menxiasheng)    → receive review verdict JSON
枢密院 → spawn(duchayuan)      → receive audit result JSON
枢密院 → output to user
```

Each subordinate agent completes its own role and returns results. They do NOT spawn the next agent.

## Role contract

### 枢密院 / shumiyuan
- Visible entrypoint to the user
- Route simple tasks directly, but force full workflow when user says "交部议"
- Serial spawn: zhongshusheng → shangshusheng → menxiasheng → duchayuan
- Handle rework: spawn shangshusheng again if menxiasheng fails (max 1 rework)
- Handle audit: spawn duchayuan again after adjusting if it fails (max 1 rework)
- Stop automatic loop after rework limits

### 中书省 / zhongshusheng
Produce JSON plan:
- task goal, subtask list, execution order, constraints
- expected output, completion criteria, known risks and gaps

⚠️ Must NOT call sessions_spawn. Return JSON directly.

### 尚书省 / shangshusheng
Produce JSON execution result:
- completed items, incomplete items, missing information
- blockers/conflicts, plan defects noted

⚠️ Must NOT call sessions_spawn. Return JSON directly.

### 门下省 / menxiasheng
- Validate against 中书省 plan
- Output verdict: passed / failed
- If failed: specify problem_source (execution_defect or plan_defect)
- Do not introduce unrelated requirements

⚠️ Must NOT call sessions_spawn. Return JSON directly.

### 都察院 / duchayuan
- Final quality gate: user need addressed, no hallucination, uncertainty marked, deliverable
- Output: passed / failed (with structured issues)
- On second rejection: require_user_decision=true, stop loop

⚠️ Must NOT run shell commands. Must NOT call sessions_spawn. Return JSON directly.

## Inter-agent communication contract

All internal handoffs between agents use JSON-formatted payloads.

Recommended minimum fields:
- `meta`: task_id, from_agent, to_agent, stage, status
- `payload`: task/plan/result/review content
- `issues`: structured issue list

## Channel migration policy

### Telegram
- Bind the target Telegram DM or test entrypoint to `shumiyuan`.
- Use Telegram as the isolated five-agent testing入口.

### Feishu
- Do **not** change the existing Feishu main channel by default.
- Treat the default migration posture as: **Telegram for five-agent testing, Feishu unchanged**.

## Trigger phrase contract

- If the user says **"交部议"**, force the five-agent workflow.
- Interpret it as a workflow command, not ordinary prose.

## Recommended smoke test

Use a prompt like:
- "请调研一下油价上升对中国房地产市场的影响，交部议。"

Expected behavior:
- 枢密院 recognizes forced five-agent mode
- 枢密院 serially spawns: 中书省 → 尚书省 → 门下省 → 都察院
- 枢密院 returns final integrated answer to user
