"""Agent models for the five-agent workflow system.

Each agent implements a `process` method that takes a Message and returns a Message.
The actual intelligence comes from an LLM backend; these classes manage the workflow
protocol, enforce role boundaries, and validate inputs/outputs.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from orchestrator.schemas import (
    AGENT_NAMES,
    AgentID,
    Attachment,
    Issue,
    IssueSeverity,
    IssueType,
    Message,
    MessageStatus,
    Stage,
    TaskType,
    build_message,
)

logger = logging.getLogger(__name__)


class AgentBase(ABC):
    """Abstract base class for all agents."""

    agent_id: AgentID

    @property
    def name(self) -> str:
        return AGENT_NAMES[self.agent_id]

    @abstractmethod
    def process(self, incoming: Message) -> Message:
        """Process an incoming message and produce an outgoing message."""
        ...

    def _log(self, action: str, detail: str = "") -> None:
        logger.info("[%s/%s] %s %s", self.agent_id.value, self.name, action, detail)


class ShuMiYuan(AgentBase):
    """Agent A: 枢密院 — Central controller, router, integrator."""

    agent_id = AgentID.A

    COMPLEX_KEYWORDS = ["交部议"]
    COMPLEX_INDICATORS = [
        "多个", "子任务", "分析", "比较", "汇总", "调研", "审查",
        "改写", "规划", "多步", "文件处理", "报告",
    ]

    def classify_task(self, user_request: str) -> tuple[TaskType, list[str]]:
        """Determine if a task is simple or complex."""
        reasons: list[str] = []

        for kw in self.COMPLEX_KEYWORDS:
            if kw in user_request:
                reasons.append(f"用户明确要求「{kw}」")

        indicator_count = sum(1 for ind in self.COMPLEX_INDICATORS if ind in user_request)
        if indicator_count >= 2:
            reasons.append(f"任务包含多个复杂指标（{indicator_count}项）")

        if len(user_request) > 200:
            reasons.append("任务描述较长，可能包含多个子目标")

        task_type = TaskType.COMPLEX if reasons else TaskType.SIMPLE
        return task_type, reasons

    def create_intake_message(
        self, task_id: str, user_request: str, task_type: TaskType, reasons: list[str]
    ) -> Message:
        """Create the initial intake message for routing."""
        to_agent = AgentID.C if task_type == TaskType.COMPLEX else AgentID.B
        constraints = []
        if "正式" in user_request or "格式" in user_request:
            constraints.append("格式需正式")
        constraints.append("避免虚构")
        constraints.append("对不确定信息明确标注")

        return build_message(
            task_id=task_id,
            version=1,
            from_agent=AgentID.A,
            to_agent=to_agent,
            task_type=task_type,
            stage=Stage.INTAKE,
            status=MessageStatus.PENDING,
            payload={
                "user_request": user_request,
                "normalized_request": user_request.replace("交部议", "").strip(),
                "routing_decision": {
                    "is_complex": task_type == TaskType.COMPLEX,
                    "reason": reasons if reasons else ["单轮可完成的简单任务"],
                },
                "user_constraints": constraints,
                "expected_output": "结构化分析结果" if task_type == TaskType.COMPLEX else "直接回复",
            },
        )

    def create_simple_response(self, task_id: str, user_request: str) -> Message:
        """Generate a direct response for simple tasks."""
        self._log("直接处理简单任务")
        return build_message(
            task_id=task_id,
            version=1,
            from_agent=AgentID.A,
            to_agent=AgentID.B,
            task_type=TaskType.SIMPLE,
            stage=Stage.FINAL_AUDIT,
            status=MessageStatus.PENDING,
            payload={
                "task_summary": user_request,
                "result": f"[枢密院直接回复] 针对用户请求「{user_request}」的回答：\n\n"
                          f"（此处为枢密院生成的直接回复内容。在实际运行中，"
                          f"此内容由 LLM 根据用户请求生成。）",
                "retry_count": 0,
                "max_retries": 1,
            },
        )

    def process(self, incoming: Message) -> Message:
        """Process messages returning to 枢密院 from other agents."""
        stage = incoming.meta.stage
        status = incoming.meta.status
        self._log(f"收到来自 {incoming.meta.from_agent.value} 的消息", f"stage={stage.value} status={status.value}")

        if stage == Stage.FINAL_AUDIT and status == MessageStatus.PASSED:
            return build_message(
                task_id=incoming.meta.task_id,
                version=incoming.meta.version,
                from_agent=AgentID.A,
                to_agent=AgentID.A,
                task_type=incoming.meta.task_type,
                stage=Stage.FINAL_OUTPUT,
                status=MessageStatus.FINALIZED,
                payload={
                    "output_mode": "normal_pass",
                    "final_answer": incoming.payload.get("result", ""),
                    "audit_summary": incoming.payload.get("summary", ""),
                },
            )

        if stage == Stage.FINAL_AUDIT and status == MessageStatus.NEEDS_REWORK:
            retry_count = incoming.payload.get("retry_count", 0)
            if retry_count >= 1:
                return build_message(
                    task_id=incoming.meta.task_id,
                    version=incoming.meta.version + 1,
                    from_agent=AgentID.A,
                    to_agent=AgentID.A,
                    task_type=incoming.meta.task_type,
                    stage=Stage.FINAL_OUTPUT,
                    status=MessageStatus.FINALIZED,
                    payload={
                        "output_mode": "stopped",
                        "current_best_result": incoming.payload.get("result", ""),
                        "unresolved_issues": [i.to_dict() for i in incoming.issues] if incoming.issues else [],
                        "audit_summary": incoming.payload.get("summary", ""),
                        "user_action_needed": incoming.payload.get("required_actions", []),
                        "recommend_continue": False,
                    },
                )

        if stage == Stage.REVIEW and status == MessageStatus.PASSED:
            self._log("门下省审查通过，提交都察院终审")
            return build_message(
                task_id=incoming.meta.task_id,
                version=incoming.meta.version,
                from_agent=AgentID.A,
                to_agent=AgentID.B,
                task_type=incoming.meta.task_type,
                stage=Stage.FINAL_AUDIT,
                status=MessageStatus.PENDING,
                payload=incoming.payload,
                attachments=incoming.attachments,
            )

        if stage == Stage.REVIEW and status == MessageStatus.FAILED:
            problem_source = incoming.payload.get("problem_source", "execution_defect")
            rework_target = AgentID.D if problem_source == "execution_defect" else AgentID.C
            self._log(f"门下省审查不通过，发回 {rework_target.value}")
            return build_message(
                task_id=incoming.meta.task_id,
                version=incoming.meta.version + 1,
                from_agent=AgentID.A,
                to_agent=rework_target,
                task_type=incoming.meta.task_type,
                stage=Stage.REWORK,
                status=MessageStatus.NEEDS_REWORK,
                payload=incoming.payload,
                issues=incoming.issues,
            )

        return incoming


class DuChaYuan(AgentBase):
    """Agent B: 都察院 — Final quality auditor."""

    agent_id = AgentID.B

    def process(self, incoming: Message) -> Message:
        """Perform final audit on the result."""
        self._log("开始终审")
        raw_result = incoming.payload.get("result", "")
        if isinstance(raw_result, dict):
            result_text = raw_result.get("content", "")
        else:
            result_text = str(raw_result) if raw_result else ""
        issues: list[Issue] = []

        if not result_text or result_text.strip() == "":
            issues.append(Issue(
                issue_id="ISSUE-AUD-001",
                type=IssueType.USER_REQUEST_NOT_FULLY_ADDRESSED,
                severity=IssueSeverity.HIGH,
                description="答复内容为空，未回应用户需求。",
                action_required="生成完整答复",
            ))

        if "虚构" in result_text or "假设" in result_text:
            issues.append(Issue(
                issue_id="ISSUE-AUD-002",
                type=IssueType.HALLUCINATION_RISK,
                severity=IssueSeverity.MEDIUM,
                description="答复中可能包含虚构或未验证的内容。",
                action_required="验证相关信息并标注不确定性",
            ))

        audit_decision = "passed" if not issues else "needs_rework"
        retry_count = incoming.payload.get("retry_count", 0)

        status = MessageStatus.PASSED if not issues else MessageStatus.NEEDS_REWORK

        return build_message(
            task_id=incoming.meta.task_id,
            version=incoming.meta.version,
            from_agent=AgentID.B,
            to_agent=AgentID.A,
            task_type=incoming.meta.task_type,
            stage=Stage.FINAL_AUDIT,
            status=status,
            payload={
                "audit_id": f"AUD-{incoming.meta.task_id}",
                "audit_decision": audit_decision,
                "audit_scope": [
                    "用户需求响应情况",
                    "真实性与依据充分性",
                    "不确定项标注情况",
                    "最终可交付性",
                ],
                "summary": "终审通过，内容可交付用户。" if not issues else "终审发现问题，需要修正。",
                "required_actions": [i.action_required for i in issues if i.action_required],
                "result": incoming.payload.get("result", ""),
                "retry_count": retry_count,
            },
            issues=issues,
        )


class ZhongShuSheng(AgentBase):
    """Agent C: 中书省 — Planning agent for complex tasks."""

    agent_id = AgentID.C

    def process(self, incoming: Message) -> Message:
        """Generate an execution plan from the task description."""
        self._log("开始规划")
        user_request = incoming.payload.get("normalized_request", incoming.payload.get("user_request", ""))
        constraints = incoming.payload.get("user_constraints", [])

        plan_id = f"PLAN-{incoming.meta.task_id}"

        subtasks = [
            {"subtask_id": "ST-001", "name": "需求分析", "description": f"分析用户核心需求：{user_request}"},
            {"subtask_id": "ST-002", "name": "信息收集", "description": "收集相关信息与数据"},
            {"subtask_id": "ST-003", "name": "分析执行", "description": "根据收集的信息进行分析"},
            {"subtask_id": "ST-004", "name": "结果整合", "description": "整合分析结果，形成结构化输出"},
        ]

        return build_message(
            task_id=incoming.meta.task_id,
            version=incoming.meta.version,
            from_agent=AgentID.C,
            to_agent=AgentID.A,
            task_type=TaskType.COMPLEX,
            stage=Stage.PLAN,
            status=MessageStatus.PENDING,
            payload={
                "plan_id": plan_id,
                "objective": f"完成用户请求的结构化分析：{user_request}",
                "subtasks": subtasks,
                "execution_order": ["ST-001", "ST-002", "ST-003", "ST-004"],
                "constraints": constraints + ["必须避免虚构", "不确定信息需标注"],
                "expected_output_schema": {
                    "type": "document",
                    "sections": ["需求分析", "信息收集", "分析结论", "局限与不确定性"],
                },
                "completion_criteria": [
                    "覆盖全部子任务",
                    "满足用户约束",
                    "不确定信息已标注",
                    "输出结构清晰",
                ],
                "risks": [
                    "信息不足可能导致分析不完整",
                    "部分结论可能需要进一步验证",
                ],
            },
            notes=["规划基于当前可用信息生成，执行阶段可能需要调整。"],
        )


class ShangShuSheng(AgentBase):
    """Agent D: 尚书省 — Execution agent."""

    agent_id = AgentID.D

    def process(self, incoming: Message) -> Message:
        """Execute the plan from 中书省."""
        self._log("开始执行")
        plan_id = incoming.payload.get("plan_id", "")
        subtasks = incoming.payload.get("subtasks", [])

        completed = []
        results: dict[str, str] = {}
        unresolved: list[dict[str, str]] = []

        for st in subtasks:
            st_id = st.get("subtask_id", "")
            st_name = st.get("name", "")
            completed.append(st_id)
            results[st_id] = f"[尚书省执行结果] {st_name}：（LLM 生成的执行结果占位）"

        exec_id = f"EXEC-{incoming.meta.task_id}"

        return build_message(
            task_id=incoming.meta.task_id,
            version=incoming.meta.version,
            from_agent=AgentID.D,
            to_agent=AgentID.A,
            task_type=TaskType.COMPLEX,
            stage=Stage.EXECUTE,
            status=MessageStatus.PENDING,
            payload={
                "plan_id": plan_id,
                "execution_result_id": exec_id,
                "completed_subtasks": completed,
                "result": {
                    "content": json.dumps(results, ensure_ascii=False, indent=2),
                },
                "unresolved_items": unresolved,
            },
            notes=["已按计划完成全部子任务。"],
            attachments=[Attachment(type="plan_reference", ref_id=plan_id)],
        )


class MenXiaSheng(AgentBase):
    """Agent E: 门下省 — Process review agent."""

    agent_id = AgentID.E

    def process(self, incoming: Message) -> Message:
        """Review execution results against the plan."""
        self._log("开始过程审查")

        plan_id = incoming.payload.get("plan_id", "")
        exec_id = incoming.payload.get("execution_result_id", "")
        completed = incoming.payload.get("completed_subtasks", [])
        unresolved = incoming.payload.get("unresolved_items", [])

        issues: list[Issue] = []

        if unresolved:
            for item in unresolved:
                issues.append(Issue(
                    issue_id=f"ISSUE-REV-{item.get('item_id', 'UNK')}",
                    type=IssueType.EXECUTION_INCOMPLETE,
                    severity=IssueSeverity.MEDIUM,
                    description=item.get("description", "未解决项"),
                ))

        review_decision = "passed" if not issues else "failed"
        problem_source = "none" if not issues else "execution_defect"
        rework_target = None if not issues else "D"

        status = MessageStatus.PASSED if not issues else MessageStatus.FAILED

        return build_message(
            task_id=incoming.meta.task_id,
            version=incoming.meta.version,
            from_agent=AgentID.E,
            to_agent=AgentID.A,
            task_type=incoming.meta.task_type,
            stage=Stage.REVIEW,
            status=status,
            payload={
                "review_id": f"REV-{incoming.meta.task_id}",
                "plan_id": plan_id,
                "execution_result_id": exec_id,
                "review_decision": review_decision,
                "review_scope": [
                    "子任务覆盖",
                    "关键约束满足情况",
                    "遗漏与矛盾检查",
                    "不确定项说明",
                ],
                "summary": "执行结果覆盖全部子任务，符合计划要求。" if not issues else "存在问题，需补充执行。",
                "problem_source": problem_source,
                "rework_target": rework_target,
                "result": incoming.payload.get("result", {}),
            },
            issues=issues,
            attachments=[
                Attachment(type="plan_reference", ref_id=plan_id),
                Attachment(type="execution_reference", ref_id=exec_id),
            ],
        )
