"""Data models and enums for the five-agent workflow system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AgentID(str, Enum):
    A = "A"  # 枢密院
    B = "B"  # 都察院
    C = "C"  # 中书省
    D = "D"  # 尚书省
    E = "E"  # 门下省


AGENT_NAMES = {
    AgentID.A: "枢密院",
    AgentID.B: "都察院",
    AgentID.C: "中书省",
    AgentID.D: "尚书省",
    AgentID.E: "门下省",
}


class TaskType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class Stage(str, Enum):
    INTAKE = "intake"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    FINAL_AUDIT = "final_audit"
    FINAL_OUTPUT = "final_output"
    REWORK = "rework"


class MessageStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REWORK = "needs_rework"
    BLOCKED = "blocked"
    FINALIZED = "finalized"


class IssueType(str, Enum):
    MISSING_INFORMATION = "missing_information"
    MISSING_SUBTASK = "missing_subtask"
    CONSTRAINT_VIOLATION = "constraint_violation"
    LOGIC_CONFLICT = "logic_conflict"
    FORMAT_ERROR = "format_error"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    HALLUCINATION_RISK = "hallucination_risk"
    UNCERTAINTY_NOT_MARKED = "uncertainty_not_marked"
    EXECUTION_INCOMPLETE = "execution_incomplete"
    PLAN_DEFECT = "plan_defect"
    USER_REQUEST_NOT_FULLY_ADDRESSED = "user_request_not_fully_addressed"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Issue:
    issue_id: str
    type: IssueType
    severity: IssueSeverity
    description: str
    location: str = ""
    action_required: str = ""

    def to_dict(self) -> dict:
        d = {
            "issue_id": self.issue_id,
            "type": self.type.value,
            "severity": self.severity.value,
            "description": self.description,
        }
        if self.location:
            d["location"] = self.location
        if self.action_required:
            d["action_required"] = self.action_required
        return d


@dataclass
class Attachment:
    type: str
    ref_id: str

    def to_dict(self) -> dict:
        return {"type": self.type, "ref_id": self.ref_id}


@dataclass
class Meta:
    task_id: str
    message_id: str
    version: int
    from_agent: AgentID
    to_agent: AgentID
    timestamp: str
    task_type: TaskType
    stage: Stage
    status: MessageStatus

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "message_id": self.message_id,
            "version": self.version,
            "from_agent": self.from_agent.value,
            "to_agent": self.to_agent.value,
            "timestamp": self.timestamp,
            "task_type": self.task_type.value,
            "stage": self.stage.value,
            "status": self.status.value,
        }


@dataclass
class Message:
    meta: Meta
    payload: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "meta": self.meta.to_dict(),
            "payload": self.payload,
            "notes": self.notes,
            "issues": [i.to_dict() for i in self.issues],
            "attachments": [a.to_dict() for a in self.attachments],
        }


def generate_task_id() -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_id = uuid.uuid4().hex[:6].upper()
    return f"TASK-{date_str}-{short_id}"


def generate_message_id() -> str:
    return f"MSG-{uuid.uuid4().hex[:8].upper()}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_message(
    task_id: str,
    version: int,
    from_agent: AgentID,
    to_agent: AgentID,
    task_type: TaskType,
    stage: Stage,
    status: MessageStatus,
    payload: dict[str, Any],
    notes: list[str] | None = None,
    issues: list[Issue] | None = None,
    attachments: list[Attachment] | None = None,
) -> Message:
    """Factory function to create a properly structured Message."""
    meta = Meta(
        task_id=task_id,
        message_id=generate_message_id(),
        version=version,
        from_agent=from_agent,
        to_agent=to_agent,
        timestamp=now_iso(),
        task_type=task_type,
        stage=stage,
        status=status,
    )
    return Message(
        meta=meta,
        payload=payload,
        notes=notes or [],
        issues=issues or [],
        attachments=attachments or [],
    )
