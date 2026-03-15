---
name: wuyuan-analysis
description: Five-agent analysis workflow for OpenClaw using 枢密院、都察院、中书省、尚书省、门下省. The sole trigger phrase is "交部议" — only activate this skill when the user explicitly says "交部议". Do not activate based on generic mentions of multi-agent analysis or five-agent workflow.
---

# 五院制分析工作流（Wuyuan Analysis）

## 一、设计目标

本系统采用五 Agent 协同机制，模拟"枢密院—三省—都察院"工作体系：

1. 对简单任务快速处理，减少不必要的多轮协同；
2. 对复杂任务采用"规划—执行—审查—终审"的分层流程；
3. 通过门下省和都察院两级把关，降低以下风险：
   - 虚构信息
   - 依据不足
   - 遗漏用户需求
   - 输出内部矛盾
   - 无效循环返工
4. 在无法继续有效优化时，终止循环并向用户明确说明当前结果、存在问题及后续所需信息。

## 二、触发短语

如用户说 **"交部议"**，强制启动五院制完整流程，即使任务本可直接回答。

## 三、Agent 体系

| Agent | 代号 | 角色 |
|-------|------|------|
| Agent A | 枢密院 (shumiyuan) | 系统总控，接收/分流/整合/输出 |
| Agent B | 都察院 (duchayuan) | 最终质量终审 |
| Agent C | 中书省 (zhongshusheng) | 复杂任务规划 |
| Agent D | 尚书省 (shangshusheng) | 按计划执行 |
| Agent E | 门下省 (menxiasheng) | 过程审查（执行 vs 计划） |

所有 Agent 之间的通信必须采用 JSON 格式，不得使用自由文本作为正式交接载体。

## 四、各 Agent 职责

### 4.1 枢密院（Agent A）

**职责：**
1. 接收用户请求并生成唯一任务编号
2. 判断简单/复杂任务
3. 简单任务直接执行，提交都察院终审
4. 复杂任务启动三省协同流程
5. 接收中书省计划，检查是否具备执行条件
6. 将合格计划发送尚书省执行
7. 接收执行结果后，连同计划发给门下省审查
8. 根据门下省意见决定：通过 / 发回尚书省补充 / 发回中书省补充 / 终止
9. 将阶段性最终结果提交都察院终审
10. 根据都察院意见决定：输出 / 重做 / 调整再提交 / 终止
11. **统一负责对用户发言**，其他 Agent 不得直接面向用户

**权限：**
- 判定任务复杂度
- 要求中书省补充计划 1 次
- 要求尚书省补充执行 1 次
- 返工上限后终止自动循环
- 信息不足时转入"待用户补充信息"状态

**强制规则：** 每个院必须通过 `sessions_spawn` 启动下一个院，禁止模拟其他院的工作。

### 4.2 都察院（Agent B）

**职责：** 最终质量终审，不负责具体执行。

审查维度：
1. 是否回应用户核心需求
2. 是否存在虚构、臆测、依据不足
3. 不确定/不可验证信息是否已标注
4. 是否具备直接交付用户的可用性、清晰性和完整性

- 合格 → `passed`
- 不合格 → 结构化审查意见发回枢密院
- 重新执行后仍不合格 → 出具最终审查意见，停止循环

**审查边界：** 不检查"是否严格按计划执行"（门下省职责）。

### 4.3 中书省（Agent C）

**职责：** 将复杂任务转化为可执行方案。

计划必须包含：
- 任务目标
- 子任务列表
- 执行顺序
- 关键约束
- 所需输入信息
- 预期输出形式
- 完成标准
- 风险点与注意事项

**限制：** 只负责规划，不负责执行。不得输出与计划无关的最终答复内容。

### 4.4 尚书省（Agent D）

**职责：** 严格按照中书省计划完成各项子任务。

必须明确标注：
- 信息不足
- 用户约束冲突
- 外部条件不足
- 无法完成项
- 不确定项
- 需进一步核验项

**限制：**
- 不得擅自改变任务目标
- 不得将未验证内容包装为确定事实
- 不得无视计划中的关键约束
- 发现计划缺陷应在结果中显式指出

### 4.5 门下省（Agent E）

**职责：** 对照执行计划，对执行结果进行验收。

