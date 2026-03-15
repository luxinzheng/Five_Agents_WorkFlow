#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./scripts/lib/common.sh
source "$SCRIPT_DIR/scripts/lib/common.sh"

status=0
report(){ local lvl="$1"; shift; printf '[%s] %s\n' "$lvl" "$*"; }
failmark(){ status=1; }

ensure_base

if [ -f "$CONFIG_FILE" ]; then
  report PASS "Found OpenClaw config: $CONFIG_FILE"
else
  report BLOCKER "Missing OpenClaw config: $CONFIG_FILE"
  report INFO "Run OpenClaw setup first, then re-run this doctor."
  exit 1
fi

for agent in shumiyuan duchayuan zhongshusheng shangshusheng menxiasheng; do
  if [ -d "$TARGET_ROOT/$agent" ]; then
    report PASS "Workspace present: $TARGET_ROOT/$agent"
  else
    report WARN "Workspace missing: $TARGET_ROOT/$agent"
    report INFO "Suggested fix: run bash install-lite.sh"
  fi
done

python3 - <<'PY' "$CONFIG_FILE"
import json,sys
p=sys.argv[1]
try:
    data=json.load(open(p,'r',encoding='utf-8'))
except Exception as e:
    print(f'[BLOCKER] invalid openclaw.json: {e}')
    print('[INFO] Suggested fix: restore from backup or repair JSON syntax before continuing.')
    raise SystemExit(2)
ids={a.get('id'):a for a in data.get('agents',{}).get('list',[]) if isinstance(a,dict)}
for aid in ['shumiyuan','duchayuan','zhongshusheng','shangshusheng','menxiasheng']:
    if aid in ids:
        print(f'[PASS] Agent registered: {aid}')
    else:
        print(f'[WARN] Agent missing from agents.list: {aid}')
        print('[INFO] Suggested fix: run apply-config-patch.py in dry-run, then with --write after review.')
# telegram binding
bindings=data.get('bindings',[])
tele=False
for b in bindings:
    m=b.get('match',{})
    p=m.get('peer',{})
    if b.get('agentId')=='shumiyuan' and m.get('channel')=='telegram' and p.get('kind')=='dm':
        tele=True
        break
print('[PASS] Telegram isolated binding to shumiyuan detected' if tele else '[INFO] Telegram isolated binding not detected (OK if Telegram is optional)')
# feishu binding safety
feishu_shumi=False
for b in bindings:
    m=b.get('match',{})
    if m.get('channel')=='feishu' and b.get('agentId')=='shumiyuan':
        feishu_shumi=True
        break
if feishu_shumi:
    print('[WARN] Feishu is bound to shumiyuan. Verify this was intentional.')
    print('[INFO] Risk: this may alter the existing Feishu main-channel behavior.')
else:
    print('[PASS] Feishu main-channel was not forcibly rebound to shumiyuan')
# sandbox
ss=ids.get('shangshusheng',{})
mode=((ss.get('sandbox') or {}).get('mode'))
if mode=='off':
    print('[PASS] shangshusheng sandbox.mode=off')
else:
    print(f'[WARN] shangshusheng sandbox.mode={mode}')
    print('[INFO] Suggested fix: set sandbox.mode to off unless Docker-backed sandboxing is intentionally configured.')
PY

if [ -f "$SCRIPT_DIR/templates/config/trigger-semantics.md" ]; then
  report PASS "Trigger phrase contract documented"
else
  report ERROR "Trigger phrase contract doc missing"
  report INFO "Suggested fix: restore templates/config/trigger-semantics.md from the release pack."
  failmark
fi

report INFO "Recommended smoke test: 请调研一下伊朗战争对中国房地产市场的影响，交部议。"
exit $status
