# FAQ

## Why not auto-overwrite my OpenClaw config?
Because this pack is designed to be safe for existing OpenClaw users, especially those already running Feishu in production.

## Why is Telegram optional?
Because this release treats Telegram as a test entrypoint, not a mandatory dependency.

## Why hard-code `交部议` as a fixed phrase?
To avoid prompt drift and keep the workflow trigger deterministic.
