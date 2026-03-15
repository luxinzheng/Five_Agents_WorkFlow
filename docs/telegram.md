# Telegram isolated entry

Telegram is optional in this pack.

## Goal
Use Telegram as a narrow, isolated testing entrypoint for `shumiyuan` without disturbing Feishu.

## Rule
- Do not enable Telegram by default.
- If enabled, bind only the chosen Telegram DM/test peer to `shumiyuan`.
- Keep Feishu routing unchanged.

## Template
See `templates/config/telegram-binding.example.json`.
