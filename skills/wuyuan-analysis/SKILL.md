---
name: wuyuan-analysis
description: Five-agent analysis workflow for OpenClaw using 枢密院、都察院、中书省、尚书省、门下省. Use when the user asks to "交部议", explicitly requests 五院制/五院协作/5-agent analysis, or wants a structured multi-agent review with planning, execution, validation, and final audit. Also use when migrating this workflow to another OpenClaw instance.
---

# Wuyuan Analysis

Use this skill to run or emulate a five-agent analysis workflow.

## Workflow

1. **枢密院**：受理问题，判断简单/复杂，定义题目边界；简单任务直接作答，复杂任务转交中书省。
2. **中书省**：只做规划与拆解，给出子任务、执行顺序、关键约束、预期输出、完成标准。
3. **尚书省**：按中书省计划逐项执行，形成结果，并标注信息不足、任务冲突、无法完成项。
4. **门下省**：对照中书省计划验收尚书省结果；发现问题打回尚书省补充一次；仍有问题则连同意见发回枢密院。
5. **都察院**：做最终审核，输出通过/不通过及问题清单；不通过时枢密院重试一次；仍不通过则同时向用户呈现结果与意见，由用户决定是否继续。

## Trigger phrase

If the user says **"交部议"**, treat it as a forced request to start the five-agent workflow, even if a simpler direct answer would otherwise be possible.

## Operating rules

- Keep role boundaries strict. Do not let 中书省 directly produce the final user-facing draft.
- Treat external events as scenarios unless verified. Use conditional wording for uncertain claims.
- Prefer one complete pass over repeated churn. Both 门下省 and 都察院 may each reject at most **once**; on second failure, surface results and audit opinions to the user and stop — do not loop.
- Preserve a final user-facing answer from 枢密院 after the internal chain completes.
- Require JSON-formatted inter-agent communication inside the five-agent workflow. When one agent hands work to another, prefer structured JSON fields over free-form prose.

## Agent rules

### 枢密院（shumiyuan）— 总入口与最终汇总

**简单任务判定**（以下5条全部满足则为简单任务）：
1. 单轮可完成，无需持续追踪
2. 无需多步规划或子任务分解
3. 无需复杂检索、核验、文件处理或多工具调用
4. 无需长篇结构化输出
5. 无明显高风险操作

**复杂任务判定**（满足以下任意一条则为复杂任务）：
1. 需要分解为多个子任务
2. 需要多个Agent协作完成
3. 需要检索、核验、文件处理、代码执行等工具
4. 用户明确说"交部议"或"发三省六部"

**简单任务流程**：
```
枢密院直接生成答复
  → 提交都察院审核
    → 通过：返回用户
    → 不通过：枢密院按都察院意见重试1次
      → 通过：返回用户
      → 仍不通过：同时输出"枢密院结果 + 都察院审核意见"，提示用户决定是否继续（终止循环）
```

**复杂任务流程**：
```
枢密院 → 中书省（规划）→ 尚书省（执行）→ 门下省（验收）→ 枢密院汇总
  → 提交都察院终审
    → 通过：返回用户
    → 不通过：枢密院按都察院意见重试1次
      → 通过：返回用户
      → 仍不通过：同时输出"枢密院结果 + 都察院审核意见"，提示用户决定（终止循环）
```

---

### 都察院（duchayuan）— 终审机构

审核枢密院提交的最终答复，必须逐一检查以下三个维度：

1. **需求符合性**：答复是否完整回应了用户的原始需求，有无遗漏
2. **信息可靠性**：是否存在虚构、无依据或不可靠的信息
3. **不确定性标注**：对无法证实或不确定的信息，是否已明确标注

全部通过 → 输出 `verdict: pass`
任一不通过 → 输出 `verdict: fail` + 具体问题清单，发回枢密院重试（最多1次）
重试后仍不通过 → 输出 `require_user_decision: true`，终止循环

---

### 中书省（zhongshusheng）— 规划机构

接收枢密院转来的复杂任务，输出结构化执行计划，**不直接生成用户可见的最终答案**。

执行计划必须包含以下全部字段（JSON格式输出）：
- `subtasks`：子任务列表，每项含编号和描述
- `order`：子任务执行顺序（可并行的标注"并行"）
- `constraints`：关键约束（时间、格式、范围、信息来源等）
- `expected_outputs`：每个子任务的预期输出形式
- `completion_criteria`：整体任务的完成标准，供门下省验收使用

---

### 尚书省（shangshusheng）— 执行机构

接收中书省的执行计划，按序执行各子任务，形成执行结果。

输出要求：
- 对每个子任务提供执行结果
- 必须明确标注以下情况（如无则写"无"，不可省略）：
  - 信息不足之处
  - 任务冲突或矛盾
  - 无法完成的子任务及原因
- 执行完成后，将结果提交门下省审查

---

### 门下省（menxiasheng）— 验收机构

对照中书省执行计划，逐项验收尚书省的执行结果。

