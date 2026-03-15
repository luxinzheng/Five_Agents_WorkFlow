"""Workflow engine that orchestrates the five-agent pipeline.

Implements the full workflow as specified:
- Simple tasks: A → B (audit) → user
- Complex tasks: A → C (plan) → A → D (execute) → A → E (review) → A → B (audit) → user
- Rework limits enforced at each level
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from orchestrator.models import (
    DuChaYuan,
    MenXiaSheng,
    ShangShuSheng,
    ShuMiYuan,
    ZhongShuSheng,
)
from orchestrator.schemas import (
    AgentID,
    Message,
    MessageStatus,
    Stage,
    TaskType,
    generate_task_id,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Orchestrates the five-agent workflow pipeline."""

    def __init__(self, log_dir: str | None = None):
        self.shumiyuan = ShuMiYuan()
        self.duchayuan = DuChaYuan()
        self.zhongshusheng = ZhongShuSheng()
        self.shangshusheng = ShangShuSheng()
        self.menxiasheng = MenXiaSheng()

        self.agents = {
            AgentID.A: self.shumiyuan,
            AgentID.B: self.duchayuan,
            AgentID.C: self.zhongshusheng,
            AgentID.D: self.shangshusheng,
            AgentID.E: self.menxiasheng,
        }

        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        self.message_log: list[dict] = []

        # Rework counters
        self._plan_rework_count = 0
        self._exec_rework_count = 0
        self._audit_rework_count = 0

    def _save_message(self, msg: Message) -> None:
        """Log a message to the message history and optionally to disk."""
        msg_dict = msg.to_dict()
        self.message_log.append(msg_dict)

        if self.log_dir:
            idx = len(self.message_log)
            filename = f"{idx:03d}_{msg.meta.from_agent.value}_to_{msg.meta.to_agent.value}_{msg.meta.stage.value}.json"
            filepath = self.log_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(msg_dict, f, ensure_ascii=False, indent=2)

    def run(self, user_request: str) -> dict[str, Any]:
        """Run the full workflow for a user request.

        Returns the final output payload.
        """
        task_id = generate_task_id()
        logger.info("=== 新任务 %s ===", task_id)
        logger.info("用户请求: %s", user_request)

        # Reset rework counters
        self._plan_rework_count = 0
        self._exec_rework_count = 0
        self._audit_rework_count = 0

        # Step 1: 枢密院 classify task
        task_type, reasons = self.shumiyuan.classify_task(user_request)
        logger.info("任务类型: %s, 原因: %s", task_type.value, reasons)

        if task_type == TaskType.SIMPLE:
            return self._run_simple(task_id, user_request)
        else:
            return self._run_complex(task_id, user_request, reasons)

    def _run_simple(self, task_id: str, user_request: str) -> dict[str, Any]:
        """Simple task flow: A → B → user."""
        logger.info("--- 简单任务流程 ---")

        # 枢密院 generates direct response
        response = self.shumiyuan.create_simple_response(task_id, user_request)
        self._save_message(response)

        # Submit to 都察院 for audit
        audit_result = self.duchayuan.process(response)
        self._save_message(audit_result)

        if audit_result.meta.status == MessageStatus.PASSED:
            final = self.shumiyuan.process(audit_result)
            self._save_message(final)
            return final.payload

        # First audit failed - rework once
        logger.info("都察院终审不通过，枢密院重做 1 次")
        self._audit_rework_count += 1

        reworked = self.shumiyuan.create_simple_response(task_id, user_request)
        reworked.meta.version = 2
        reworked.payload["retry_count"] = 1
        self._save_message(reworked)

        audit_result2 = self.duchayuan.process(reworked)
        self._save_message(audit_result2)

        if audit_result2.meta.status == MessageStatus.PASSED:
            final = self.shumiyuan.process(audit_result2)
            self._save_message(final)
            return final.payload

        # Still failed - stop and output
        logger.info("都察院二次终审仍不通过，停止循环")
        audit_result2.payload["retry_count"] = 1
        final = self.shumiyuan.process(audit_result2)
        self._save_message(final)
        return final.payload

    def _run_complex(self, task_id: str, user_request: str, reasons: list[str]) -> dict[str, Any]:
        """Complex task flow: A → C → A → D → A → E → A → B → user."""
        logger.info("--- 复杂任务流程 ---")

        # Step 1: Create intake and send to 中书省
        intake = self.shumiyuan.create_intake_message(task_id, user_request, TaskType.COMPLEX, reasons)
        self._save_message(intake)

        # Step 2: 中书省 generates plan
        plan = self.zhongshusheng.process(intake)
        self._save_message(plan)

        # Step 3: 枢密院 checks plan (simplified - accept if has subtasks)
        if not plan.payload.get("subtasks"):
            if self._plan_rework_count < 1:
                logger.info("计划缺失子任务，要求中书省补充 1 次")
                self._plan_rework_count += 1
                plan = self.zhongshusheng.process(intake)
                plan.meta.version = 2
                self._save_message(plan)

        # Step 4: Send plan to 尚书省 for execution
        exec_msg = self._prepare_for_execution(plan)
        self._save_message(exec_msg)

        exec_result = self.shangshusheng.process(exec_msg)
        self._save_message(exec_result)

        # Step 5: Send plan + execution result to 门下省 for review
        review_msg = self._prepare_for_review(plan, exec_result)
        review_result = self.menxiasheng.process(review_msg)
        self._save_message(review_result)

        # Step 6: Handle review result
        if review_result.meta.status == MessageStatus.FAILED:
            problem_source = review_result.payload.get("problem_source", "execution_defect")

            if problem_source == "execution_defect" and self._exec_rework_count < 1:
                logger.info("门下省审查不通过（执行缺陷），尚书省补充执行 1 次")
                self._exec_rework_count += 1
                exec_result2 = self.shangshusheng.process(exec_msg)
                exec_result2.meta.version = 2
                self._save_message(exec_result2)

                review_msg2 = self._prepare_for_review(plan, exec_result2)
                review_result = self.menxiasheng.process(review_msg2)
                self._save_message(review_result)

            elif problem_source == "plan_defect" and self._plan_rework_count < 1:
                logger.info("门下省审查不通过（计划缺陷），中书省补充计划 1 次")
                self._plan_rework_count += 1
                plan2 = self.zhongshusheng.process(intake)
                plan2.meta.version = 2
                self._save_message(plan2)

                exec_msg2 = self._prepare_for_execution(plan2)
                exec_result2 = self.shangshusheng.process(exec_msg2)
                self._save_message(exec_result2)

                review_msg2 = self._prepare_for_review(plan2, exec_result2)
                review_result = self.menxiasheng.process(review_msg2)
                self._save_message(review_result)

        # Step 7: 枢密院 forms preliminary result and submits to 都察院
        prelim = self.shumiyuan.process(review_result)
        self._save_message(prelim)

        if prelim.meta.stage == Stage.FINAL_OUTPUT:
            return prelim.payload

        # Submit to 都察院
        audit_result = self.duchayuan.process(prelim)
        self._save_message(audit_result)

        if audit_result.meta.status == MessageStatus.PASSED:
            final = self.shumiyuan.process(audit_result)
            self._save_message(final)
            return final.payload

        # Audit failed - adjust once
        if self._audit_rework_count < 1:
            logger.info("都察院终审不通过，枢密院调整 1 次")
            self._audit_rework_count += 1

            audit_result.payload["retry_count"] = 0
            adjusted = self.shumiyuan.process(audit_result)
            self._save_message(adjusted)

            if adjusted.meta.stage == Stage.FINAL_OUTPUT:
                return adjusted.payload

            audit_result2 = self.duchayuan.process(adjusted)
            self._save_message(audit_result2)

            final = self.shumiyuan.process(audit_result2)
            self._save_message(final)
            return final.payload

        # Stop
        audit_result.payload["retry_count"] = 1
        final = self.shumiyuan.process(audit_result)
        self._save_message(final)
        return final.payload

    def _prepare_for_execution(self, plan: Message) -> Message:
        """Forward plan to 尚书省 for execution."""
        from orchestrator.schemas import build_message
        return build_message(
            task_id=plan.meta.task_id,
            version=plan.meta.version,
            from_agent=AgentID.A,
            to_agent=AgentID.D,
            task_type=TaskType.COMPLEX,
            stage=Stage.EXECUTE,
            status=MessageStatus.PENDING,
            payload=plan.payload,
            attachments=plan.attachments,
        )

    def _prepare_for_review(self, plan: Message, exec_result: Message) -> Message:
        """Combine plan and execution result for 门下省 review."""
        from orchestrator.schemas import build_message
        combined_payload = {
            "plan_id": plan.payload.get("plan_id", ""),
            "execution_result_id": exec_result.payload.get("execution_result_id", ""),
            "subtasks": plan.payload.get("subtasks", []),
            "completed_subtasks": exec_result.payload.get("completed_subtasks", []),
            "result": exec_result.payload.get("result", {}),
            "unresolved_items": exec_result.payload.get("unresolved_items", []),
            "completion_criteria": plan.payload.get("completion_criteria", []),
        }
        return build_message(
            task_id=plan.meta.task_id,
            version=exec_result.meta.version,
            from_agent=AgentID.A,
            to_agent=AgentID.E,
            task_type=TaskType.COMPLEX,
            stage=Stage.REVIEW,
            status=MessageStatus.PENDING,
            payload=combined_payload,
        )

    def get_message_log(self) -> list[dict]:
        """Return the full message log."""
        return self.message_log
