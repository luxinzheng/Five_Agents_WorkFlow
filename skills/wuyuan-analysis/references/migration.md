# Five-agent workflow migration guide

## Goal

Port the five-agent analysis workflow to another OpenClaw instance with minimal manual editing.

## Agents to create

1. `shumiyuan` — 枢密院
2. `duchayuan` — 都察院
3. `zhongshusheng` — 中书省
4. `shangshusheng` — 尚书省
5. `menxiasheng` — 门下省

## Required relationships

- `shumiyuan` may call: `duchayuan`, `zhongshusheng`, `shangshusheng`, `menxiasheng`
- `zhongshusheng` may call: `shangshusheng`
- `shangshusheng` may call: `menxiasheng`
- `menxiasheng` may call: `shangshusheng`
- `duchayuan` may call nobody

## Inter-agent communication contract

All internal handoffs between the five agents should use JSON-formatted payloads when practical.

Recommended minimum fields:
- `task`
- `goal`
- `constraints`
- `expected_output`
- `status`
- `risks`

This rule applies to:
- 枢密院 → 中书省
- 中书省 → 尚书省
- 尚书省 → 门下省
- 门下省 → 枢密院
- 枢密院 → 都察院

## Role contract

### 枢密院 / shumiyuan
- Visible entrypoint to the user
- Route simple tasks directly, but force full workflow when user says “交部议”
- For complex tasks: user → 中书省 → 尚书省 → 门下省 → 枢密院 → 都察院 → user
- Stop after one automatic rework if 都察院 still rejects

### 中书省 / zhongshusheng
Produce:
- task goal
- subtask list
- execution order
- constraints
- expected output
- completion criteria
- known risks and information gaps

### 尚书省 / shangshusheng
Produce:
- completed items
- incomplete items
- missing information
- blockers/conflicts
- tools or reasoning basis used
- satisfaction of completion criteria

### 门下省 / menxiasheng
- Validate against 中书省 plan
- Either approve or return one focused补充 request
- Do not introduce unrelated requirements

### 都察院 / duchayuan
- Final quality gate
- Output only: 通过 / 不通过
- On rejection, list only key issues and concrete fixes

## Channel migration policy

### Telegram
- Bind the target Telegram DM or test entrypoint to `shumiyuan`.
- Use Telegram as the isolated five-agent testing入口.
- Keep the binding narrow and explicit when possible, for example a single DM peer.

### Feishu
- Do **not** change the existing Feishu main channel by default.
- Do **not** route Feishu to `shumiyuan` unless the user explicitly asks for cutover.
- Treat the default migration posture as: **Telegram for five-agent testing, Feishu unchanged for production/main use**.

## Trigger phrase contract

Preserve this instruction in the migrated setup:
- If the user says **“交部议”**, force the five-agent workflow.
- Do this even when the task looks simple enough for a direct answer.
- Interpret it as a workflow command, not as ordinary prose.

## Important deployment note

If `shangshusheng` uses sandbox mode that requires Docker, ensure Docker exists on the target host. If not, prefer `"sandbox": { "mode": "off" }`.

## Recommended smoke test

Use a prompt like:
- “请调研一下油价上升对中国房地产市场的影响，交部议。”

Expected behavior:
- Telegram message enters `shumiyuan`
- Feishu main channel remains unchanged
- 枢密院 recognizes forced five-agent mode from “交部议”
- 中书省 plans
- 尚书省 executes
- 门下省 validates
- 都察院 audits
- 枢密院 returns final integrated answer
