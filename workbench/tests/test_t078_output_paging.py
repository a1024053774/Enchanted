"""Exercise the actual P1 screen entry with a read-only output transport fixture."""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import uuid

SOURCE = Path(__file__).resolve().parents[2]
TESTS = SOURCE / 'workbench/tests'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def entry_case(output, script, fault, ps_mode, length, nonce, one_page_mutant, entry):
    output.mkdir()
    unit = (nonce + ' independent 中断收据\n').encode('utf-8')
    payload = (unit * ((length + len(unit) - 1) // len(unit)))[:length]
    with tempfile.TemporaryDirectory(prefix='t078-reader-entry-', dir='/tmp') as tmp:
        root = Path(tmp).resolve(); materials = root / 'materials'; materials.mkdir()
        fixture = root / 'fixture.json'; payload_file = root / 'payload.bin'; payload_file.write_bytes(payload)
        launch, session, dispatch = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        save(fixture, {'launch': launch, 'dispatch': dispatch, 'entry': entry, 'payload': str(payload_file), 'fault': fault, 'calls': str(root / 'calls.jsonl')})
        fake_node = root / 'fixture-node'
        fake_node.write_text('#!' + sys.executable + '\n' + f'''import base64,json,sys
from pathlib import Path
f=json.loads(Path({str(fixture)!r}).read_bytes());a=sys.argv[1:]
assert a[0]=={str(SOURCE/'workbench/src/gates/cli.ts')!r}
command=a[a.index('--state')+2]
assert command in (['pane_output','pane_status'] if f['entry']=='permission' else ['pane_output']), a
if command=='pane_status':
    with Path(f['calls']).open('a') as stream:stream.write(json.dumps({{'command':command}})+'\\n')
    print(json.dumps({{'ok':True,'state':'busy','active':{{'dispatch':f['dispatch']}}}}));raise SystemExit(0)
assert a[a.index('--launch')+1]==f['launch']
offset=int(a[a.index('--offset')+1]);data=Path(f['payload']).read_bytes();total=len(data)
with Path(f['calls']).open('a') as stream:stream.write(json.dumps({{'command':'pane_output','offset':offset}})+'\\n')
raw=data[offset:offset+65536];next_offset=offset+len(raw)
if offset and f['fault']=='total-change':total+=1
if offset==len(data) and f['fault']=='eof-change':total+=1
if offset and offset<len(data) and f['fault']=='zero-progress':raw=b'';next_offset=offset
if offset and offset<len(data) and f['fault']=='truncated':raw=b'';next_offset=len(data)
print(json.dumps({{'ok':True,'launch':f['launch'],'start_offset':offset,'next_offset':next_offset,'total_bytes':total,'data_base64':base64.b64encode(raw).decode()}}))
''', encoding='utf-8'); fake_node.chmod(0o755)
        role = root / 'roles/executor/role.md'; role.parent.mkdir(parents=True); role.write_text('Reader fixture only\n')
        inp = {'root': str(root), 'task': 'reader-fixture', 'preset': 'executor', 'launch': launch,
               'session': session, 'thread': str(uuid.uuid4()), 'role_file': str(role)}
        save(root / 'input.json', inp); save(materials / 'input.json', inp)
        save(root / 'scenario.json', {'name': 'reader-fixture'}); shutil.copyfile(root / 'scenario.json', materials / 'scenario.json')
        (root / 'nonce.txt').write_text(nonce); shutil.copyfile(root / 'nonce.txt', materials / 'nonce.txt')
        shutil.copyfile(role, materials / 'role.md')
        save(materials / 'approval.json', {'input': inp, 'launch': {'node_executable': str(fake_node)}})
        frozen = ['workbench/tests/run_t078_p1.py']
        if (TESTS / 'p1_output.py').exists(): frozen.append('workbench/tests/p1_output.py')
        save(materials / 'source-files.json', frozen)
        with tarfile.open(materials / 'sources.tar.gz', 'x:gz') as archive:
            for name in frozen: archive.add(SOURCE / name, arcname=name)
        if ps_mode == 'real':
            from p1_processes import identity_from_ps
            observed = subprocess.run(['/bin/ps', '-p', str(os.getpid()), '-o', 'pid=,lstart=,comm='], capture_output=True, text=True,
                                      env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}, check=True)
            identity = identity_from_ps(os.getpid(), observed.returncode, observed.stdout, observed.stderr)
        else:
            identity = {'pid': 424242, 'started': 'Thu Jan 1 00:00:00 2026', 'command': 'fixture-python'}
        save(materials / 'launch/process-manifest.json', {'launch': launch, 'session': session, 'cli': identity})
        entry_dir = materials / ('screen-01' if entry == 'screen' else 'permission-01')
        entry_args = [str(script), '--materials', str(materials), '--phase', 'screen', '--label', 'screen-01', '--screen-id', 'fixture-screen']
        if entry == 'permission':
            (root / 'state').mkdir()
            with sqlite3.connect(root / 'state/state.sqlite3') as db:
                db.execute('CREATE TABLE orchestration_events(seq INTEGER,type TEXT,launch TEXT,data TEXT)')
                db.execute('INSERT INTO orchestration_events VALUES (7,?,?,?)', ('permission_wait', launch, '{}'))
            save(root / 'stage-a/readiness.json', {'root': str(root)})
            reference = root / 'permission-screen.bin'; reference.write_bytes(payload)
            pages = [{'start_offset': offset, 'next_offset': min(offset + 65536, length), 'total_bytes': length,
                      'bytes': min(65536, length - offset)} for offset in range(0, length, 65536)]
            pages.append({'start_offset': length, 'next_offset': length, 'total_bytes': length, 'bytes': 0})
            capture = {'complete': True, 'start_offset': 0, 'next_offset': length, 'total_bytes': length, 'pages': pages}
            dispatch_value = {'status': 'READY_FOR_PERMISSION', 'stage': 'E4',
                 'dispatch': {'id': dispatch, 'tool_use': {'input': {'command': 'echo fixture'}}},
                 'permission_event': {'seq': 7, 'data': {'tool_input': {'command': 'echo fixture'}}},
                 'permission_screen': str(reference), 'permission_screen_capture': capture}
            if fault == 'missing-capture':
                dispatch_value.pop('permission_screen_capture'); reference.write_bytes(payload[:65536])
            save(root / 'dispatch.json', dispatch_value)
            save(root / 'permission.json', {'approved_by': 'executor', 'approval_ref': 'isolated reader fixture only',
                 'launch': launch, 'session': session, 'dispatch': dispatch, 'permission_seq': 7,
                 'screen_file': str(reference), 'key': 'Enter', 'selected_label': 'Yes', 'selected_line': '\u276f 1. Yes',
                 'bash_command': 'echo fixture'})
            fake_bin = root / 'bin'; fake_bin.mkdir(); shutil.copyfile(fake_node, fake_bin / 'node'); (fake_bin / 'node').chmod(0o755)
            entry_args = [str(script), '--materials', str(materials), '--p1', str(materials), '--stage', 'E4',
                          '--stage-a', str(root / 'stage-a'), '--dispatch-result', str(root / 'dispatch.json'),
                          '--process-manifest', str(materials / 'launch/process-manifest.json'), '--approval', str(root / 'permission.json'),
                          '--output', str(entry_dir), '--check-only']
        wrapper = root / 'entry.py'
        mutant_path = None
        if one_page_mutant:
            mutant_path = root / 'mutant'; mutant_path.mkdir()
            bad = (TESTS / 'p1_output.py').read_text(encoding='utf-8') + '''
def read_complete_output(fetch_page, launch):
    value=fetch_page(0); raw=base64.b64decode(value['data_base64'])
    return {'raw':raw,'output':value,'capture':{'complete':True,'start_offset':0,'next_offset':value['next_offset'],'total_bytes':value['total_bytes'],'pages':[]}}
'''
            (mutant_path / 'p1_output.py').write_text(bad, encoding='utf-8')
            (output / 'known-bad-reader.py').write_text(bad, encoding='utf-8')
        wrapper.write_text(f'''import sys,runpy,types
sys.path.insert(0,{str(TESTS)!r})
''' + (f'sys.path.insert(0,{str(mutant_path)!r})\n' if mutant_path else '') + ('''import command_evidence
original=command_evidence.CommandLog.run
def ps_spy(self,argv,**kwargs):
    if str(argv[0])=='/bin/ps':
        assert argv[1:]==['-p','424242','-o','pid=,lstart=,comm=']
        return types.SimpleNamespace(returncode=0,stdout='424242 Thu Jan 1 00:00:00 2026 fixture-python\\n',stderr='')
    return original(self,argv,**kwargs)
command_evidence.CommandLog.run=ps_spy
''' if ps_mode == 'spy' else '') + (f'''import subprocess
actual_run=subprocess.run
def output_transport(argv,**kwargs):
    if str(argv[0])=='/opt/homebrew/bin/node':
        return actual_run([{str(fake_node)!r},*argv[1:]],**kwargs)
    return actual_run(argv,**kwargs)
subprocess.run=output_transport
''' if entry == 'permission' else '') + f'''sys.argv={entry_args!r}
runpy.run_path({str(script)!r},run_name='__main__')
''', encoding='utf-8')
        command = [sys.executable, '-B', str(wrapper)]
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        if entry == 'permission': env['PATH'] = str(fake_bin) + os.pathsep + env.get('PATH', '')
        run = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True, timeout=30)
        (output / 'stdout.bin').write_bytes(run.stdout); (output / 'stderr.bin').write_bytes(run.stderr)
        result = json.loads((entry_dir / 'result.json').read_bytes())
        calls_file = root / 'calls.jsonl'
        calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
        shutil.copytree(entry_dir, output / 'entry')
        (output / 'expected-payload.bin').write_bytes(payload)
        expected_rejection = fault != 'good'
        if expected_rejection:
            passed = run.returncode == 1 and not (entry_dir / 'screen.bin').exists()
            expected_error = {'total-change': 'output_total_changed', 'eof-change': 'output_total_changed',
                              'zero-progress': 'output_zero_progress', 'truncated': 'output_byte_count_mismatch',
                              'missing-capture': 'permission_complete_capture_required'}[fault]
            passed = passed and expected_error in result.get('error', '')
        else:
            if entry == 'screen':
                screen = entry_dir / 'screen.bin'
                passed = run.returncode == 0 and screen.is_file() and screen.read_bytes() == payload
                if passed:
                    meta = json.loads((entry_dir / 'screen.json').read_bytes())
                    passed = meta['capture']['complete'] is True and meta['output']['next_offset'] == length == meta['output']['total_bytes']
            else:
                passed = run.returncode == 0 and result['status'] == 'PASS' and result['business_input_sent'] is False
                if passed: passed = result['permission_screen_verified_capture']['total_bytes'] == length
            page_calls = [call for call in calls if call['command'] == 'pane_output']
            passed = passed and page_calls[-1]['offset'] == length and len(page_calls) > 1
        record = {'status': 'PASS' if passed else 'INCOMPLETE', 'fault': fault, 'ps_mode': ps_mode,
                  'entry_script': str(script), 'entry_kind': entry, 'one_page_mutant': one_page_mutant, 'argv': command, 'exit_code': run.returncode,
                  'observed_error': result.get('error'), 'page_calls': calls, 'expected_bytes': length,
                  'expected_rejection': expected_rejection, 'scope': 'Real reader CLI entry; read-only output/identity transport fixture; no native CLI/API/daemon/window/key'}
        save(output / 'result.json', record)
    assert not root.exists()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--p1-script', type=Path)
    parser.add_argument('--entry', choices=['screen', 'permission'], default='screen')
    parser.add_argument('--ps-mode', choices=['spy', 'real'], default='spy')
    parser.add_argument('--entry-only', action='store_true')
    parser.add_argument('--one-page-mutant', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    script = args.p1_script or TESTS / ('run_t078_p1.py' if args.entry == 'screen' else 't078_09b_i1_permission.py')
    cases = [('good', 90137), ('good', 155701)]
    if not args.entry_only:
        cases += [('total-change', 90137), ('zero-progress', 90137), ('truncated', 90137), ('eof-change', 90137)]
        if args.entry == 'permission': cases += [('missing-capture', 90137)]
    results = []
    for index, (fault, length) in enumerate(cases, 1):
        results.append(entry_case(args.output / f'{index:02d}-{fault}', script.resolve(), fault,
                                  args.ps_mode, length, 'nonce-' + uuid.uuid4().hex, args.one_page_mutant, args.entry))
    report = {'status': 'PASS' if all(x['status'] == 'PASS' for x in results) else 'INCOMPLETE',
              'ps_mode': args.ps_mode, 'cases': results, 'scene_actions': 0, 'scratch_removed': True}
    save(args.output / 'results.json', report)
    print(json.dumps({'status': report['status'], 'cases': len(results), 'ps_mode': args.ps_mode, 'scene_actions': 0}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