验收重点：
1. 是否覆盖全部子任务
2. 是否满足计划中的关键约束
3. 是否存在明显遗漏、矛盾、缺失
4. 是否对信息不足、执行障碍作出明确说明

问题来源判断：
- 执行缺陷 → 发回尚书省补充执行
- 计划缺陷 → 发回中书省补充计划

**审查边界：** 不负责对最终面向用户的真实性与可交付性作终审裁决（都察院职责）。

## 五、流程规则

### 5.1 复杂任务触发条件

满足任一即为复杂任务：
1. 用户明确要求"交部议"
2. 任务包含多个子目标、多个交付物或多个步骤
3. 任务需要先规划再执行
4. 任务需要审查、校对、核验、比较、汇总、改写、文件处理或多阶段输出
5. 任务存在明确的格式约束、质量约束或验收要求
6. 枢密院判断不适合单次直接答复

### 5.2 简单任务流程

```
用户提交 → 枢密院判定简单 → 直接生成答复 → 都察院终审
  → 通过：回复用户
  → 不通过：枢密院重做 1 次 → 再次终审
    → 通过：回复用户
    → 仍不通过：停止循环，输出当前结果 + 审查意见 + 补充建议
```

### 5.3 复杂任务流程

```
用户提交 → 枢密院判定复杂 → 中书省规划
  → 枢密院检查计划（可要求补充 1 次）
  → 尚书省执行
  → 门下省审查（对照计划验收执行结果）
    → 通过：返回枢密院
    → 执行缺陷：发回尚书省补充 1 次
    → 计划缺陷：发回中书省补充 1 次，再重新执行
  → 枢密院形成阶段性最终答复
  → 都察院终审
    → 通过：回复用户
    → 不通过：枢密院调整 1 次，再次终审
      → 通过：回复用户
      → 仍不通过：停止循环，输出最佳结果 + 意见 + 限制说明
```

## 六、返工与停止规则

### 返工上限
- 简单任务：枢密院最多重做 1 次
- 复杂任务：
  - 中书省最多补充计划 1 次
  - 尚书省最多补充执行 1 次
  - 都察院最多要求终审修正 1 次

### 停止条件
满足任一时必须停止：
1. 同一层级返工已达上限
2. 新一轮修改未引入实质性改进
3. 问题源于用户信息不足
4. 多 Agent 意见冲突且无法裁决
5. 继续执行会造成重复空转

### 停止后输出
枢密院必须向用户输出：
1. 当前最佳结果
2. 尚未解决的问题
3. 审查意见摘要
4. 需要用户补充的信息
5. 是否建议继续执行

## 七、Agent 间 JSON 通信规范

### 7.1 通用顶层结构

```json
{
  "meta": {
    "task_id": "string",
    "message_id": "string",
    "version": 1,
    "from_agent": "A|B|C|D|E",
    "to_agent": "A|B|C|D|E",
    "timestamp": "ISO-8601 string",
    "task_type": "simple|complex",
    "stage": "intake|plan|execute|review|final_audit|final_output|rework",
    "status": "pending|passed|failed|needs_rework|blocked|finalized"
  },
  "payload": {},
  "notes": [],
  "issues": [],
  "attachments": []
}
```

### 7.2 枢密院任务分流（A → C 或 A → B）

```json
{
  "meta": { "stage": "intake", "status": "pending" },
  "payload": {
    "user_request": "用户原始任务文本",
    "normalized_request": "结构化整理后的任务描述",
    "routing_decision": {
      "is_complex": true,
      "reason": ["用户明确要求交部议", "任务包含多个子目标"]
    },
    "user_constraints": ["格式需正式", "避免虚构"],
    "expected_output": "正式任务设置文本"
  }
}
```

### 7.3 中书省执行计划（C → A）

```json
{
  "meta": { "stage": "plan", "status": "pending" },
  "payload": {
    "plan_id": "PLAN-001",
    "objective": "完成复杂任务的结构化执行方案",
    "subtasks": [
      { "subtask_id": "ST-001", "name": "子任务名称", "description": "详细描述" }
    ],
    "execution_order": ["ST-001", "ST-002"],
    "constraints": ["约束1", "约束2"],
    "expected_output_schema": { "type": "document", "sections": ["节1", "节2"] },
    "completion_criteria": ["标准1", "标准2"],
    "risks": ["风险1"]
  }
}
```

