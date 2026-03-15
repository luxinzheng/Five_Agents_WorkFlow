# Install prompt for AI assistants

Use this prompt when you want another AI assistant to guide a user through installing this pack.

---

I want to install the **OpenClaw Wuyuan Analysis Pack** safely.

Please help me step by step with these constraints:

1. Do **not** overwrite my existing `~/.openclaw/openclaw.json` blindly.
2. Keep my **Feishu main channel unchanged** unless I explicitly ask to cut it over.
3. Treat **Telegram as optional** and only configure it as an isolated testing entrypoint to `shumiyuan` if I ask.
4. Preserve the workflow command semantics:
   - `交部议` = force the five-agent workflow
5. Prefer a conservative install path:
   - install pack
   - inspect config patch in dry-run mode
   - only then apply patch
   - run doctor checks
6. Explain each command before I run it.
7. If any step is risky, stop and ask me first.

Please walk me through:
- prerequisite checks
- pack install
- dry-run config patch
- optional Telegram isolated binding
- doctor validation
- smoke test

Recommended smoke test prompt:
`请调研一下油价上升对中国房地产市场的影响，交部议。`
