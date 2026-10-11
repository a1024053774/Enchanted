#!/usr/bin/env python3
"""Two explicitly approved real launches, four root turns maximum, no retries."""
import argparse
import contextlib
import datetime
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077'
PLAN_FILE = EVIDENCE / 'real-plan-01.json'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog, command_json
from fixture_artifacts import archive_stopped_database

BASE_SOURCE = 'def summarize(values):\n    total = sum(values)\n    return {"count": len(values), "total_ms": total}\n'
HOST_SOURCE = 'def summarize(values):\n    total = sum(values)\n    return {"count": len(values), "total_ms": total, "unit": "ms"}\n'
ORACLE = '''import importlib.util,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("independent_summary",root/"src/summary.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for values,expected in [([], {"count":0,"total_ms":0,"mean_ms":None}),
                        ([2,5,8], {"count":3,"total_ms":15,"mean_ms":5.0}),
                        ([-4,1], {"count":2,"total_ms":-3,"mean_ms":-1.5}),
                        ([0], {"count":1,"total_ms":0,"mean_ms":0.0})]:
    actual=module.summarize(values)
    print(json.dumps({"values":values,"actual":actual,"expected":expected}),flush=True)
    for key,value in expected.items(): assert actual[key]==value,(values,expected,actual)
    if sys.argv[2]=="integrated": assert actual==dict(expected,unit="ms"),(values,actual)
if sys.argv[2]=="integrated":
    assert (root/"host-policy.txt").read_text()=="unit=ms; source=host\\n"
print("independent summary oracle PASS")
'''


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2); handle.write('\n')