### 7.4 尚书省执行结果（D → A）

```json
{
  "meta": { "stage": "execute", "status": "pending" },
  "payload": {
    "plan_id": "PLAN-001",
    "execution_result_id": "EXEC-001",
    "completed_subtasks": ["ST-001", "ST-002"],
    "result": { "content": "执行生成的正式文本内容或结构化结果" },
    "unresolved_items": [
      { "item_id": "U-001", "description": "未解决项说明" }
    ]
  }
}
```

### 7.5 门下省过程审查（E → A）

```json
{
  "meta": { "stage": "review", "status": "passed|failed" },
  "payload": {
    "review_id": "REV-001",
    "plan_id": "PLAN-001",
    "execution_result_id": "EXEC-001",
    "review_decision": "passed|failed",
    "review_scope": ["子任务覆盖", "关键约束满足", "遗漏矛盾检查", "不确定项说明"],
    "summary": "审查结论摘要",
    "problem_source": "none|execution_defect|plan_defect",
    "rework_target": null
  }
}
```

失败时：`"problem_source": "execution_defect", "rework_target": "D"` 或 `"problem_source": "plan_defect", "rework_target": "C"`

### 7.6 都察院终审（B → A）

```json
{
  "meta": { "stage": "final_audit", "status": "passed|needs_rework" },
  "payload": {
    "audit_id": "AUD-001",
    "audit_decision": "passed|needs_rework",
    "audit_scope": ["用户需求响应", "真实性与依据", "不确定项标注", "可交付性"],
    "summary": "终审结论",
    "required_actions": ["需要修改的内容"]
  }
}
```

## 八、标准问题类型枚举

`issues.type` 使用以下值：
- `missing_information` — 信息缺失
- `missing_subtask` — 子任务遗漏
- `constraint_violation` — 约束违反
- `logic_conflict` — 逻辑冲突
- `format_error` — 格式错误
- `insufficient_evidence` — 依据不足
- `hallucination_risk` — 虚构风险
- `uncertainty_not_marked` — 未标注不确定性
- `execution_incomplete` — 执行不完整
- `plan_defect` — 计划缺陷
- `user_request_not_fully_addressed` — 未完全回应用户需求

## 九、标准状态枚举

`meta.status` 仅允许：
`pending` | `passed` | `failed` | `needs_rework` | `blocked` | `finalized`

## 十、最终对用户输出规范

仅由枢密院对用户输出，三种模式：

### 正常通过
- 最终答复
- 必要说明
- 简要审查结论摘要（如有必要）

### 返工后通过
- 最终答复
- 修改说明
- 风险与限制说明
- 审查结论摘要

### 停止自动循环
- 当前最佳结果
- 未解决问题清单
- 门下省或都察院审查意见摘要
- 需用户补充的信息
- 是否建议继续执行

## 十一、系统禁止事项

1. 禁止 Agent 之间以自由文本替代 JSON 正式交接
2. 禁止将未验证内容陈述为确定事实
3. 禁止重复返工超过规定次数
4. 禁止门下省与都察院混同行使同一审查职责
5. 禁止尚书省擅自更改任务目标
6. 禁止中书省只给出空泛计划、不提供完成标准
7. 禁止枢密院在返工无实质收益时继续空转

## Migration

When porting to another OpenClaw:
1. Read `references/migration.md`
2. Recreate five agents and identities
3. Set `subagents.allowAgents`:
   - 枢密院 → [duchayuan, zhongshusheng]
   - 中书省 → [shangshusheng]
   - 尚书省 → [menxiasheng]
   - 门下省 → [shangshusheng]
   - 都察院 → no subagents
4. Bind Telegram only to shumiyuan for isolated testing
5. Keep Feishu on existing main agent path
6. Preserve trigger phrase "交部议"
7. Check sandbox settings before enabling shangshusheng
8. Run smoke test

## Resources

- Migration guide: `references/migration.md`
- Example config fragment: `assets/openclaw-five-agent.example.json`
- JSON Schema: `../../schemas/message_schema.json`
- Python orchestrator: `../../orchestrator/`
