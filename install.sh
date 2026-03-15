#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./scripts/lib/common.sh
source "$SCRIPT_DIR/scripts/lib/common.sh"

msg "== Wuyuan Analysis Pack: full install =="
ensure_base
backup_config
copy_workspace_templates
openclaw plugins install "$SCRIPT_DIR" || true

msg ""
msg "Running conservative config patch dry-run ..."
python3 "$SCRIPT_DIR/scripts/apply-config-patch.py" "$CONFIG_FILE" "$TARGET_ROOT" "${WUYUAN_TELEGRAM_DM_ID:-}" || true

msg ""
msg "Full install prepared these pieces:"
msg "- bundled wuyuan-analysis skill/plugin"
msg "- five workspace templates under $TARGET_ROOT"
msg "- a safe config patch helper with backup + dry-run"
msg ""
msg "To APPLY the patch after review:"
msg "python3 $SCRIPT_DIR/scripts/apply-config-patch.py $CONFIG_FILE $TARGET_ROOT ${WUYUAN_TELEGRAM_DM_ID:-none} --write"
msg ""
msg "Safety rules of this installer:"
msg "- does NOT overwrite your existing Feishu main-channel routing"
msg "- does NOT auto-enable Telegram unless you pass WUYUAN_TELEGRAM_DM_ID"
msg "- does NOT inject real credentials"
msg ""
msg "Recommended next steps:"
msg "1. Read README.md and docs/install-prompt.md"
msg "2. Review the dry-run result"
msg "3. Apply patch only if it looks correct"
msg "4. Run: bash doctor.sh"
