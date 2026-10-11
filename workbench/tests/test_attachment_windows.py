"""Document two attachment history/transaction windows through the real CLI.

Controlled runtime/barrier code is isolated to the test host. Product source,
storage and acceptance assertions are not changed. No Codex calls occur.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import uuid

from command_evidence import CommandLog, command_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    commands = CommandLog(output)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='1',
               GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_AUTHOR_NAME='T076 attachment fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T076 attachment fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    results = []; roots = []
    record = {'status': 'INCOMPLETE', 'source': str(source), 'argv': sys.argv, 'real_codex_turns': 0,
              'scope': '两个 attachment 窗口的取证；不启动真实附着 CLI，不修存储', 'cases': results}

    def save(path, value):
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

    def run(argv, *, cwd=source, timeout=60):
        return commands.run(argv, cwd=cwd, env=env, timeout=timeout)

    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk is not mounted; no cache fallback')
        for mode in ('creating', 'active'):
            root = Path(tempfile.mkdtemp(prefix='a76-', dir='/tmp')).resolve(); roots.append(root)
            repo, state, control = root / 'repo', root / 'state', root / 'control'
            repo.mkdir(); control.mkdir(); case = output / mode; case.mkdir()
            ready, release = control / 'ready.json', control / 'release'
            host = request = None
            stdout = (case / 'host.stdout.txt').open('xb'); stderr = (case / 'host.stderr.txt').open('xb')
            cli = ['node', source / 'workbench/src/gates/cli.ts', '--state', state]
            verdict = {'mode': mode, 'status': 'INCOMPLETE', 'root': str(root), 'real_codex_turns': 0}
            try:
                for argv in (['git', 'init', '-b', 'main'],):
                    result = run(argv, cwd=repo); assert result.returncode == 0, result.evidence
                (repo / 'value.txt').write_text('attachment fixture\n', encoding='utf-8')
                for argv in (['git', 'add', 'value.txt'], ['git', 'commit', '-m', 'Independent attachment fixture']):
                    result = run(argv, cwd=repo); assert result.returncode == 0, result.evidence
                argv = ['node', source / 'workbench/tests/attachment_window_host.ts', source, state, control, ready, mode]
                host = subprocess.Popen(list(map(str, argv)), cwd=source, env=env, stdout=stdout,
                                        stderr=stderr, start_new_session=True)
                save(case / 'host-launch.json', {'pid': host.pid, 'argv': list(map(str, argv))})
                deadline = time.monotonic() + 10
                while not ready.exists():
                    if host.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError('Owned attachment host failed before ready')
                    time.sleep(0.02)
                task = 'T076-' + mode + '-' + uuid.uuid4().hex[:8]
                card = {'id': task, 'source': None, 'goal': '只观察附着状态，不运行模型', 'non_goals': ['不交付代码、不改存储'],
                    'paths': {'allow': ['value.txt'], 'deny': []}, 'completion_conditions': [{'argv': [sys.executable, '-I', '-B', '-c',
                     "from pathlib import Path; assert Path('value.txt').read_text() == 'attachment fixture\\n'"]}],
                    'red_commands': [], 'task_type': '测试', 'repair_target': None, 'complexity': 'M',
                    'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
                save(case / 'card.json', card)
                for argv in ([*cli, 'card_save', '--task', task, '--card', case / 'card.json', '--expected-version', '0'],
                             [*cli, 'create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', task]):
                    result = run(argv); assert result.returncode == 0 and command_json(result)['ok'] is True, result.evidence
                instructions = root / 'instructions.txt'; instructions.write_text('受控附着夹具，不运行 provider。\n', encoding='utf-8')
                argv = [*cli, 'attach', '--task', task, '--role', 'reviewer', '--model-selection',
                        json.dumps({'provider': 'codex', 'model': 'gpt-6.1-sol'}), '--instructions', instructions,
                        '--runtime-mode', 'approval-required', '--preset', 'reviewer']
                request = subprocess.Popen(list(map(str, argv)), cwd=source, env=env, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, start_new_session=True)
                save(case / 'attach-launch.json', {'pid': request.pid, 'argv': list(map(str, argv))})
                boundary = control / 'boundary.json'; deadline = time.monotonic() + 10
                while not boundary.exists():
                    if request.poll() is not None or host.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError('Attach did not reach the selected real write boundary')
                    time.sleep(0.02)
                result = run(['node', source / 'workbench/tests/read_attachment_window.ts', state, boundary, case / 'observation.json'])
                assert result.returncode == 0, result.evidence
                observed = json.loads((case / 'observation.json').read_text(encoding='utf-8'))
                assert observed['independently_visible'] and observed['attachment']['state'] == mode, observed
                attachment_events = [e for e in observed['events'] if e['details'].get('attachment', {}).get('thread_id') == observed['marker']['thread']]
                assert not attachment_events, 'The selected window must precede the attached event'
                if mode == 'active':
                    assert observed['marker']['state_db_in_transaction'] is False, 'Active row must be visible outside a state transaction at this observed boundary'
                result = run(['node', source / 'workbench/tests/snapshot_state.ts', state, case / 'window-databases'])
                assert result.returncode == 0, result.evidence
                result = run(['node', source / 'workbench/src/stateConsistency.ts', '--state', case / 'window-databases', '--output', case / 'consistency.json'])
                assert result.returncode in (0, 1), result.evidence
                report = json.loads((case / 'consistency.json').read_text(encoding='utf-8'))
                attachment = next(row for row in report['tables'] if row['table'] == 'attachments')
                assert attachment['label'] in ('一致', '不一致', '无法由现有事件重建'), attachment
                conclusion = {'consistent': '一致', 'inconsistent': '不一致', 'unreconstructable': '无法重建'}[attachment['status']]
                verdict.update(status='PASS', conclusion=conclusion, task=task,
                    thread=observed['marker']['thread'], table_result=attachment,
                    reason='事件重建无附件行，独立连接可见 creating 行；没有相应 creating 历史事件' if mode == 'creating' else
                           '独立连接已可见 active 行，状态库不在事务中，attached 事件尚不存在；两个事实不在同一事务内',
                    source_boundary=observed['marker'])
                release.write_text('release', encoding='utf-8')
                reply, error = request.communicate(timeout=15)
                save(case / 'attach-reply.json', {'exit': request.returncode, 'stdout': reply, 'stderr': error})
                assert request.returncode == 0 and json.loads(reply)['ok'] is True
                # The later completion does not erase the preserved window.
                result = run([*cli, 'events', '--task', task]); assert result.returncode == 0
                save(case / 'events-after-release.json', command_json(result))
            except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
                verdict.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
                raise
            finally:
                try:
                    if host is not None and host.poll() is None:
                        if not release.exists(): release.write_text('cleanup-release', encoding='utf-8')
                        if request is not None and request.poll() is None:
                            reply, error = request.communicate(timeout=15)
                            save(case / 'cleanup-attach-reply.json', {'exit': request.returncode, 'stdout': reply, 'stderr': error})
                        result = run([*cli, 'daemon_stop']); assert result.returncode == 0, result.evidence
                        host.wait(timeout=10)
                        assert host.returncode == 0
                    verdict['owned_host_exited'] = host is None or host.poll() is not None
                except (OSError, ValueError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
                    verdict.update(status='INCOMPLETE', cleanup_error=repr(error), cleanup_traceback=traceback.format_exc())
                    raise
                finally:
                    stdout.close(); stderr.close(); results.append(verdict); save(case / 'run.json', verdict)
            if verdict['status'] != 'PASS': break
        if len(results) == 2 and all(row['status'] == 'PASS' for row in results): record['status'] = 'PASS'
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        with tarfile.open(output / 'fixtures.tar.gz', 'x:gz') as archive:
            for root in roots: archive.add(root, arcname=root.name)
        save(output / 'run.json', record)
    print(json.dumps({'status': record['status'], 'conclusions': [(x['mode'], x.get('conclusion')) for x in results], 'real_codex_turns': 0}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
