"""
fix-allow-agents.py
修正 openclaw.json 中 allowAgents 配置：
- 枢密院：["duchayuan", "zhongshusheng", "shangshusheng", "menxiasheng"]
- 其余各院：移除 allowAgents（depth=1 不能 spawn）
"""
import json

CONFIG_PATH = r'C:\Users\Administrator\.openclaw\openclaw.json'

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

for agent in cfg['agents']['list']:
    aid = agent.get('id', '')
    if aid == 'shumiyuan':
        agent['subagents'] = {
            'allowAgents': ['duchayuan', 'zhongshusheng', 'shangshusheng', 'menxiasheng']
        }
        print(f'[OK] {aid} allowAgents -> array of 4')
    elif aid in ('duchayuan', 'zhongshusheng', 'shangshusheng', 'menxiasheng'):
        if 'subagents' in agent:
            agent.pop('subagents')
        print(f'[OK] {aid} allowAgents -> removed')

with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('Done.')
