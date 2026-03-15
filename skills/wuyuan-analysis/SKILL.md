---
name: wuyuan-analysis
description: Five-agent analysis workflow for OpenClaw using 枢密院、都察院、中书省、尚书省、门下省. Use when the user asks to "交部议", explicitly requests 五院制/五院协作/5-agent analysis, or wants a structured multi-agent review with planning, execution, validation, and final audit. Also use when migrating this workflow to another OpenClaw instance.
---

# Wuyuan Analysis

Use this skill to run or emulate a five-agent analysis workflow.

## Workflow

1. **枢密院**：受理问题，判断简单/复杂，定义题目边界。
2. **中书省**：只做规划与拆解，给出目标、子任务、顺序、约束、完成标准、风险缺口。
3. **尚书省**：按计划执行，形成分析正文，并标注未完成项、信息不足、障碍与依据。
4. **门下省**：对照中书省计划验收尚书省结果；通过或打回一次补充。
5. **都察院**：做最终审核，只给“通过/不通过”；枢密院据此向用户交付。

## Trigger phrase

If the user says **“交部议”**, treat it as a forced request to start the five-agent workflow, even if a simpler direct answer would otherwise be possible.

## Operating rules

- Keep role boundaries strict. Do not let 中书省 directly produce the final user-facing draft.
- Treat external events as scenarios unless verified. Use conditional wording for uncertain claims.
- Prefer one complete pass over repeated churn. If 门下省 or 都察院 rejects once, allow at most one targeted rework.
- Preserve a final user-facing answer from 枢密院 after the internal chain completes.
- Separate **short-term market sentiment** from **medium-term fundamentals**.
- Distinguish **domestic core drivers** from **external amplifiers**.
- Require JSON-formatted inter-agent communication inside the five-agent workflow. When one agent hands work to another, prefer structured JSON fields over free-form prose.

## Output shape

Default final answer from 枢密院:
- One-line conclusion
- Main transmission mechanisms
- Short-term vs medium-term impact
- Policy offset / constraints
- Structural differentiation or risk notes

## Migration to another OpenClaw

When asked to port this workflow to another OpenClaw:
1. Read `references/migration.md`.
2. Recreate the five agents and their identities.
3. Recreate `subagents.allowAgents` relationships.
4. Bind **Telegram only** to `shumiyuan` for isolated testing.
5. Keep Feishu on its existing main agent path unless the user explicitly asks to cut it over.
6. Preserve the trigger phrase **“交部议”** as a forced start signal for the five-agent workflow.
7. Check sandbox settings before enabling `shangshusheng`.
8. Run a smoke test with a known analysis prompt.

## Resources

- Migration guide: `references/migration.md`
- Example config fragment: `assets/openclaw-five-agent.example.json`
