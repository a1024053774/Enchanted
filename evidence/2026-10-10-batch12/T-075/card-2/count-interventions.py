"""从指定旧套件的隔离数据库只读统计缺尾注推断记录。"""
import json
from pathlib import Path
import sqlite3
import sys

folder = Path(sys.argv[1]).resolve()
checks = list(folder.glob('check-*.json'))
if len(checks) != 1:
    raise RuntimeError('必须指定仅有一份 check 收据的套件目录')
check = json.loads(checks[0].read_text(encoding='utf-8'))
states = sorted({item['state'] for item in check['trace']['artifacts']})
records = []
for state in states:
    database = Path(state) / 'state.sqlite3'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        inputs = [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs')]
        events = [(row[0], json.loads(row[1])) for row in db.execute('SELECT type,details FROM events')]
    inferred = [item for item in inputs if item.get('form') == 'action'
                and item.get('certainty') == 'inferred'
                and item.get('source_ref', {}).get('label') == '推断：缺尾注']
    ids = {item['id'] for item in inferred}
    interventions = [item for kind, item in events if kind == 'human_intervention' and item.get('input_id') in ids]
    if len(inferred) != len(interventions):
        raise AssertionError('用户输入和人工介入记录数量不一致：' + state)
    records.append({'state': state, 'action_inputs': len(inferred), 'human_interventions': len(interventions),
                    'inputs': [{'id': item['id'], 'target': item['target'], 'source_ref': item['source_ref']} for item in inferred]})
result = {'command': sys.argv, 'check': str(checks[0]), 'suite_exit': check['exit_code'],
          'action_inputs': sum(item['action_inputs'] for item in records),
          'human_interventions': sum(item['human_interventions'] for item in records), 'databases': records}
with (folder / 'inferred-interventions.json').open('x', encoding='utf-8') as out:
    json.dump(result, out, ensure_ascii=False, indent=2)
    out.write('\n')
print(json.dumps({key: result[key] for key in ('suite_exit', 'action_inputs', 'human_interventions')}, ensure_ascii=False))
