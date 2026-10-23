"""只读重放 outside03 的真实审查员启动记录；不启动 CLI，不改原始数据库。
期望来自主控 #9：SessionEnd 是唯一新增的获准钩子，原记录其它边界应保持有效。
"""
import ast
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

output = Path(sys.argv[1])
assert not output.exists(), '保留既有证据'
source = Path('evidence/2026-10-23-batch23/T-146/outside03-20261023T103723Z-98444/t137.json')
original = json.loads(source.read_text(encoding='utf-8'))
details = ast.literal_eval(original['error'].split('AssertionError: ', 1)[1])['details']
db_path = Path(original['fixture']) / 'state/state.sqlite3'
db = sqlite3.connect(db_path.as_uri() + '?mode=ro&immutable=1', uri=True)
task = json.loads(db.execute("SELECT data FROM tasks WHERE id='demo+T-1'").fetchone()[0])
# startReview binds these observed fields immediately before reviewLaunch; failure happened before save(review_started).
task['review']['launch_id'] = details['live']['runtime_identity']['launch']
task['review']['runtime_identity'] = details['live']['runtime_identity']
worker_id = task['review']['attempt']['runtime_identity']['launch']
worker = json.loads(db.execute('SELECT data FROM launch_records WHERE id=?', (worker_id,)).fetchone()[0])
db.close()
payload = dict(task=task, worker=worker, launch=details['launch'], live=details['live'])
code = """
import { A2AGates } from './workbench/src/gates/core.ts';
const { task, worker, launch, live } = JSON.parse(process.argv[1]);
const gate = { launchRecord: id => id === launch.id ? launch : id === worker.id ? worker : null,
  boundCard: () => task.card };
const result = A2AGates.prototype.reviewLaunch.call(gate, task, task.review, live);
console.log(JSON.stringify({ launch: result.id, role: result.role }));
"""
run = subprocess.run(['node', '--input-type=module', '-e', code, json.dumps(payload)], capture_output=True, text=True)
report = dict(status='PASS' if run.returncode == 0 else 'INCOMPLETE', input=str(source), database=str(db_path),
              reconstructed_binding='startReview assigns review.launch_id/runtime_identity from the recorded live observation before checking the boundary',
              scope='只读重放真实启动记录，不替代真实审查员 e2e', exit_code=run.returncode,
              stdout=run.stdout, stderr=run.stderr)
with output.open('x', encoding='utf-8') as f:
    f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
assert run.returncode == 0, report
