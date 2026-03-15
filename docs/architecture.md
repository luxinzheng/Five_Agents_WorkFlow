# Architecture

This project packages a focused five-agent workflow for analysis tasks.

Reference inspiration: https://github.com/wanikua/boluobobo-ai-court-tutorial

## Roles
- `shumiyuan`: visible orchestrator and final integrator
- `zhongshusheng`: planning only
- `shangshusheng`: execution only
- `menxiasheng`: acceptance only
- `duchayuan`: final audit only

## Channel policy
- Feishu remains the main channel by default.
- Telegram is optional and should be bound narrowly to `shumiyuan` for isolated testing.
- Telegram failures should not block Feishu.

## Trigger policy
- `交部议` is the fixed trigger phrase for forced five-agent mode.

## Inter-agent communication
- Internal communication between the five agents should be JSON-formatted where practical.
- Prefer structured payloads for handoff, validation, and audit steps.
