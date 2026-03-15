# Upgrade notes

## Round 2 upgrade goals

This release improves:
- safer config patching with backup + dry-run
- richer doctor output with suggested repairs
- install prompt for AI-guided setup
- more productized README and release docs

## Safety posture

This pack still remains conservative:
- it does not blindly replace `openclaw.json`
- it does not automatically rebind Feishu to `shumiyuan`
- Telegram remains optional
