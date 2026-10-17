"""Resume frozen post-rebase regressions at cards, without vendor CLIs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
TARGET = '490de67d05a08ccf8a453a78694a106288579b47'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != BASE or not out.name.startswith('post-rebase-2-outside-'):
        raise RuntimeError('Output must be a new T-078 post-rebase-2 directory.')
    out.mkdir(exist_ok=False)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_', 'COOP_'))}
    record = {'status': 'INCOMPLETE', 'commands': [], 'checks': [], 'argv': sys.argv,
              'scope': '真实库入口、hook、Electron/PTY；确定性接收器；无供应商 CLI/模型',
              'real_model_turns': 0, 'vendor_cli_starts': 0,
              'timeout_action': '保留进程身份与现场，停止阶段，不发信号或重试',
              'retained_frontend_slots': []}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, timeout=30):
        argv = [str(arg) for arg in argv]
        index = len(record['commands']) + 1
        item = {'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout,
                'stdout': f'{index:02d}.stdout.bin', 'stderr': f'{index:02d}.stderr.bin'}
        record['commands'].append(item)
        save()
        with (out / item['stdout']).open('xb') as stdout, (out / item['stderr']).open('xb') as stderr:
            child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                     start_new_session=True)
            item.update(pid=child.pid, process_group=child.pid, started_at=time.time())
            save()
            try:
                item['exit_code'] = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                item['status'] = 'INCOMPLETE'
                item['reason'] = 'timeout; owned harness retained; no next command or signal'
                save()
                raise
        item['finished_at'] = time.time()
        save()
        if item['exit_code'] != 0:
            raise RuntimeError({'command': index, 'exit_code': item['exit_code'], 'argv': argv})
        return (out / item['stdout']).read_text(encoding='utf-8')

    def verify(name, path, count, *, setup=False, cleanup=False):
        facts = json.loads(path.read_bytes())
        if facts.get('status') != 'PASS' or len(facts['checks']) != count:
            raise RuntimeError({'scenario': name, 'status': facts.get('status'), 'checks': len(facts['checks'])})
        if any(c.get('status') != 'PASS' for c in facts['checks']):
            raise RuntimeError({'scenario': name, 'reason': 'nonpassing individual check'})
        if setup and facts.get('setup_complete') is not True:
            raise RuntimeError({'scenario': name, 'reason': 'setup not complete'})
        if cleanup and facts.get('cleanup_complete') is not True:
            raise RuntimeError({'scenario': name, 'reason': 'cleanup not complete'})
        record['checks'].append({'name': name, 'status': 'PASS', 'checks': count,
                                 'evidence': str(path.relative_to(out))})
        save()

    save()
    try:
        freeze = json.loads((BASE / 'post-rebase-2b-source-freeze.json').read_bytes())
        head = run(['git', 'rev-parse', 'HEAD']).strip()
        if head != freeze['revision']:
            raise RuntimeError('Frozen revision changed.')
        record['revision'] = head
        run(['git', 'merge-base', '--is-ancestor', TARGET, head])
        if run(['git', 'diff', 'HEAD', '--', 'workbench', 'acceptance', 'scripts']).strip():
            raise RuntimeError('Frozen source changed.')
        if run(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench', 'acceptance', 'scripts']).strip():
            raise RuntimeError('Untracked source is present.')
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('External build-cache volume missing; no fallback.')
        save()

        previous = BASE / 'post-rebase-2-outside-01'
        prior = json.loads((previous / 'result.json').read_bytes())
        inbox = json.loads((previous / 'inbox-entry/results.json').read_bytes())
        if (prior['status'] != 'INCOMPLETE' or prior['revision'] != freeze['reused_inbox_revision']
                or inbox['status'] != 'PASS' or inbox['cleanup_complete'] is not True
                or len(inbox['checks']) != 8 or any(c['status'] != 'PASS' for c in inbox['checks'])):
            raise RuntimeError('Prior inbox pass and cleanup are not verified.')
        if run(['git', 'diff', prior['revision'], head, '--', 'workbench/src', 'workbench/app',
                'workbench/hooks', 'workbench/bin', 'scripts', 'acceptance',
                'workbench/tests/test_t078_inbox_entry.py']).strip():
            raise RuntimeError('Previously passing inbox source changed; stop instead of silently reusing it.')
        record['previous_passes'] = {'name': 'inbox-entry', 'status': 'PASS', 'checks': 8,
                                    'revision': prior['revision'], 'rerun': False,
                                    'evidence': str(previous / 'inbox-entry/results.json'),
                                    'product_and_inbox_source_unchanged': True}
        save()

        target = out / 'cards'
        run(['python3', '-B', ROOT / 'workbench/tests/run_s3_rebased_regression.py', '--suite', 'cards',
             '--revision', head, '--output', target], 720)
        facts = json.loads((target / 'run.json').read_bytes())
        if (facts['status'] != 'PASS' or facts['tests_run'] != 15 or facts['failures'] or facts['errors']
                or facts['skipped'] or facts['unexecuted_methods'] or facts['collection_errors']
                or facts['no_business_test_overrides'] is not True):
            raise RuntimeError({'scenario': 'cards', 'result': facts})
        record['checks'].append({'name': 'cards', 'status': 'PASS', 'checks': 15,
                                 'evidence': 'cards/run.json', 'accepted_assertions_unchanged': True})
        save()

        target = out / 'empty-declaration-entry'
        run(['node', ROOT / 'workbench/tests/test_t078_empty_declaration_entry.ts', target], 180)
        verify('empty-declaration-entry', target / 'results.json', 17)
        state = Path(json.loads((target / 'results.json').read_bytes())['root'])
        if (state / 'daemon.pid').exists() or (state / 'control.sock').exists():
            raise RuntimeError('Declaration fixture daemon exit unconfirmed.')

        frontend = None
        for name, flag, count in [('runtime', '--runtime-probe', 12),
                                  ('input-failures', '--input-failures', 11),
                                  ('worker-inbox', '--worker-inbox', 14)]:
            target = out / name
            argv = ['python3', '-B', ROOT / 'workbench/tests/test_t078_input_entry.py',
                    '--source', ROOT, '--output', target, flag]
            if frontend is not None:
                argv += ['--reuse-build', frontend]
            run(argv, 300)
            verify(name, target / 'results.json', count, setup=True, cleanup=True)
            if frontend is None:
                frontend = Path(json.loads((target / 'build.json').read_bytes())['out'])
                record['retained_frontend_slots'].append(str(frontend))
                save()
        if run(['git', 'rev-parse', 'HEAD']).strip() != head:
            raise RuntimeError('Revision changed during regression.')
        if run(['git', 'diff', 'HEAD', '--', 'workbench', 'acceptance', 'scripts']).strip():
            raise RuntimeError('Source changed during regression.')
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        save()
    print(json.dumps({'status': record['status'], 'output': str(out), 'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
