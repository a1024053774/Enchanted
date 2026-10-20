"""Recheck the merged branch, then run T-110 and T-112 real no-model entries."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback
import uuid

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--electron-dist', type=Path, required=True)
parser.add_argument('--summary', type=Path, required=True)
parser.add_argument('--run-id', default='01')
args = parser.parse_args()
assert len(args.run_id) == 2 and args.run_id.isdigit(), 'Use a two-digit fresh run ID'
source, summary = args.source.resolve(), args.summary.resolve()
assert not summary.exists()
evidence = summary.parent
env = {key: value for key, value in os.environ.items()
       if key not in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE')}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
report = dict(status='INCOMPLETE', source=str(source), commands=[], checks=[], cleanup=[])
def run(argv, timeout=600):
    command = list(map(str, argv))
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=timeout)
    report['commands'].append(dict(argv=command, exit=result.returncode, stdout=result.stdout[-3000:], stderr=result.stderr[-3000:]))
    assert result.returncode == 0, report['commands'][-1]
    return result.stdout

def clean_question_fixtures(result):
    paths = [result['retained_fixture']]
    paths += [case['fixture'] for key in ('failure_cases', 'answer_lifecycle_cases') for case in result[key]]
    for value in paths:
        path = Path(value)
        assert path.parent == Path('/private/tmp') and path.name.startswith(('t108-question-contract-', 't108-hook-failure-', 't108-answer-lifecycle-'))
        assert not path.is_symlink()
        shutil.rmtree(path)
        report['cleanup'].append(dict(path=value, removed=not path.exists(), scope='finished contract fixture explicitly named by this run'))

try:
    report['source_head'] = run(['git', 'rev-parse', 'HEAD']).strip()
    assert not run(['git', 'status', '--porcelain', '--', 'workbench', 'scripts/launch-worker']).strip(), 'Commit merged product before regressions'
    tests = [
        ('cleanup', ['/usr/bin/python3', '-B', 'workbench/tests/test_t110_cleanup.py', '--summary']),
        ('ipc', ['node', '--experimental-vm-modules', 'workbench/tests/test_t091_pane_ipc.mjs']),
        ('questions', ['node', 'workbench/tests/test_t108_questions.mjs']),
        ('window-sequence', ['node', '--experimental-vm-modules', 'workbench/tests/test_t110_window_sequence.mjs']),
        ('reconnect-view', ['node', 'workbench/tests/test_t110_reconnect_view.mjs']),
        ('execution', ['node', 'workbench/tests/test_t112_execution.mjs']),
    ]
    for name, command in tests:
        output = evidence / ('outside-merge-' + name + '-' + args.run_id + '.json')
        assert not output.exists()
        run([*command, output])
        result = json.loads(output.read_text())
        assert result['status'] == 'PASS', result
        report['checks'].append(dict(name=name, summary=str(output), status=result['status']))
        if name == 'questions':
            clean_question_fixtures(result)
    slot = 't112-merged-' + uuid.uuid4().hex[:12]
    built = json.loads(run(['node', 'workbench/app/build.mjs', '--slot', slot]).splitlines()[-1])
    build = Path(built['out']).parent.resolve()
    assert build.parent == Path(tempfile.gettempdir()).resolve() and build.name == 'a2a-build-' + slot
    report['build'] = built
    shutil.rmtree(build)
    report['cleanup'].append(dict(path=str(build), removed=not build.exists(), scope='completed private build'))
    for name, command in [
        ('t110-native', ['/usr/bin/python3', '-B', 'workbench/tests/run_t110_notifications.py', '--electron-dist', args.electron_dist]),
        ('t112-native', ['/usr/bin/python3', '-B', 'workbench/tests/run_t112_native.py', '--source', source, '--electron-dist', args.electron_dist]),
    ]:
        output = evidence / ('outside-merge-' + name + '-' + args.run_id + '.json')
        assert not output.exists()
        run([*command, '--summary', output], timeout=2400)
        result = json.loads(output.read_text())
        assert result['status'] == 'PASS', result.get('error')
        report['checks'].append(dict(name=name, summary=str(output), status=result['status']))
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=str(error), traceback=traceback.format_exc())
finally:
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], error=report.get('error'), summary=str(summary)), ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
