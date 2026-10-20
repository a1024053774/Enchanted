"""Herdr 期启动脚本透传；使用既有显式 CLI/Herdr 进程夹具，不调用模型。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--summary', required=True, type=Path)
a = p.parse_args()
assert not a.summary.exists()
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'):
    os.environ.pop(key, None)
os.environ['LC_ALL'] = 'C'
sys.path.insert(0, str(root / 'scripts'))
spec = importlib.util.spec_from_file_location('t094_fixture', root / 'scripts/test_launch_worker_failure.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
fixture = module.LaunchFailure(); fixture.setUp()
command = [sys.executable, str(root / 'scripts/launch-worker'), '--root', str(fixture.root), '--cwd', str(fixture.root),
           '--agent', 'fixture-worker', '--project', 'fixture', '--task', 'T-112', '--attempt', 'a1', '--session', 'fixture-session',
           '--model', 'model-sentinel', '--effort', 'future-effort-sentinel']
result = subprocess.run(command, env=dict(fixture.env, T094_SCENARIO='success'), capture_output=True, text=True, timeout=20)
report = dict(status='INCOMPLETE', command=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
              fixture=str(fixture.root), model_calls=0, scope='launch-worker real Python entry with supplied native CLI/Herdr processes')
if result.returncode == 0:
    rows = [json.loads(line) for line in (fixture.root / 'records/launches.jsonl').read_text().splitlines()]
    if all(row['model'] == 'model-sentinel' and row['effort'] == 'future-effort-sentinel'
           and row['argv'][row['argv'].index('-m') + 1] == 'model-sentinel'
           and 'model_reasoning_effort="future-effort-sentinel"' in row['argv'] for row in rows):
        report['status'] = 'PASS'
a.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'summary': str(a.summary)}))
if report['status'] == 'PASS':
    fixture.doCleanups()
else:
    fixture.temp._finalizer.detach()
raise SystemExit(0 if report['status'] == 'PASS' else 1)