def records(path):
    raw = path.read_bytes()
    return [json.loads(line) for line in raw.splitlines(keepends=True) if line.endswith(b'\n')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=int, choices=(1, 2), required=True)
    parser.add_argument('--approval-ref', required=True)
    args = parser.parse_args()
    if not args.approval_ref.strip(): raise ValueError('An explicit controller approval reference is required')
    plan = json.loads(PLAN_FILE.read_text(encoding='utf-8'))
    fixture, repo, state, home = (Path(plan[k]) for k in ('fixture', 'repo', 'state', 'home'))
    control = fixture / 'control'
    run_root = EVIDENCE / 'real-conflict-01'
    out = run_root / ('attempt-' + str(args.phase))
    out.mkdir(parents=True, exist_ok=False)
    log = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_'))}
    env.update(GIT_AUTHOR_NAME='T077 real fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T077 real fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    git_env = dict(env, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='1',
                   GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull)
    cli = [plan['node'], plan['cli'], '--state', str(state)]
    owned = set(); host = None; started = False; keep = False; current_launch = None; created_fixture = False
    record = {'status': 'INCOMPLETE', 'phase': args.phase, 'validation_task': plan['task'], 'product_revision': plan['product_revision'],
              'evidence_layer': 'production gates/Panes with real PTY and Codex; public-launch-ID fixture',
              'argv': sys.argv, 'approval_ref': args.approval_ref, 'real_turns_reserved': 0,
              'observed_root_turns': None, 'fixture': str(fixture), 'requested_model': 'gpt-6.1-sol',
              'requested_effort': 'xhigh', 'requested_service_tier': 'fast'}

    def run(argv, *, cwd=ROOT, command_env=env, check=True, timeout=60):
        result = log.run(argv, cwd=cwd, env=command_env, timeout=timeout)
        if check and result.returncode: raise RuntimeError({'command_failed': result.evidence})
        return result

    def call(command, *values, check=True):
        result = run([*cli, command, *values], check=False, timeout=120)
        value = command_json(result)
        if check and (result.returncode != 0 or value.get('ok') is not True):
            raise RuntimeError({'gate_failed': result.evidence, 'reply': value})
        return value

    def git(*values, cwd=repo):
        return run(['git', *values], cwd=cwd, command_env=git_env).stdout.strip()

    def unchanged_product():
        assert run(['git', 'rev-parse', 'HEAD']).stdout.strip() == plan['product_revision']
        run(['git', 'diff', '--exit-code', plan['product_revision'], '--', 'workbench', 'acceptance', '.project-map/roles/worker.md'])

    def observe(thread):
        info = call('pane_process_info', '--thread', thread)
        owned.update(p['pid'] for p in info['processes'])
        if info['failed']: raise RuntimeError({'runtime_identity_unknown': info})
        return info

    def wait_receipt(attempt):
        thread = attempt['thread_id']; deadline = time.monotonic() + 30
        while True:
            info = observe(thread)
            if info['leader']: break
            if time.monotonic() > deadline: raise RuntimeError('Initial leader was not observed')
            time.sleep(0.1)
        save(out / 'before-release.json', info)
        call('pane_release', '--thread', thread, '--reason', args.approval_ref + ': initial foreground leader checked; bind native session after first input')
        deadline = time.monotonic() + 900; last = None
        while True:
            pane = call('pane_status', '--thread', thread)
            if pane['failed'] or pane['stopped']: raise RuntimeError({'pane_failed': pane})
            rows = []
            if pane['native_session']:
                paths = list((home / 'sessions').rglob('*' + pane['native_session'] + '.jsonl'))
                if len(paths) != 1: raise RuntimeError('Root rollout is not unique')
                rows = records(paths[0])
            turns = {r['payload']['turn_id'] for r in rows if r['type'] == 'event_msg' and r['payload'].get('type') == 'task_started'}
            completed = {r['payload']['turn_id'] for r in rows if r['type'] == 'event_msg' and r['payload'].get('type') == 'task_complete'}
            if len(turns) > 2: raise RuntimeError('A third turn in one attempt is outside the approved budget')
            progress = (len(turns), len(completed), pane['state'])
            if progress != last:
                print(json.dumps({'phase': args.phase, 'turns': len(turns), 'completed': len(completed), 'pane': pane['state']}), flush=True)
                last = progress
            if len(turns) == len(completed) == 2 and pane['state'] == 'idle' and not pane['queued'] and not pane['writing']:
                break
            if len(turns) == len(completed) == 1 and pane['state'] == 'idle' and not pane['queued'] and not pane['writing']:
                raise RuntimeError('First turn ended without an explicit request/receipt; no automatic extra input')
            if time.monotonic() > deadline: raise RuntimeError('Delivery and receipt did not finish within 900 seconds')
            time.sleep(0.5)
        after = observe(thread)
        assert after['leader'] == info['leader'] and after['native_session'] == pane['native_session']
        current = call('status', '--task', plan['task'])['task']
        assert current['state'] == 'submitted' and current['current_attempt']['attempt_id'] == attempt['attempt_id'], current
        bound = current['current_attempt']; delivery_turn = bound['turn_id']
        assert delivery_turn in turns
        receipt_turn = next(iter(turns - {delivery_turn}))
        assert not [r for r in rows if r['type'] == 'response_item' and r['payload'].get('type') in ('function_call', 'custom_tool_call') and
                    r['payload'].get('internal_chat_message_metadata_passthrough', {}).get('turn_id') == receipt_turn]
        context = [r['payload'] for r in rows if r['type'] == 'turn_context' and r['payload'].get('turn_id') == delivery_turn][-1]
        assert context['model'] == 'gpt-6.1-sol' and context.get('effort', context.get('reasoning_effort')) == 'xhigh'
        metadata = [r['payload'] for r in rows if r['type'] == 'session_meta' and r['payload'].get('source') == 'cli']
        assert len(metadata) == 1 and metadata[0]['id'] == after['native_session'] and metadata[0]['cwd'] == attempt['workspace']
        assert metadata[0]['cli_version'] == '0.162.1'
        candidate = current['candidate_commit']
        message = git('show', '-s', '--format=%B', candidate)
        fields = [line for line in message.splitlines() if line.startswith('A2A-')]
        expected = {'A2A-Task': plan['task'], 'A2A-Attempt': attempt['attempt_id'], 'A2A-Session': attempt['session_id'],
                    'A2A-Role': 'worker', 'A2A-Tool': 'codex-cli 0.162.1', 'A2A-Model': 'gpt-6.1-sol', 'A2A-Effort': 'xhigh',
                    'A2A-Native-Session': after['native_session'], 'A2A-Launch': current_launch['id']}
        assert len(fields) == 9 and dict(line.split(': ', 1) for line in fields) == expected
        assert git('diff', '--name-only', attempt['base_commit'], candidate, '--').splitlines() == ['src/summary.py']
        save(out / 'receipt-boundary.json', {'attempt': bound, 'candidate': candidate, 'turns': sorted(turns),
            'completed': sorted(completed), 'native_session': after['native_session'], 'pane': pane, 'process_info': after,
            'delivery_context': context, 'expected_trailers': expected, 'message': message})
        record['observed_root_turns'] = 2
        return current, paths[0], after

    def reserve():
        budget = EVIDENCE / 'real-turn-budget.jsonl'
        with budget.open('a+', encoding='utf-8') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX); handle.seek(0)
            entries = [json.loads(line) for line in handle if line.strip()]
            reservations = [v for v in entries if v['kind'] == 'reservation']
            if len(reservations) != args.phase - 1 or sum(v['turns'] for v in reservations) != 2 * (args.phase - 1):
                raise RuntimeError('Budget ledger does not authorize another invocation')
            handle.seek(0, 2)
            handle.write(json.dumps({'kind': 'reservation', 'phase': args.phase, 'turns': 2, 'limit': 4,
                'launch': plan['launches'][args.phase - 1]['launch'], 'approval_ref': args.approval_ref, 'output': str(out),
                'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}) + '\n')
            handle.flush(); os.fsync(handle.fileno())
        record['real_turns_reserved'] = 2

    def record_launch(attempt):
        spec = plan['launches'][args.phase - 1]
        launch = call('launch_show', '--launch', spec['launch'])['launch']
        assert launch['argv'] == spec['argv'] and launch['worktree'] == spec['workspace']
        assert launch['attempt'] == attempt['attempt_id'] and launch['fence'] == args.phase
        assert launch['env']['CODEX_HOME'] == str(home)
        save(out / 'launch-record.json', launch)
        return launch

    try:
        if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External volume is unavailable')
        unchanged_product()
        if args.phase == 1:
            fixture.mkdir(mode=0o700); created_fixture = True
            repo.mkdir(); state.mkdir(); home.mkdir(mode=0o700); control.mkdir()
            with tarfile.open(run_root / 'source-snapshot.tar.gz', 'x:gz') as archive:
                for part in ('src', 'hooks', 'tests'):
                    archive.add(ROOT / 'workbench' / part, arcname='workbench/' + part)
                for name in ('real-launch-host.ts', 'run-real-conflict.py', 'real-plan-01.json'):
                    archive.add(EVIDENCE / name, arcname='fixture/' + name)
                archive.add(ROOT / '.project-map/roles/worker.md', arcname='worker-role.md')
            git('init', '-b', 'main')
            (repo / 'src').mkdir(); (repo / 'src/summary.py').write_text(BASE_SOURCE, encoding='utf-8')
            (repo / '.gitignore').write_text('__pycache__/\n*.pyc\n', encoding='utf-8')
            (repo / 'host-policy.txt').write_text('host baseline\n', encoding='utf-8')
            git('add', '.'); git('commit', '-m', 'Independent T077 conflict baseline')
            base = git('rev-parse', 'HEAD'); record['base'] = base
            (fixture / 'check.py').write_text(ORACLE, encoding='utf-8')
            red = run([sys.executable, '-I', '-B', fixture / 'check.py', repo, 'worker'], check=False)
            assert red.returncode == 1, 'The independent oracle must reject the known-bad baseline'
            assert json.loads(red.stdout.splitlines()[0]) == {'values': [], 'actual': {'count': 0, 'total_ms': 0},
                'expected': {'count': 0, 'total_ms': 0, 'mean_ms': None}}, 'An import/setup failure is not oracle red evidence'
            shutil.copyfile(Path.home() / '.codex/auth.json', home / 'auth.json'); (home / 'auth.json').chmod(0o600)
            (home / 'config.toml').write_text('[projects.' + json.dumps(plan['trust_root']) + ']\ntrust_level="trusted"\n', encoding='utf-8')
            (home / 'rules').mkdir(); (home / 'rules/default.rules').write_text('\n'.join(plan['rules']) + '\n', encoding='utf-8')
            config = {'codex_bin': plan['codex'], 'codex_home': str(home), 'role_card': plan['role_card'],
                      'role_card_revision': plan['role_card_revision'], 'code_revision': plan['product_revision'],
                      'source_snapshot': str(run_root / 'source-snapshot.tar.gz'), 'turn_limit': 4,
                      'hook_authorization': 'T-077 per-launch approvals in control/approval-a1.json and approval-a2.json',
                      'turn_authorization': 'T-077 total four root turns; two per explicitly approved launch; no retry'}
            save(control / 'launch-config.json', config)
            reserve()
            save(control / 'approval-a1.json', {'launch': plan['launches'][0]['launch'], 'product_revision': plan['product_revision'], 'controller_ref': args.approval_ref})
            argv = [plan['node'], str(EVIDENCE / 'real-launch-host.ts'), str(ROOT), str(PLAN_FILE), str(control / 'launch-config.json'), str(control / 'ready.json')]
            with (out / 'host.stdout.txt').open('xb') as stdout, (out / 'host.stderr.txt').open('xb') as stderr:
                host = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            owned.add(host.pid); started = True
            assert os.getpgid(host.pid) == os.getsid(host.pid) == host.pid and os.getpgrp() != host.pid
            save(run_root / 'host-process.json', {'pid': host.pid, 'argv': argv, 'root': str(state)})
            deadline = time.monotonic() + 15
            while not (control / 'ready.json').exists():
                if host.poll() is not None or time.monotonic() > deadline: raise RuntimeError('Owned host did not become ready')
                time.sleep(0.1)
            assert call('daemon_status')['pid'] == host.pid
            card = {'id': plan['task'], 'source': {'ticket': str(ROOT / '.project-map/tickets/T-077-worktree-lifecycle-conflicts.md'), 'ready_rev': 1},
                'goal': '这是隔离夹具任务。只在当前 worktree 的 src/summary.py 扩展 summarize(values) 的返回字典，新增 mean_ms 字段。'
                        'values 是整数列表；mean_ms 是 total_ms/count，空列表为 None；保留 count、total_ms 及现有其他字段和原求和行为。'
                        '不新增辅助函数或装饰器。运行完成条件；只做一次提交，git add 和 git commit 各自独立执行。'
                        '使用派发的 submit 命令并加 --request-id delivery。结束回合，让 Stop 转交；回执回合只确认收到，不调用工具或提交新请求。'
                        '来源 ticket 只作绑定；实现范围限本夹具，不到 a2a 源码仓库工作。',
                'non_goals': ['不改 host-policy.txt、.gitignore、任务卡、oracle、权限；不访问网络，不启动子 agent'],
                'paths': {'allow': ['src/summary.py'], 'deny': []},
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', str(fixture / 'check.py'), '{worktree}', 'worker']}],
                'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'M',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}, 'base_commit': None, 'writer': None}
            save(run_root / 'card.json', card)
            call('card_save', '--task', plan['task'], '--card', run_root / 'card.json', '--expected-version', '0')
            call('create', '--task', plan['task'], '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', plan['project'])
            attempt = call('dispatch', '--task', plan['task'], '--runtime-mode', 'workspace-write')['attempt']
            current_launch = record_launch(attempt)
            current, rollout, info = wait_receipt(attempt)
            candidate = current['candidate_commit']; record['C1'] = candidate
            (repo / 'src/summary.py').write_text(HOST_SOURCE, encoding='utf-8')
            (repo / 'host-policy.txt').write_text('unit=ms; source=host\n', encoding='utf-8')
            git('add', 'src/summary.py', 'host-policy.txt')
            git('commit', '-m', 'Independent host unit policy\n\nA2A-Task: T-077-10')
            G = git('rev-parse', 'HEAD'); record['G'] = G
            # The native worker is idle and its exact leader was just rechecked.
            # End only that owned CLI, leaving the original shell for the gate.
            confirmed = observe(attempt['thread_id'])
            idle = call('pane_status', '--thread', attempt['thread_id'])
            assert confirmed['leader'] == info['leader'] and confirmed['native_session'] == info['native_session']
            assert idle['state'] == 'idle' and not idle['queued'] and not idle['writing']
            save(out / 'native-exit-intent.json', {'signal': 'SIGTERM', 'pid': confirmed['leader'], 'identity': confirmed, 'idle': idle})
            os.kill(confirmed['leader'], signal.SIGTERM)
            deadline = time.monotonic() + 15
            while True:
                ended = observe(attempt['thread_id'])
                if ended['session_ended']: break
                if time.monotonic() > deadline: raise RuntimeError('Native end was not confirmed; do not open a new attempt')
                time.sleep(0.1)
            save(out / 'native-ended.json', ended)
            raw = rollout.read_bytes(); (out / 'original-rollout.jsonl').write_bytes(raw)
            assert raw.endswith(b'\n')
            save(run_root / 'continuation.json', {'attempt': current['current_attempt'], 'C1': candidate, 'G': G,
                'rollout': str(rollout), 'original_rollout': str(out / 'original-rollout.jsonl'),
                'first_native': info['native_session'], 'owned_pids': sorted(owned)})
            unchanged_product()
            save(out / 'orchestration-events.json', call('orchestration_events', '--task', plan['task'])['events'])
            record.update(status='INCOMPLETE', stage='awaiting_second_launch_approval', observed_root_turns=2, owned_pids=sorted(owned))
            keep = True
        else:
            with tarfile.open(run_root / 'source-snapshot.tar.gz', 'r:gz') as archive:
                for name in ('real-launch-host.ts', 'run-real-conflict.py', 'real-plan-01.json'):
                    with archive.extractfile('fixture/' + name) as saved:
                        assert (EVIDENCE / name).read_bytes() == saved.read(), 'Experiment changed between launch approvals'
                with archive.extractfile('worker-role.md') as saved:
                    assert (ROOT / '.project-map/roles/worker.md').read_bytes() == saved.read()
            previous = json.loads((run_root / 'attempt-1/run.json').read_text(encoding='utf-8'))
            assert previous['stage'] == 'awaiting_second_launch_approval' and previous['observed_root_turns'] == 2
            continuation = json.loads((run_root / 'continuation.json').read_text(encoding='utf-8'))
            old = continuation['attempt']; owned.update(continuation['owned_pids'])
            host_record = json.loads((run_root / 'host-process.json').read_text(encoding='utf-8'))
            assert call('daemon_status')['pid'] == host_record['pid']; started = True
            old_file = Path(continuation['rollout']); original = Path(continuation['original_rollout']).read_bytes()
            assert old_file.read_bytes() == original
            assert git('rev-parse', 'HEAD') == continuation['G']
            reserve()
            save(control / 'approval-a2.json', {'launch': plan['launches'][1]['launch'], 'product_revision': plan['product_revision'], 'controller_ref': args.approval_ref})
            conflict = call('verify', '--task', plan['task'], '--attempt', old['attempt_id'], check=False)
            save(out / 'conflict-reply.json', conflict)
            assert conflict.get('ok') is False and conflict.get('error') == 'merge_conflict', conflict
            current = call('status', '--task', plan['task'])['task']; attempt = current['current_attempt']
            assert attempt['fence'] == 2 and attempt['attempt_id'] != old['attempt_id'] and attempt['session_id'] != old['session_id']
            assert attempt['base_commit'] == continuation['G'] and attempt['conflict_source']
            current_launch = record_launch(attempt)
            initial_new = call('pane_status', '--thread', attempt['thread_id'])
            assert initial_new['native_session'] != continuation['first_native']
            save(out / 'before-new-worker-input.json', initial_new)
            current, rollout, info = wait_receipt(attempt)
            assert old_file.read_bytes() == original
            assert info['native_session'] != continuation['first_native'] and rollout != old_file
            events = call('orchestration_events', '--task', plan['task'])['events']
            new_metadata = [e['data']['record']['payload'] for e in events if e.get('launch') == current_launch['id'] and
                            e['type'] == 'native_record' and e['data']['record']['type'] == 'session_meta' and e['data']['record']['payload'].get('source') == 'cli']
            assert len(new_metadata) == 1 and new_metadata[0]['id'] == info['native_session'] and new_metadata[0]['cwd'] == attempt['workspace']
            save(out / 'history-isolation.json', {'same_home': str(home), 'old_rollout': str(old_file),
                'old_native': continuation['first_native'], 'old_bytes_unchanged': True, 'new_rollout': str(rollout),
                'new_launch': current_launch['id'], 'before_input_native': initial_new['native_session'],
                'new_metadata': [{k: p[k] for k in ('id', 'source', 'cwd', 'cli_version')} for p in new_metadata]})
            candidate = current['candidate_commit']
            verified = call('verify', '--task', plan['task'], '--attempt', attempt['attempt_id'])['verification']
            assert verified['state'] == 'passed' and verified['C'] == candidate and verified['G'] == continuation['G']
            assert verified['attempt']['attempt_id'] == attempt['attempt_id']
            call('integrate', '--task', plan['task'], '--attempt', attempt['attempt_id'])
            assert git('rev-parse', 'HEAD') == candidate
            run([sys.executable, '-I', '-B', fixture / 'check.py', repo, 'integrated'])
            assert git('merge-base', '--is-ancestor', continuation['G'], candidate) == ''
            assert git('rev-parse', 'refs/a2a/attempts/' + plan['task'] + '/a1') == continuation['C1']
            gates = call('events', '--task', plan['task'])['events']; save(out / 'gate-events.json', gates)
            for kind in ('path_check', 'completion_check', 'trailer_check'):
                assert any(e['type'] == kind and e['details']['verification_id'] == verified['verification_id'] and e['details']['passed'] for e in gates)
            call('reclaim', '--task', plan['task'], '--attempt', attempt['attempt_id'])
            assert not Path(attempt['workspace']).exists() and not Path(old['workspace']).exists()
            assert git('rev-parse', 'refs/a2a/attempts/' + plan['task'] + '/a2') == candidate
            assert old_file.read_bytes() == original
            assert (fixture / 'check.py').read_text(encoding='utf-8') == ORACLE
            save(out / 'orchestration-events.json', call('orchestration_events', '--task', plan['task'])['events'])
            unchanged_product()
            record.update(status='PASS', C1=continuation['C1'], C2=candidate, G=continuation['G'], verification=verified['verification_id'],
                          old_native=continuation['first_native'], new_native=info['native_session'], observed_root_turns=2)
    except (OSError, ValueError, KeyError, IndexError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        record.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
    finally:
        if not keep and started:
            try:
                save(out / 'events-before-stop.json', call('orchestration_events'))
                run([plan['node'], ROOT / 'workbench/tests/snapshot_state.ts', state, out / 'databases-before-stop'])
                save(out / 'daemon-stop.json', call('daemon_stop'))
                if host is not None: host.wait(timeout=10)
                deadline = time.monotonic() + 15
                while True:
                    seen = run(['/bin/ps', '-p', ','.join(map(str, sorted(owned))), '-o', 'pid=,ppid=,command='], check=False) if owned else None
                    if seen and (seen.returncode not in (0, 1) or seen.stderr.strip()): raise RuntimeError('Process exit observation failed')
                    if not (state / 'daemon.pid').exists() and not (seen and seen.stdout.strip()): break
                    if time.monotonic() > deadline: raise RuntimeError('Owned process exit is unconfirmed; preserve home')
                    time.sleep(0.1)
                archived = archive_stopped_database(state, out / 'databases-after-stop/state.sqlite3')
                save(out / 'database-after-stop.json', archived)
                with contextlib.closing(sqlite3.connect(Path(archived['path']).as_uri() + '?mode=ro', uri=True)) as db:
                    db.row_factory = sqlite3.Row
                    all_events = [{**dict(r), 'data': json.loads(r['data'])} for r in db.execute('SELECT * FROM orchestration_events ORDER BY seq')]
                save(out / 'events-after-stop.json', all_events)
                root_turns = {(e['launch'], e['data']['record']['payload']['turn_id']) for e in all_events
                    if e['type'] == 'native_record' and e['data']['record']['type'] == 'event_msg' and
                    e['data']['record']['payload'].get('type') == 'task_started'}
                record['observed_total_root_turns'] = len(root_turns)
                record['observed_root_turns'] = sum(launch == plan['launches'][args.phase - 1]['launch'] for launch, _turn in root_turns)
                record['turn_count_complete'] = not any(e['type'] == 'native_final_read_failed' for e in all_events)
                if record['status'] == 'PASS':
                    assert record['turn_count_complete']
                    assert not any(e['type'] in ('permission_wait', 'dispatch_unknown', 'stop_transfer_failed', 'queue_stopped') for e in all_events)
                if args.phase == 2 and record['status'] == 'PASS': assert len(root_turns) == 4
                with tarfile.open(out / 'fixture-artifacts.tar.gz', 'x:gz') as archive:
                    for path in (repo, state, fixture / 'check.py', home / 'sessions', control):
                        if path.exists(): archive.add(path, arcname=str(path.relative_to(fixture)))
                    for number in (1, 2):
                        launch_file = run_root / f'attempt-{number}/launch-record.json'
                        if launch_file.exists():
                            launch = json.loads(launch_file.read_text(encoding='utf-8'))
                            request_dir = Path(launch['request_dir'])
                            if request_dir.exists(): archive.add(request_dir, arcname=f'request-files-a{number}')
                shutil.rmtree(home); record['isolated_home_removed'] = True
            except (OSError, ValueError, KeyError, AssertionError, RuntimeError, sqlite3.Error, subprocess.TimeoutExpired, tarfile.TarError) as error:
                record.update(status='BLOCKED', cleanup_error=repr(error))
        elif created_fixture and not started and home.exists():
            # Setup failed before an owned host existed; no process can use this
            # newly created credential copy. Preserve the other fixture files.
            shutil.rmtree(home); record['isolated_home_removed'] = True
        if record['real_turns_reserved']:
            with (EVIDENCE / 'real-turn-budget.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'kind': 'observation', 'phase': args.phase, 'observed': record['observed_root_turns'],
                    'status': record['status'], 'output': str(out)}) + '\n')
        save(out / 'run.json', record)
        # Preserve verbose command output in a byte-checked compressed file.
        raw = out / 'commands.jsonl'
        if raw.exists() and raw.stat().st_size > 5 * 1024 * 1024:
            data = raw.read_bytes()
            with gzip.open(out / 'commands.jsonl.gz', 'xb') as handle: handle.write(data)
            assert gzip.decompress((out / 'commands.jsonl.gz').read_bytes()) == data
            raw.unlink()
    print(json.dumps({k: record.get(k) for k in ('status', 'stage', 'phase', 'observed_root_turns', 'observed_total_root_turns', 'error', 'cleanup_error')}, ensure_ascii=False))
    return 0 if keep or record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
