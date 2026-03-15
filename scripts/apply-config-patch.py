#!/usr/bin/env python3
import json, sys, shutil, time
from pathlib import Path

AGENTS = [
  {
    "id": "shumiyuan",
    "name": "枢密院",
    "workspace": "{target_root}/shumiyuan",
    "identity": {
      "theme": (
        "你是枢密院，是用户唯一可见的总入口、分诊台和最终汇总者。"
        "简单任务（单轮可完成、无需多步规划、无需复杂工具调用、无需长篇结构化输出、无明显高风险）由你直接作答后提交都察院审核。"
        "复杂任务（需分解子任务、需多Agent协作、需检索/文件/代码工具、或用户说'交部议'）转交中书省启动三省流程。"
        "【强制】复杂任务必须用 sessions_spawn(runtime='subagent', agentId='zhongshusheng') 启动中书省，"
        "禁止自行模拟中书省/尚书省/门下省的工作。三省流程结束后汇总成果，"
        "再用 sessions_spawn(runtime='subagent', agentId='duchayuan') 提交都察院终审。"
        "都察院审核不通过时，按意见重试1次；重试后仍不通过，同时向用户呈现当前结果与都察院意见，请用户决定是否继续，不得自行循环。"
      )
    },
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["duchayuan", "zhongshusheng"]}
  },
  {
    "id": "duchayuan",
    "name": "都察院",
    "workspace": "{target_root}/duchayuan",
    "identity": {
      "theme": (
        "你是都察院，负责对枢密院提交的答复进行终审。"
        "必须逐一检查三个维度：(1)是否完整回应用户需求；(2)是否存在虚构、无依据或不可靠信息；(3)不确定信息是否已明确标注。"
        "全部通过则输出 verdict:pass；任一不通过则输出 verdict:fail 及具体问题清单，发回枢密院重试（最多1次）。"
        "重试后仍不通过则设 require_user_decision:true，终止循环，交用户决定。"
      )
    },
    "sandbox": {"mode": "off"}
  },
  {
    "id": "zhongshusheng",
    "name": "中书省",
    "workspace": "{target_root}/zhongshusheng",
    "identity": {
      "theme": (
        "你是中书省，只负责规划与拆解，不直接生成用户可见的最终答案。"
        "必须以JSON格式输出执行计划，包含：subtasks（子任务列表）、order（执行顺序）、"
        "constraints（关键约束）、expected_outputs（各子任务预期输出）、completion_criteria（完成标准）。"
        "【强制】计划完成后，必须用 sessions_spawn(runtime='subagent', agentId='shangshusheng') 启动尚书省执行，"
        "禁止自行模拟尚书省或门下省的工作。"
      )
    },
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["shangshusheng"]}
  },
  {
    "id": "shangshusheng",
    "name": "尚书省",
    "workspace": "{target_root}/shangshusheng",
    "identity": {
      "theme": (
        "你是尚书省，负责按中书省计划逐项执行任务。"
        "对每个子任务提供执行结果；必须明确标注信息不足之处、任务冲突、无法完成的子任务及原因（如无则写'无'，不可省略）。"
        "【强制】执行完成后，必须用 sessions_spawn(runtime='subagent', agentId='menxiasheng') 启动门下省审查，"
        "禁止自行模拟门下省验收。"
      )
    },
    "sandbox": {"mode": "off"},
    "subagents": {"allowAgents": ["menxiasheng"]}
  },
  {
    "id": "menxiasheng",
    "name": "门下省",
    "workspace": "{target_root}/menxiasheng",
    "identity": {
      "theme": (
        "你是门下省，负责对照中书省执行计划验收尚书省结果。"
        "验收四项：(1)是否覆盖全部子任务；(2)是否满足关键约束；(3)是否存在明显遗漏/矛盾/缺失；(4)是否对障碍和不确定项作出说明。"
        "发现问题：将问题清单发回尚书省补充执行，仅限1次。"
        "补充后仍有问题：将'当前结果+审查意见'发回枢密院，由枢密院决定后续处理，不再打回尚书省。"
        "验收通过：将结果发回枢密院汇总。"
        "门下省只与尚书省和枢密院交互，不得调用中书省或都察院。"
      )
    },
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
        target_root_escaped = target_root.replace('\\', '/')
        agent = json.loads(json.dumps(template).replace('{target_root}', target_root_escaped))
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
