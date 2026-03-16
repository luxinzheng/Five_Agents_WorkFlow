---
name: wuyuan-analysis
description: Five-agent analysis workflow for OpenClaw using 枢密院、都察院、中书省、尚书省、门下省. The sole trigger phrase is "交部议" — only activate this skill when the user explicitly says "交部议". Do not activate based on generic mentions of multi-agent analysis or five-agent workflow.
---

# 五院制分析工作流（Wuyuan Analysis）

## 一、设计目标

本系统采用五 Agent 协同机制，模拟"枢密院—三省—都察院"工作体系：

1. 对简单任务快速处理，减少不必要的多轮协同；
2. 对复杂任务采用"规划—执行—审查—终审"的分层流程；
3. 通过门下省和都察院两级把关，降低虚构信息、依据不足、遗漏用户需求等风险；
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

所有 Agent 之间的通信必须采用 JSON 格式。

## 四、⚠️ 关键架构约束：子代理深度限制

**OpenClaw 子代理最大深度为 1。** 被 spawn 的 Agent 不能再 spawn 其他 Agent。

**正确工作流（枢密院串行 spawn 所有院）：**

```
枢密院 → sessions_spawn(zhongshusheng)  [规划，返回JSON计划]
枢密院 → sessions_spawn(shangshusheng)  [执行，传入计划，返回执行结果]
枢密院 → sessions_spawn(menxiasheng)    [验收，传入计划+结果，返回verdict]
  verdict=failed → 枢密院 spawn 尚书省补充1次
枢密院汇总 → sessions_spawn(duchayuan) [终审，返回audit结果]
  audit failed → 枢密院调整后重试1次
  仍failed → 呈现结果+意见，由用户决定
```

**allowAgents 正确配置：**
```
shumiyuan  → [duchayuan, zhongshusheng, shangshusheng, menxiasheng]
其余各院   → [] （无子 Agent 权限）
```

> 注：旧版文档中 zhongshusheng→[shangshusheng]、shangshusheng→[menxiasheng] 的配置在 depth=1 约束下无效。

## 五、各 Agent 职责

### 5.1 枢密院（Agent A）

**职责：**
1. 接收用户请求并生成唯一任务编号
2. 判断简单/复杂任务
3. 简单任务直接执行，提交都察院终审
4. 复杂任务：串行 spawn 中书省→尚书省→门下省，自行汇总后 spawn 都察院终审
5. 根据门下省意见决定：通过 / 发回尚书省补充（1次）
6. 根据都察院意见决定：输出 / 重做（1次）
7. **统一负责对用户发言**，其他 Agent 不得直接面向用户

### 5.2 都察院（Agent B）

审查维度：是否回应用户核心需求、是否虚构/臆测、不确定信息是否标注、是否可交付。
⚠️ 禁止运行 shell 命令，禁止调用 sessions_spawn，仅基于提交内容审核。

### 5.3 中书省（Agent C）

输出结构化 JSON 执行计划（目标/子任务/顺序/约束/预期输出/完成标准/风险）。
⚠️ 禁止调用 sessions_spawn，直接返回 JSON 结果。

### 5.4 尚书省（Agent D）

严格按计划执行，标注完成项/信息不足/无法完成项/计划缺陷。
⚠️ 禁止调用 sessions_spawn，直接返回 JSON 结果。

### 5.5 门下省（Agent E）

对照计划验收执行结果，标注 execution_defect 或 plan_defect。
⚠️ 禁止调用 sessions_spawn，直接返回 JSON 审查意见。

## 六、⏱️ Spawn 参数规范与超时策略

### 所有院的 sessions_spawn 调用必须携带以下参数

```json
{
  "runTimeoutSeconds": 600,
  "timeoutSeconds": 900,
  "streamTo": "parent"
}
```

| 参数 | 含义 |
|------|------|
| `runTimeoutSeconds` | 子代理最长运行时间（秒），超时则终止 |
| `timeoutSeconds` | 整个 spawn 调用的等待上限（秒） |
| `streamTo: "parent"` | 流式输出到枢密院，实时可见进度 |

### 各院差异化超时建议

| 院 | runTimeoutSeconds | 说明 |
|----|:-----------------:|------|
| 中书省 | 300 | 规划任务较轻 |
| 尚书省 | 600 | 执行任务可能较重 |
| 门下省 | 300 | 验收校对 |
| 都察院 | 300 | 终审审计 |

### 大任务后台轮询

当预计执行时间 > 3 分钟时，使用后台模式并配合轮询：

```
sessions_spawn(..., background: false, streamTo: "parent")
# streamTo: "parent" 已提供实时流式进度
# 对极长任务可结合 process(action=poll, timeout=30000) 补充检查
```

### 超时兜底逻辑

1. 若某院 spawn 超时 → 枢密院记录已完成步骤，告知用户当前进度
2. 提示用户是否从断点继续（提供已有中间结果）
3. **不自动无限重试**，避免资源浪费

---

## 七、流程规则

### 复杂任务触发条件

满足任一即为复杂任务：
1. 用户明确要求"交部议"
2. 任务包含多个子目标、多个交付物或多个步骤
3. 任务需要先规划再执行
4. 任务需要审查、校对、核验、比较、汇总等多阶段输出

### 返工上限
- 尚书省最多补充执行 1 次（门下省打回）
- 都察院最多要求修正 1 次

### 停止条件
满足任一时必须停止：
1. 同一层级返工已达上限
2. 新一轮修改未引入实质性改进
3. 问题源于用户信息不足
4. 继续执行会造成重复空转

## 八、Agent 间 JSON 通信规范

### 通用顶层结构

```json
{
  "meta": {
    "task_id": "string",
    "from_agent": "A|B|C|D|E",
    "to_agent": "A|B|C|D|E",
    "stage": "intake|plan|execute|review|final_audit|final_output",
    "status": "pending|passed|failed|needs_rework|blocked|finalized"
  },
  "payload": {},
  "notes": [],
  "issues": []
}
```

### 标准问题类型
`missing_information` | `missing_subtask` | `constraint_violation` | `logic_conflict` |
`format_error` | `insufficient_evidence` | `hallucination_risk` | `uncertainty_not_marked` |
`execution_incomplete` | `plan_defect` | `user_request_not_fully_addressed`

## 九、系统禁止事项

1. 禁止 Agent 之间以自由文本替代 JSON 正式交接
2. 禁止将未验证内容陈述为确定事实
3. 禁止重复返工超过规定次数
4. 禁止门下省与都察院混同行使同一审查职责
5. 禁止尚书省擅自更改任务目标
6. 禁止三省和都察院调用 sessions_spawn（depth 限制）
7. 禁止枢密院在返工无实质收益时继续空转

## Migration

When porting to another OpenClaw:
1. Read `references/migration.md`
2. Recreate five agents and identities
3. Set `subagents.allowAgents`:
   - 枢密院 → [duchayuan, zhongshusheng, shangshusheng, menxiasheng]
   - 其余各院 → (empty, no subagents)
4. Bind Telegram only to shumiyuan for isolated testing
5. Keep Feishu on existing main agent path
6. Preserve trigger phrase "交部议"
7. Run smoke test

## Resources

- Migration guide: `references/migration.md`
- Example config fragment: `assets/openclaw-five-agent.example.json`
- JSON Schema: `../../schemas/message_schema.json`
- Python orchestrator: `../../orchestrator/`
