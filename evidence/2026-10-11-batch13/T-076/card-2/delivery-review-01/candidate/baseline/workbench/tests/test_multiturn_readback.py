"""Fixture-only counterfactual for pre-stop snapshots and saved collection.

Expected rows are supplied independently. No daemon, socket, Git or model is
started. The known-bad harness is the preserved file from before this repair.
"""
import argparse
import ast
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace

import test_multiturn_identity_e2e as candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--known-bad', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    candidate.OUT = out; (out / 'readbacks').mkdir()
    old_source = args.known_bad.read_text(encoding='utf-8')
    old = {'__name__': 't076_known_bad', '__file__': str(args.known_bad)}
    exec(compile(old_source, str(args.known_bad), 'exec'), old)
    old_main = next(node for node in ast.parse(old_source).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    index = next(index for index, node in enumerate(old_main.body) if isinstance(node, ast.Assign) and
                 any(isinstance(target, ast.Name) and target.id == 'snapshots' for target in node.targets))
    collector = ast.Module(body=old_main.body[index:index + 2], type_ignores=[])
    old_collection = compile(ast.fix_missing_locations(collector), str(args.known_bad), 'exec')
    observations = []

    def fixture(label):
        root = Path(tempfile.mkdtemp(prefix='m76-read-', dir='/tmp')).resolve()
        state = root / 'state'; state.mkdir()
        writer = sqlite3.connect(state / 'state.sqlite3')
        writer.execute('PRAGMA journal_mode=WAL')
        for table in ('tasks', 'attempts', 'verifications', 'runs', 'events'):
            writer.execute('CREATE TABLE ' + table + ' (id INTEGER, value TEXT)')
        writer.execute('INSERT INTO tasks VALUES (7, ?)', ('独立输入：' + label,)); writer.commit()
        expected = [{'id': 7, 'value': '独立输入：' + label}]
        host = SimpleNamespace(pid=10001, returncode=None)
        host.poll = lambda: host.returncode
        host.wait = lambda timeout: host.returncode
        artifact = {'test': label, 'root': str(root)}
        value = candidate.MultiTurn('test_reclaim_after_receipt_turn')
        value.root, value.state, value.host, value.artifact = root, state, host, artifact
        value.host_stdout, value.host_stderr = io.StringIO(), io.StringIO()
        value.run_process = None
        def stop(argv):
            assert argv[-1] == 'daemon_stop'
            candidate.previous.COMMANDS.append({'argv': list(map(str, argv)), 'exit': 0,
                                                'fixture_only': True})
            writer.close()
            host.returncode = 0
            root.rename(root.with_name(root.name + '-retained'))
            return SimpleNamespace(returncode=0)
        value.process = stop
        return value, artifact, expected

    bad, artifact, expected = fixture('known-bad')
    old['MultiTurn'].stop_host(bad)
    namespace = {'previous': SimpleNamespace(ARTIFACTS=[artifact]), 'Path': Path, 'sqlite3': sqlite3}
    try:
        exec(old_collection, namespace)
    except sqlite3.OperationalError as error:
        observations.append({'case': 'known-bad-after-stop-and-root-move', 'status': 'PASS',
                             'counterfactual': 'original collector rejects the required readback',
                             'error': repr(error), 'expected': expected})
    else:
        raise AssertionError('The original late collector must fail when its source root moved')

    good, artifact, expected = fixture('candidate-sentinel')
    candidate.MultiTurn.stop_host(good)
    observed = candidate.read_state([artifact])
    assert observed[0]['tables']['tasks'] == expected, (expected, observed)
    assert observed[0]['phase'] == 'before-host-stop' and not good.root.exists()
    observations.append({'case': 'candidate-after-stop-and-root-move', 'status': 'PASS',
                         'expected': expected, 'observed': observed})
    for field, replacement in [('test', 'foreign-test'), ('database', '/foreign/state.sqlite3'), ('phase', 'after-host-stop')]:
        original = Path(artifact['state_readback'])
        wrong = json.loads(original.read_text(encoding='utf-8')); wrong[field] = replacement
        path = out / (field + '-foreign.json'); path.write_text(json.dumps(wrong), encoding='utf-8')
        try:
            candidate.read_state([{**artifact, 'state_readback': str(path)}])
        except RuntimeError:
            observations.append({'case': 'reject-foreign-' + field, 'status': 'PASS'})
        else:
            raise AssertionError('Foreign snapshot binding accepted: ' + field)
    record = {'status': 'PASS', 'scope': '读回夹具反事实；不证明后台、身份修复或产品行为',
              'argv': sys.argv, 'real_codex_turns': 0, 'observations': observations}
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': 'PASS', 'cases': len(observations), 'real_codex_turns': 0}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
