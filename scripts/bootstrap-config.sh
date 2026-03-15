#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

ensure_base
backup_config
copy_workspace_templates

msg "Workspace templates copied to: $TARGET_ROOT"
msg "Next: merge templates/openclaw-five-agent.example.json into $CONFIG_FILE carefully."
msg "Telegram should remain optional; Feishu main channel should stay unchanged by default."
