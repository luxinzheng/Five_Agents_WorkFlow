#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v openclaw >/dev/null 2>&1; then
  echo "openclaw not found in PATH"
  exit 1
fi

echo "Installing OpenClaw plugin from: $REPO_DIR"
openclaw plugins install "$REPO_DIR"

echo
echo "Done. Next checks:"
echo "  openclaw plugins list"
echo "  openclaw skills list"
echo
echo "If you want the full five-agent setup, adapt:"
echo "  $REPO_DIR/templates/openclaw-five-agent.example.json"
