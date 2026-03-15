#!/usr/bin/env python3
import json, sys, shutil, time
from pathlib import Path

AGENTS = [
  {
    "id": "shumiyuan",
    "name": "枢密院",
    "workspace": "{target_root}/shumiyuan",
    "identity": {"theme": "你是枢密院，是用户唯一可见的总入口、分诊台和最终汇总者。用户说‘交部议’时，强制启动五院制分析流程。"},
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["duchayuan", "zhongshusheng", "shangshusheng", "menxiasheng"]}
  },
  {
    "id": "duchayuan",
    "name": "都察院",
    "workspace": "{target_root}/duchayuan",
    "identity": {"theme": "你是都察院，负责最终审核，只输出通过/不通过。"},
    "sandbox": {"mode": "off"}
  },
  {
    "id": "zhongshusheng",
    "name": "中书省",
    "workspace": "{target_root}/zhongshusheng",
    "identity": {"theme": "你是中书省，只负责规划与拆解，不直接写最终答案。"},
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["shangshusheng"]}
  },
  {
    "id": "shangshusheng",
    "name": "尚书省",
    "workspace": "{target_root}/shangshusheng",
    "identity": {"theme": "你是尚书省，负责按中书省计划执行。"},
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["menxiasheng"]}
  },
  {
    "id": "menxiasheng",
    "name": "门下省",
    "workspace": "{target_root}/menxiasheng",
    "identity": {"theme": "你是门下省，负责验收尚书省执行结果。"},
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["shangshusheng"]}
  }
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

def upsert_agents(data, target_root):
    agents = data.setdefault('agents', {})
    lst = agents.setdefault('list', [])
    by_id = {a.get('id'): a for a in lst if isinstance(a, dict)}
    changed = False
    for template in AGENTS:
        agent = json.loads(json.dumps(template).replace('{target_root}', target_root))
        aid = agent['id']
        if aid not in by_id:
            lst.append(agent)
            changed = True
        else:
            existing = by_id[aid]
            # conservative patch: only ensure workspace, sandbox.off, identity exists, and allowAgents exists
            for k in ['name', 'workspace', 'identity', 'sandbox', 'subagents']:
                if k not in existing and k in agent:
                    existing[k] = agent[k]
                    changed = True
            if existing.get('id') == 'shangshusheng':
                if ((existing.get('sandbox') or {}).get('mode')) != 'off':
                    existing['sandbox'] = {'mode': 'off'}
                    changed = True
    return changed

def maybe_add_telegram_binding(data, telegram_peer_id):
    if not telegram_peer_id:
        return False
    bindings = data.setdefault('bindings', [])
    for b in bindings:
        m = b.get('match', {})
        p = m.get('peer', {})
        if b.get('agentId') == 'shumiyuan' and m.get('channel') == 'telegram' and p.get('kind') == 'dm' and str(p.get('id')) == str(telegram_peer_id):
            return False
    bindings.append({
      'agentId': 'shumiyuan',
      'match': {'channel': 'telegram', 'peer': {'kind': 'dm', 'id': str(telegram_peer_id)}}
    })
    return True

def main():
    if len(sys.argv) < 2:
        print('usage: apply-config-patch.py <openclaw.json> [target_root] [telegram_dm_id|empty] [--write]')
        sys.exit(2)
    cfg = Path(sys.argv[1]).expanduser()
    target_root = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / '.openclaw' / 'workspace-five-agent')
    telegram_peer_id = None if len(sys.argv) < 4 or sys.argv[3] in ('', '-', 'none', 'null') else sys.argv[3]
    write = '--write' in sys.argv
    data = load_json(cfg)
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    upsert_agents(data, target_root)
    maybe_add_telegram_binding(data, telegram_peer_id)
    after = json.dumps(data, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if not changed:
        print('No changes needed.')
        return
    if not write:
        print('Dry run: changes detected. Re-run with --write to apply.')
        return
    backup = cfg.with_name(cfg.name + f'.wuyuan-backup-{int(time.time())}')
    shutil.copy2(cfg, backup)
    save_json(cfg, data)
    print(f'Patched config written: {cfg}')
    print(f'Backup created: {backup}')

if __name__ == '__main__':
    main()
