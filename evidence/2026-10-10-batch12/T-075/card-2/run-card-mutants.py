"""运行四个任务卡变异体，并从真实 CLI/Git 收据确认业务失败。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--prefix', required=True)
args = parser.parse_args()
if Path(args.prefix).name != args.prefix:
    parser.error('prefix 不能含目录')
manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
cases = {
    'path': 'test_forbidden_path_rejected',
    'trailer': 'test_foreign_middle_commit_rejected',
    'dirty': 'test_dirty_target_rejects_without_losing_staged_unstaged_or_untracked',
    'fast-forward': 'test_non_fast_forward_git_result_cannot_integrate',
}
records = []
for name, case in cases.items():
    item = next(item for item in manifest['mutants'] if item['name'] == name)
    label = args.prefix + '-mutant-' + name
    out = BASE / label
    command = [sys.executable, '-B', str(ROOT/'workbench/tests/test_task_cards_e2e.py'),
               '--gate', item['gate'], '--case', case, '--output', str(out)]
    with (BASE/(label+'.stdout.txt')).open('x') as stdout, (BASE/(label+'.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr)
    record = {'name': name, 'argv': command, 'expected_exit': 1, 'exit': result.returncode}
    with (BASE/(label+'.command.json')).open('x', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    trace = json.loads((out/'run.json').read_text(encoding='utf-8'))
    assert result.returncode == 1 and trace['failures'] > 0 and trace['errors'] == 0, record
    target_command = 'verify' if name in ('path', 'trailer') else 'integrate'
    calls = [row for row in trace['commands'] if row['argv'][0] == 'node'
             and len(row['argv']) > 4 and row['argv'][4] == target_command]
    assert calls, record
    if name in ('path', 'trailer', 'fast-forward'):
        # The mutant must accept the bad behavior through the actual gate.
        assert any(row['exit'] == 0 and json.loads(row['stdout'])['ok'] is True for row in calls), calls
        if name == 'fast-forward':
            assert any(json.loads(row['stdout']).get('task', {}).get('state') == 'accepted' for row in calls), calls
    else:
        # The dirty mutant advances the real work branch before rejecting.
        assert len(trace['artifacts']) == 3, trace['artifacts']
        for artifact in trace['artifacts']:
            repo = str(Path(artifact['root'])/'repo')
            heads = [row['stdout'].strip() for row in trace['commands']
                     if row['argv'] == ['git', '-C', repo, 'rev-parse', 'HEAD']]
            assert heads and heads[-1] != artifact['base'], (artifact, heads)
    record.update(failures=trace['failures'], errors=trace['errors'], classification='business-red')
    records.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
with (BASE/(args.prefix+'-card-mutants-summary.json')).open('x', encoding='utf-8') as f:
    json.dump({'status': 'PASS', 'scope': '四个变异体均触发业务断言失败',
               'manifest': str(args.manifest), 'candidate': manifest['head'], 'records': records},
              f, ensure_ascii=False, indent=2)
    f.write('\n')
