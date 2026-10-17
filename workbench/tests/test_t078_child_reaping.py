"""Replay #369's real Z sample and the actual CScene cleanup wiring.

Only ps/Popen/SQLite transports are fixtures. No scene, process, signal or model
starts here. The separate child-exit probe supplies physical waitpid evidence.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2]
TESTS = SOURCE / 'workbench/tests'
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
SAMPLE = BASE / '09c-parity-child-exit-probe-01/before-reap-4.json'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def recorded_zombie(raw, out):
    original = json.loads(SAMPLE.read_bytes()); cells = original['stdout'].strip().split(None, 9)
    assert len(cells) == 10 and 'Z' in cells[3]
    pid, parent = int(cells[0]), int(cells[1]); calls = []
    def ps(argv, **_):
        calls.append(argv)
        assert argv[:2] == ['/bin/ps', '-ww'] and int(argv[argv.index('-p') + 1]) == pid
        text = original['stdout'] if 'stat=' in argv[-1] else f'{pid} {" ".join(cells[4:9])} {cells[9]}\n'
        return subprocess.CompletedProcess(argv, 0, text, '')
    runtime = raw.NativeRuntime({'processes': {'daemon': {'pid': pid, 'started': ' '.join(cells[4:9])}}})
    runtime.exit_output = out / 'exit-observations'
    with patch.object(raw.subprocess, 'run', ps):
        try: runtime.wait_absent(['daemon'], 0)
        except ValueError as error: reason = str(error)
        else: raise AssertionError('Z must never count as absent')
    assert f'pid={pid}' in reason and f'ppid={parent}' in reason and 'stat=Z' in reason, ('missing_Z_identity_diagnostic', reason)
    samples = list(runtime.exit_output.rglob('sample-*.json')); assert samples, 'raw Z ps not saved'
    saved = [json.loads(path.read_bytes()) for path in samples]
    assert any(row['probes'][0]['stdout'] == original['stdout'] for row in saved), 'real Z bytes not preserved'
    return {'status': 'PASS', 'pid': pid, 'ppid': parent, 'error': reason, 'raw_samples': list(map(str, samples))}


def cleanup_wiring(raw, scene_module, out):
    calls = []; states = {}; children = []
    with tempfile.TemporaryDirectory(prefix='t078-child-wiring-', dir='/private/tmp') as scratch:
        root = Path(scratch); evidence = root / 'evidence'; evidence.mkdir(); (evidence / 'startup-topology').mkdir()
        processes = {label: {'pid': 41000 + index, 'started': 'Fri Oct 16 23:32:21 2026',
                            'command': '/fixture/' + label}
                     for index, label in enumerate(['daemon', 'ideation_api', 'executor_api', 'target_shell',
                         'target_leader', 'ideation_shell', 'ideation_cli', 'executor_shell', 'executor_cli'])}
        owner = {'root': str(root), 'source': str(SOURCE), 'source_revision': '1' * 40, 'scene': '09C',
                 'target_binding': {}, 'evidence_trees': [], 'processes': processes,
                 'process_graph': {key: {'ppid': os.getpid()} for key in processes}}
        (root / 'raw-owner.json').write_text(json.dumps(owner), encoding='utf-8')
        bypid = {row['pid']: name for name, row in processes.items()}
        states.update({label: 'S' for label in processes})
        class Child:
            def __init__(self, name, pid): self.name = name; self.pid = pid; self.args = ['/fixture/' + name]; self.returncode = None
            def wait(self, timeout):
                calls.append('wait:' + self.name)
                assert self.name == 'coordinator' or states[self.name] == 'Z', 'wait before authorized stop/signal'
                self.returncode = 0; states[self.name] = None; return 0
        for label in ['daemon', 'ideation_api', 'executor_api', 'coordinator']:
            name = label.replace('_', '-'); child = Child(label, processes[label]['pid'] if label in processes else 42000)
            children.append({'name': name, 'pid': child.pid, 'argv': child.args, 'child': child})
        scene = scene_module.CScene.__new__(scene_module.CScene)
        scene.root = root; scene.state = root / 'state'; scene.output = evidence; scene.children = children
        def native(argv, **_):
            if argv[-1] == 'daemon_stop':
                calls.append('daemon_stop')
                for label in states: states[label] = 'Z' if label == 'daemon' or label.endswith('_api') else None
                return subprocess.CompletedProcess(argv, 0, b'', b'')
            assert argv[0] == '/bin/ps', argv
            pid = int(argv[argv.index('-p') + 1]); label = bypid[pid]; calls.append('ps:' + label)
            if states[label] is None: return subprocess.CompletedProcess(argv, 1, '', '')
            prefix = f'{pid} {os.getpid()} {pid} {states[label]} ' if 'stat=' in argv[-1] else f'{pid} '
            return subprocess.CompletedProcess(argv, 0, prefix + processes[label]['started'] + ' ' + processes[label]['command'] + '\n', '')
        def kill(pid, number):
            label = bypid[pid]; assert label.endswith('_api') and number == 15
            calls.append('SIGTERM:' + label); states[label] = 'Z'
        class Database:
            def backup(self, other): pass
            def close(self): pass
            def execute(self, statement): assert statement == 'PRAGMA integrity_check'; return self
            def fetchone(self): return ('ok',)
        def finish(owner, approval, captured, independent, output, runtime):
            runtime.exit_output = Path(output) / 'exit-observations'
            runtime.normal_stop()
            runtime.wait_absent([label for label in processes if not label.endswith('_api')], 0)
            for label in ['ideation_api', 'executor_api']:
                runtime.terminate(label); runtime.wait_absent([label], 0)
            assert all(item['child'].returncode is not None for item in children), 'direct child left unreaped'
            return {'status': 'PASS', 'root_removed': True}
        with patch.object(raw, 'check_identities', return_value=[]), patch.object(raw, 'capture', return_value={}), \
             patch.object(raw, 'archive_capture', return_value={}), patch.object(raw, 'readback', return_value={}), \
             patch.object(raw, 'finish', finish), patch.object(raw.subprocess, 'run', native), \
             patch.object(raw.os, 'kill', kill), patch.object(scene_module.sqlite3, 'connect', return_value=Database()):
            scene.cleanup()
        assert calls.index('daemon_stop') < calls.index('wait:daemon') < calls.index('ps:daemon')
        for role in ['ideation', 'executor']:
            label = role + '_api'
            assert calls.index('SIGTERM:' + label) < calls.index('wait:' + label) < calls.index('ps:' + label)
        assert 'wait:coordinator' in calls
    return {'status': 'PASS', 'scope': 'actual CScene.cleanup; explicit transport fixtures', 'calls': calls}


def detached_and_live_guards(raw, out):
    checks = []
    for name, states, expected in [('launchd_reaps_Z', ['Z', None], 'PASS'), ('live_is_not_absent', ['S'], 'BLOCKED'),
                                   ('reused_PID', ['REUSED'], 'BLOCKED')]:
        runtime = raw.NativeRuntime({'processes': {'daemon': {'pid': 32408, 'started': 'Fri Oct 16 23:32:21 2026'}}})
        runtime.exit_output = out / name; index = 0
        def ps(argv, **_):
            nonlocal index
            value = states[min(index, len(states) - 1)]; index += 1
            if value is None: return subprocess.CompletedProcess(argv, 1, '', '')
            started = 'Sat Oct 17 00:00:00 2026' if value == 'REUSED' else 'Fri Oct 16 23:32:21 2026'
            stat = 'S' if value == 'REUSED' else value
            return subprocess.CompletedProcess(argv, 0, f'32408 1 32408 {stat} {started} /fixture/daemon\n', '')
        with patch.object(raw.subprocess, 'run', ps), patch.object(raw.os, 'waitpid', side_effect=AssertionError('must not reap launchd child')), \
             patch.object(raw.os, 'kill', side_effect=AssertionError('wait_absent must not signal')), patch.object(raw.time, 'sleep'):
            try: runtime.wait_absent(['daemon'], 1 if expected == 'PASS' else 0); actual = 'PASS'
            except ValueError as error: actual = 'BLOCKED'; reason = str(error)
        assert actual == expected, (name, actual)
        if name == 'reused_PID': assert 'identity_changed' in reason
        checks.append({'name': name, 'status': 'PASS', 'actual_verdict': actual})
    return checks


def child_handle_guards(raw, scene, out):
    from types import SimpleNamespace
    import copy
    checks = []
    labels = ['daemon', 'ideation_api', 'executor_api']
    processes = {name: {'pid': 51000 + index} for index, name in enumerate(labels)}
    owner = {'processes': processes, 'process_graph': {name: {'ppid': os.getpid()} for name in labels}}
    children = []
    def never_wait(**_): raise AssertionError('invalid binding must not reach wait')
    for label in labels:
        argv = ['/fixture/' + label]; child = SimpleNamespace(pid=processes[label]['pid'], args=argv, wait=never_wait)
        children.append({'name': label.replace('_', '-'), 'pid': child.pid, 'argv': argv, 'child': child})
    for name in ['foreign_parent', 'changed_handle_PID', 'changed_spawn_argv', 'duplicate_handle']:
        candidate = copy.deepcopy(owner); handles = copy.deepcopy(children)
        if name == 'foreign_parent': candidate['process_graph']['daemon']['ppid'] = 1
        if name == 'changed_handle_PID': handles[0]['pid'] += 999
        if name == 'changed_spawn_argv': handles[0]['argv'] = handles[0]['argv'] + ['--wrong']
        if name == 'duplicate_handle': handles.append(handles[0])
        try: scene.DirectChildRuntime(candidate, handles, out / name)
        except AssertionError as error: assert 'original' in str(error) or 'unique' in str(error)
        else: raise AssertionError('foreign/changed child accepted:' + name)
        checks.append({'name': name, 'status': 'PASS', 'waits': 0, 'signals': 0})
    def timeout(**_): raise subprocess.TimeoutExpired('/fixture/daemon', 20)
    children[0]['child'].wait = timeout
    runtime = scene.DirectChildRuntime(owner, children, out / 'child-timeout')
    with patch.object(raw.NativeRuntime, 'normal_stop'), patch.object(raw.os, 'kill', side_effect=AssertionError('timeout must not signal APIs')):
        try: runtime.normal_stop()
        except subprocess.TimeoutExpired: pass
        else: raise AssertionError('timed out direct child accepted')
    receipt = json.loads((out / 'child-timeout/child-waits/daemon.json').read_bytes())
    assert receipt['status'] == 'BLOCKED' and receipt['pid'] == processes['daemon']['pid']
    checks.append({'name': 'child_timeout_blocks_before_API_signal', 'status': 'PASS', 'receipt': receipt})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--expect', choices=['red', 'green'], required=True)
    parser.add_argument('--raw-source', type=Path, default=TESTS / 't078_raw_retention.py')
    parser.add_argument('--scene-source', type=Path, default=TESTS / 'test_t078_09c_real_chain.py')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    raw = load('t078_raw_retention', args.raw_source); scene = load('test_t078_09c_real_chain', args.scene_source)
    results = []
    for name, call in [('recorded_Z_diagnostic', lambda: recorded_zombie(raw, out / 'Z')),
                       ('creator_reaps_before_OS_absence', lambda: cleanup_wiring(raw, scene, out / 'wiring'))]:
        try: results.append({'name': name, **call()})
        except Exception as error: results.append({'name': name, 'status': 'FAIL', 'error': repr(error), 'traceback': traceback.format_exc()})
    success = all(row['status'] == 'PASS' for row in results)
    if args.expect == 'red':
        expected = ['missing_Z_identity_diagnostic', 'owned_process_exit_unconfirmed']
        verdict = all(row['status'] == 'FAIL' and reason in row['error'] for row, reason in zip(results, expected))
    else:
        try: guards = detached_and_live_guards(raw, out / 'guards') + child_handle_guards(raw, scene, out / 'child-guards')
        except Exception as error: guards = [{'status': 'FAIL', 'error': repr(error), 'traceback': traceback.format_exc()}]
        results.extend(guards); verdict = success and all(row['status'] == 'PASS' for row in guards)
    value = {'status': 'PASS' if verdict else 'INCOMPLETE', 'expect': args.expect, 'results': results,
             'sample': str(SAMPLE), 'raw_source': str(args.raw_source), 'scene_source': str(args.scene_source),
             'processes_started': 0, 'actual_signals': 0, 'model_turns': 0,
             'limitations': 'ps/Popen transports are explicit fixtures; full nine-process outside rehearsal still required'}
    with (out / 'result.json').open('x', encoding='utf-8') as stream: stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(value, ensure_ascii=False)); return 0 if verdict else 1


if __name__ == '__main__': raise SystemExit(main())
