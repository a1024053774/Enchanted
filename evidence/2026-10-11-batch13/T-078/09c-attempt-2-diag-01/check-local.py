"""Check diagnosis files and commands without ps, scene writes or shutdown."""
import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[4]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
HERE = Path(__file__).resolve().parent
CLOSE = BASE / '09c-attempt-2-closeout-materials-01'
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
import t078_raw_retention as raw


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    checked = []
    for folder in [HERE, CLOSE]:
        for path in sorted(folder.rglob('*')):
            if not path.is_file(): continue
            if path.suffix in ['.py', '.md', '.txt', '.json']:
                text = path.read_text(encoding='utf-8')
                assert '\ufffd' not in text and not text.startswith('\ufeff'), path
                if path.suffix == '.py': ast.parse(text, filename=str(path))
                if path.suffix == '.json': json.loads(text)
                checked.append(str(path))
    original = raw.read_json(BASE / '09c-attempt-2-materials-02/owner.json')
    owner = raw.read_json(CLOSE / 'capture-owner.json')
    assert {k: v for k, v in owner.items() if k != 'evidence_trees'} == {
        k: v for k, v in original.items() if k != 'evidence_trees'}
    # Metadata receipts only. No NativeRuntime/ps; no claim about live lifetimes.
    raw.validate_owner_receipts(owner)
    approval = raw.read_json(CLOSE / 'cleanup-approval.json')
    assert approval['approved_by'] is None and approval['approval_ref'] is None
    assert approval['retain_failed_scene'] is True
    for key in ['root', 'scene', 'source_revision', 'processes', 'target_binding']:
        assert approval[key] == original[key]
    manifest = []
    for path in sorted(CLOSE.glob('*COMMAND.txt')):
        text = path.read_text(encoding='utf-8')
        syntax = subprocess.run(['/bin/sh', '-n', str(path)], capture_output=True, text=True)
        assert syntax.returncode == 0, (path, syntax.stderr)
        if "<<'PY'" in text:
            ast.parse(text.split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0])
        for line in text.splitlines():
            if not line.startswith('python3 -B /'): continue
            argv = shlex.split(line)
            assert Path(argv[2]).is_file(), argv[2]
            inputs = {}
            for key in ['--owner', '--approval']:
                if key in argv:
                    value = Path(argv[argv.index(key) + 1]); assert value.is_file(), value
                    inputs[key] = str(value)
            manifest.append({'file':str(path),'entry':argv[2],'existing_inputs':inputs,
                             'execution':'NOT_RUN'})
    # Parse recorded ps columns with the real probe, substituting only the ps
    # transport. The synthetic extra PID below is never a live observation.
    spec = importlib.util.spec_from_file_location('topology_probe', HERE / 'probe-topology.py')
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    identities = {value['pid']: value for value in owner['processes'].values()}
    graph = {value['pid']: owner['process_graph'][label] for label, value in owner['processes'].items()}
    fixture_cases = []
    for number, add_extra in enumerate([False, True], 1):
        nodes = copy.deepcopy(graph)
        if add_extra:
            assert 2000000000 not in nodes
            nodes[2000000000] = {'ppid':owner['processes']['ideation_cli']['pid'], 'pgid':2000000000, 'tpgid':-1}
        def ps_fixture(folder, name, argv):
            if argv[1] == '-axo':
                return ''.join(f"{pid} {row['ppid']} {row['pgid']} {row['tpgid']}\n" for pid,row in nodes.items())
            pid = int(argv[argv.index('-p') + 1]); row = nodes[pid]
            identity = identities.get(pid, {'started':'Fri Oct 16 21:06:14 2026', 'command':'/usr/bin/false --synthetic-probe-fixture'})
            if argv[-1] == 'comm=': return shlex.split(identity['command'])[0] + '\n'
            return (f"{pid} {row['ppid']} {row['pgid']} {row['tpgid']} " + identity['started'] + ' ' + identity['command'] + '\n')
        with patch.object(probe, 'run', ps_fixture):
            value = probe.sample(args.output / ('parser-fixture-' + str(number)), owner)
        assert value['extra'] == ([2000000000] if add_extra else []) and value['missing'] == []
        for pid, identity in identities.items():
            assert value['details'][str(pid)]['command'] == identity['command']
            assert value['details'][str(pid)]['lstart'] == identity['started']
        if add_extra:
            assert value['details']['2000000000']['current_parent_chain'] == [
                2000000000, owner['processes']['ideation_cli']['pid'],
                owner['processes']['ideation_shell']['pid'], owner['processes']['daemon']['pid']]
        fixture_cases.append({'status':'PASS','name':'extra' if add_extra else 'original-nine',
                              'scope':'recorded owner + synthetic ps transport; not actual ps or process classification'})
    # Actual CLI duplicate-output refusal, before any ps read.
    duplicate = args.output / 'duplicate-existing'; duplicate.mkdir()
    sentinel = duplicate / 'sentinel.bin'; sentinel.write_bytes(b'unchanged\x00')
    result = subprocess.run([sys.executable, '-B', HERE/'probe-topology.py', '--output', duplicate], capture_output=True)
    assert result.returncode != 0 and b'FileExistsError' in result.stderr
    assert sentinel.read_bytes() == b'unchanged\x00' and list(duplicate.iterdir()) == [sentinel]
    save(args.output/'duplicate-refusal.json', {'exit_code':result.returncode,
         'stderr':result.stderr.decode(),'original_bytes_unchanged':True,'ps_calls':0,'signals_sent':[]})
    save(args.output/'result.json', {'status':'PASS','scope':'UTF8/AST/command syntax, original metadata binding, parser fixtures and duplicate refusal only',
         'checked_text_files':len(checked),'commands':manifest,'parser_fixtures':fixture_cases,
         'future_inputs':[str(HERE/'current-topology-01'),'external capture/tar and signed independent readback'],
         'live_ps':'BLOCKED by sandbox; not run by this check','scene_actions':0,
         'classification':'UNKNOWN','rehearsal_parity_green':'INCOMPLETE'})
    print(json.dumps({'status':'PASS','checked_text_files':len(checked),'command_entries':len(manifest),
         'parser_fixtures':len(fixture_cases),'duplicate_refusal':'PASS','scene_actions':0,
         'process_classification':'UNKNOWN','parity_green':'INCOMPLETE'}))


if __name__ == '__main__': main()
