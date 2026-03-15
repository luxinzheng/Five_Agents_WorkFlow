"""CLI entry point for the five-agent workflow orchestrator."""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
from pathlib import Path

from orchestrator.engine import WorkflowEngine


def main() -> None:
    # Ensure stdout handles UTF-8 on Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="五院制工作流引擎 (Five-Agent Workflow Engine)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python -m orchestrator.cli "今天天气怎么样"
  python -m orchestrator.cli "交部议 分析油价对房地产的影响"
  python -m orchestrator.cli --log-dir ./logs "交部议 调研AI发展趋势"
""",
    )
    parser.add_argument("request", help="用户请求文本")
    parser.add_argument(
        "--log-dir",
        default="./logs",
        help="保存 Agent 间 JSON 消息的目录 (默认: ./logs)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志输出",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="以 JSON 格式输出最终结果",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    engine = WorkflowEngine(log_dir=args.log_dir)

    print(f"\n{'='*60}")
    print(f"  五院制工作流引擎")
    print(f"{'='*60}")
    print(f"  用户请求: {args.request}")
    print(f"  日志目录: {args.log_dir}")
    print(f"{'='*60}\n")

    result = engine.run(args.request)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_result(result)

    msg_count = len(engine.get_message_log())
    print(f"\n{'='*60}")
    print(f"  流程完成，共交换 {msg_count} 条 Agent 间消息")
    print(f"  消息日志已保存到: {args.log_dir}/")
    print(f"{'='*60}\n")


def _print_result(result: dict) -> None:
    """Pretty-print the final result."""
    output_mode = result.get("output_mode", "unknown")

    if output_mode == "normal_pass":
        print("【最终结果 - 正常通过】\n")
        print(result.get("final_answer", "（无内容）"))
        audit = result.get("audit_summary", "")
        if audit:
            print(f"\n审查摘要: {audit}")

    elif output_mode == "rework_pass":
        print("【最终结果 - 返工后通过】\n")
        print(result.get("final_answer", "（无内容）"))
        print(f"\n修改说明: {result.get('modification_notes', '')}")
        print(f"风险与限制: {result.get('risks_and_limits', '')}")

    elif output_mode == "stopped":
        print("【最终结果 - 自动循环已停止】\n")
        print("当前最佳结果:")
        print(result.get("current_best_result", "（无内容）"))

        issues = result.get("unresolved_issues", [])
        if issues:
            print("\n未解决的问题:")
            for issue in issues:
                if isinstance(issue, dict):
                    print(f"  - [{issue.get('type', '')}] {issue.get('description', '')}")
                else:
                    print(f"  - {issue}")

        print(f"\n审查意见: {result.get('audit_summary', '')}")

        actions = result.get("user_action_needed", [])
        if actions:
            print("\n需要用户补充:")
            for action in actions:
                print(f"  - {action}")

        recommend = result.get("recommend_continue", None)
        if recommend is not None:
            print(f"\n建议继续执行: {'是' if recommend else '否'}")

    else:
        print("【最终结果】\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
