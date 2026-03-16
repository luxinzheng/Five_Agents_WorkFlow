import json

with open(r'C:\Users\Administrator\.openclaw\openclaw.json', encoding='utf-8') as f:
    cfg = json.load(f)

for a in cfg['agents']['list']:
    aid = a.get('id', '')
    sa = a.get('subagents', {}).get('allowAgents', [])
    has_sub = 'subagents' in a
    if sa:
        print(f'{aid}: allowAgents={sa}')
    else:
        print(f'{aid}: allowAgents=NONE, has_subagents_key={has_sub}')
