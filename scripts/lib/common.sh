#!/usr/bin/env bash
set -euo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_DIR="${OPENCLAW_DIR:-$HOME/.openclaw}"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
BACKUP_DIR="$OPENCLAW_DIR/backups/wuyuan-analysis"
TARGET_ROOT="${WUYUAN_TARGET_ROOT:-$OPENCLAW_DIR/workspace-five-agent}"

msg() { printf '%s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "$1 not found in PATH"; }

ensure_base() {
  need_cmd openclaw
  need_cmd python3
  mkdir -p "$OPENCLAW_DIR" "$BACKUP_DIR"
}

backup_config() {
  if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$BACKUP_DIR/openclaw.$(date +%Y%m%d-%H%M%S).json.bak"
  fi
}

copy_workspace_templates() {
  mkdir -p "$TARGET_ROOT"
  for agent in shumiyuan duchayuan zhongshusheng shangshusheng menxiasheng; do
    mkdir -p "$TARGET_ROOT/$agent"
    cp -R "$PACK_DIR/templates/workspaces/$agent/." "$TARGET_ROOT/$agent/" 2>/dev/null || true
    mkdir -p "$TARGET_ROOT/$agent/memory"
  done
}
