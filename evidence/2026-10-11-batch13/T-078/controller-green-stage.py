"""Run the frozen controller/window regressions outside the sandbox; no vendor CLI."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'controller-green-outside-01')
    parser.add_argument('--freeze', type=Path, default=BASE / 'controller-green-code-freeze.json')
    args = parser.parse_args()
    out = args.output.resolve(); freeze_file = args.freeze.resolve()
    assert out.parent == BASE and out.name.startswith('controller-green-outside-')
    assert freeze_file.parent == BASE and freeze_file.name in ['controller-green-code-freeze.json', 'controller-green-2-code-freeze.json']
    out.mkdir()
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_', 'COOP_'))}
    record = {'status': 'INCOMPLETE', 'commands': [], 'checks': [], 'real_model_turns': 0,
              'vendor_cli_starts': 0, 'retained_frontend_slots': [],
              'scope': 'Actual daemon/client/hook/window transport; native process/PTY spies and deterministic terminal receiver',
              'timeout_action': 'Preserve PID and fixture; stop without signal, retry or next command'}
    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    def run(argv, timeout=30):
        argv = list(map(str, argv)); n = len(record['commands']) + 1
        item = {'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout,
                'stdout': f'{n:02d}.stdout.bin', 'stderr': f'{n:02d}.stderr.bin'}
        record['commands'].append(item); save()
        with (out / item['stdout']).open('xb') as stdout, (out / item['stderr']).open('xb') as stderr:
            child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            item.update(pid=child.pid, process_group=child.pid, started_at=time.time()); save()
            try: item['exit_code'] = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                item['reason'] = 'Timeout; no signal or retry'; save(); raise
        item['finished_at'] = time.time(); save()
        if item['exit_code'] != 0: raise RuntimeError({'command': n, 'exit_code': item['exit_code']})
        return (out / item['stdout']).read_text(encoding='utf-8')
    def verify(name, count, complete=False):
        facts = json.loads((out / name / 'results.json').read_bytes())
        assert facts['status'] == 'PASS' and len(facts['checks']) == count
        assert all(c['status'] == 'PASS' for c in facts['checks'])
        if complete: assert facts['setup_complete'] is True and facts['cleanup_complete'] is True
        record['checks'].append({'name': name, 'status': 'PASS', 'checks': count,
                                 'evidence': name + '/results.json'}); save()
        return facts
    save()
    try:
        freeze = json.loads(freeze_file.read_bytes())
        head = run(['git', 'rev-parse', 'HEAD']).strip(); assert head == freeze['revision']
        record['revision'] = head; save()
        assert not run(['git', 'diff', 'HEAD', '--', 'workbench', 'acceptance', 'scripts']).strip()
        assert not run(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench', 'acceptance', 'scripts']).strip()
        assert os.path.ismount('/Volumes/WD-Elements'), 'External build cache required; no fallback'
        run(['node', ROOT / 'workbench/tests/test_t078_controller_inbox_entry.ts', out / 'controller-entry'], 180)
        facts = verify('controller-entry', 6)
        state = Path(facts['fixture']) / 'state'
        assert not any((state / p).exists() for p in ['daemon.pid', 'control.sock'])
        run(['node', ROOT / 'workbench/tests/test_t078_empty_declaration_entry.ts', out / 'empty-declaration-entry'], 180)
        facts = verify('empty-declaration-entry', 17)
        assert not any((Path(facts['root']) / p).exists() for p in ['daemon.pid', 'control.sock'])
        frontend = None
        for name, flag, count in [('runtime', '--runtime-probe', 12),
                                  ('input-failures', '--input-failures', 11),
                                  ('worker-inbox', '--worker-inbox', 14)]:
            argv = ['python3', '-B', ROOT / 'workbench/tests/test_t078_input_entry.py',
                    '--source', ROOT, '--output', out / name, flag]
            if frontend: argv += ['--reuse-build', frontend]
            run(argv, 300); verify(name, count, True)
            if frontend is None:
                frontend = json.loads((out / name / 'build.json').read_bytes())['out']
                record['retained_frontend_slots'].append(frontend); save()
        assert run(['git', 'rev-parse', 'HEAD']).strip() == head
        assert not run(['git', 'diff', 'HEAD', '--', 'workbench', 'acceptance', 'scripts']).strip()
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally: save()
    print(json.dumps({'status': record['status'], 'output': str(out), 'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1

if __name__ == '__main__': raise SystemExit(main())
