#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./scripts/lib/common.sh
source "$SCRIPT_DIR/scripts/lib/common.sh"

msg "== Wuyuan Analysis Pack: lite install =="
ensure_base
backup_config
copy_workspace_templates
openclaw plugins install "$SCRIPT_DIR" || true

msg ""
msg "Lite install dry-run patch preview ..."
python3 "$SCRIPT_DIR/scripts/apply-config-patch.py" "$CONFIG_FILE" "$TARGET_ROOT" "${WUYUAN_TELEGRAM_DM_ID:-}" || true

msg ""
msg "Lite install complete. What it did:"
msg "- Installed the bundled skill/plugin pack"
msg "- Created five agent workspace templates"
msg "- Previewed a safe patch for openclaw.json"
msg "- Did NOT modify Feishu main-channel bindings"
msg "- Did NOT auto-enable Telegram unless explicitly requested"
msg ""
msg "If the patch preview looks right, apply it with:"
msg "python3 $SCRIPT_DIR/scripts/apply-config-patch.py $CONFIG_FILE $TARGET_ROOT ${WUYUAN_TELEGRAM_DM_ID:-none} --write"
msg ""
msg "Then run: bash doctor.sh"