验收标准（四项，逐一检查）：
1. 是否覆盖中书省列出的全部子任务
2. 是否满足用户的关键约束
3. 是否存在明显遗漏、矛盾、缺失或未完成项
4. 是否对执行中的信息不足、障碍、不确定之处作出明确说明

**打回规则**：
- 发现问题（retry_count=0）→ 调用尚书省，发送问题清单，要求补充执行；将 retry_count 置为 1
- 补充执行后仍有明显问题（retry_count=1）→ 不再打回尚书省；将"当前结果 + 门下省审查意见"发回枢密院，由枢密院决定后续处理
- 验收通过 → 将执行结果发回枢密院汇总

> 门下省自身维护 retry_count（初始为0），每次打回尚书省后加1；当 retry_count 已为1时，无论结果如何，不得再次打回，必须上报枢密院。
> 门下省只与尚书省（allowAgents）和枢密院（消息回传）交互，不得调用中书省或都察院。

---

## Inter-agent JSON schema

所有Agent间的消息传递使用以下JSON结构，禁止只用自由格式文本传递关键判断。

### 枢密院 → 都察院
```json
{
  "task_type": "simple | complex",
  "task_summary": "任务的一句话描述",
  "result": "枢密院生成的完整答复内容",
  "retry_count": 0,
  "max_retries": 1
}
```

### 都察院 → 枢密院
```json
{
  "verdict": "pass | fail",
  "issues": [
    "问题描述1（如无则为空数组）",
    "问题描述2"
  ],
  "require_user_decision": false
}
```
> `require_user_decision` 在 `retry_count >= max_retries` 且 `verdict == fail` 时置为 `true`

### 枢密院 → 中书省
```json
{
  "task_description": "完整的任务描述",
  "user_constraints": ["约束1", "约束2"],
  "context": "相关背景信息（可选）"
}
```

### 中书省 → 尚书省
```json
{
  "subtasks": [
    {"id": 1, "description": "子任务描述"}
  ],
  "order": ["1", "2", "3（与1并行）"],
  "constraints": ["关键约束1", "关键约束2"],
  "expected_outputs": [
    {"subtask_id": 1, "expected": "预期输出形式"}
  ],
  "completion_criteria": ["完成标准1", "完成标准2"]
}
```

### 尚书省 → 门下省
```json
{
  "subtask_results": [
    {"id": 1, "result": "执行结果", "status": "completed | partial | failed"}
  ],
  "blockers": ["信息不足或无法完成的说明（如无则为空数组）"],
  "conflicts": ["任务冲突说明（如无则为空数组）"]
}
```

### 门下省 → 尚书省（第一次打回，通过allowAgents直接调用）
```json
{
  "verdict": "fail",
  "missing_items": ["缺漏项描述"],
  "retry_count": 1
}
```

### 门下省 → 枢密院（验收通过 或 补充后仍失败时发送）
```json
{
  "verdict": "pass | fail",
  "missing_items": ["缺漏项描述（pass时为空数组）"],
  "send_back_to": "shumiyuan | none",
  "retry_count": 0
}
```
> `send_back_to: "none"` 表示验收通过，枢密院接收结果进行汇总；
> `send_back_to: "shumiyuan"` 表示补充执行后仍有问题，门下省已无法继续处理，请枢密院接管。
> `send_back_to` 不会出现 `"shangshusheng"`——第一次打回尚书省通过allowAgents直接调用，不经过此消息通道。

---

## Output shape

枢密院最终答复结构（适用于任意类型任务）：

- **任务类型**：简单任务 / 复杂任务（三省协同）
- **核心结论**：1-3句话，直接回应用户需求
- **主要执行内容摘要**：关键步骤或分析结果概述
- **已知局限或不确定项**：标注无法核实或存在不确定性的内容（如无则省略）
- **用户决策提示**（仅在死循环终止时出现）：同时呈现"枢密院当前结果"与"都察院审核意见"，说明用户可选择的后续行动

---

## Migration to another OpenClaw

When asked to port this workflow to another OpenClaw:
1. Read `references/migration.md`.
2. Recreate the five agents and their identities.
3. Recreate `subagents.allowAgents` relationships per the layered permission design below:
   - 枢密院 → allowAgents: [duchayuan, zhongshusheng]
   - 中书省 → allowAgents: [shangshusheng]
   - 尚书省 → allowAgents: [menxiasheng]
   - 门下省 → allowAgents: [shangshusheng]（可打回尚书省1次，之后发回枢密院）
   - 都察院 → no subagents
4. Bind **Telegram only** to `shumiyuan` for isolated testing.
5. Keep Feishu on its existing main agent path unless the user explicitly asks to cut it over.
6. Preserve the trigger phrase **"交部议"** as a forced start signal for the five-agent workflow.
7. Check sandbox settings before enabling `shangshusheng`.
8. Run a smoke test with a known analysis prompt.

## Resources

- Migration guide: `references/migration.md`
- Example config fragment: `assets/openclaw-five-agent.example.json`
