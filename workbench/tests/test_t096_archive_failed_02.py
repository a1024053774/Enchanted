"""Fixed -02 archive entry, real temporary files/copy, supplied PID/socket probes.
No actual process queries, socket connections, CLI, PTY, Electron or model.
Failures: live PID/endpoint archived; secret or IPC copied; originals changed;
counts/bytes not checked; arbitrary target accepted; later epoch adopted.
"""
import contextlib
import errno
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
sys.path.insert(0,str(FOLDER))
source=(FOLDER/'archive_failed_02.py').read_text(encoding='utf-8')


def module(text):
    value=ModuleType('archive_02_test'); value.__file__=str(FOLDER/'archive_failed_02.py')
    exec(compile(text,value.__file__,'exec'),value.__dict__); return value


def exercise(text,scenario,case='02-pair'):
    product=module(text); real_targets=product.TARGETS if case=='02-pair' else [product.RED03 if case=='red-b-03' else product.RED04]
    home=Path(tempfile.mkdtemp(prefix='t096-archive-02-unit-',dir='/private/tmp'))
    product.HERE=home/'reports'; product.HERE.mkdir(); product.BASE=home/'evidence'; product.BASE.mkdir()
    targets=[]; originals={}; controls=set(); connect_calls=[]
    for index,real in enumerate(real_targets):
        fixture=home/('fixture-'+str(index)); (fixture/'repo').mkdir(parents=True); (fixture/'state').mkdir()
        (fixture/'repo/value.txt').write_bytes(b'text\n')
        (fixture/'state/daemon.pid').write_text(str(real['daemon'])+'\n',encoding='utf-8')
        control=fixture/'state/control.sock'; control.write_bytes(b'placeholder socket'); controls.add(control)
        credential=fixture/'operator-1.json'; credential.write_bytes(b'PRIVATE_UNIT_SENTINEL'); credential.chmod(0o600)
        (fixture/'link').symlink_to('repo/value.txt')
        target=dict(real,fixture=str(fixture)); targets.append(target)
        ownerlist=[dict(pid=pid,started='fixture start',command='fixture command') for pid in real['pids']]
        original=dict(fixture=str(fixture),owned=ownerlist,status='INCOMPLETE',daemon_start_receipt=dict(epoch=1))
        summary=product.HERE/(real['label']+'.run.json'); summary.write_text(json.dumps(original),encoding='utf-8')
        originals[summary]=summary.read_bytes()
        folder=product.BASE/real['label']; folder.mkdir()
        (folder/'ownership.jsonl').write_text(''.join(json.dumps(dict(owner=owner))+'\n' for owner in ownerlist),encoding='utf-8')
        for path in [fixture/'repo/value.txt',fixture/'state/daemon.pid',control,credential]: originals[path]=path.read_bytes()
    if scenario=='later-epoch': (Path(targets[0]['fixture'])/'operator-2.json').write_bytes(b'unread new epoch')
    if case=='02-pair': product.TARGETS=targets
    elif case=='red-b-03': product.RED03=targets[0]
    else: product.RED04=targets[0]
    reads=[]
    def probe(pid):
        reads.append(pid)
        if scenario=='live-pid' and pid==({'02-pair':15840,'red-b-03':26605,'red-b-04':53458}[case]): return dict(pid=pid,started='still live',command='still live')
        return None
    product.probe_process=probe
    real_lstat=Path.lstat
    def lstat(path):
        value=real_lstat(path)
        if path in controls:
            return SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_uid=value.st_uid,st_ino=value.st_ino,st_dev=value.st_dev)
        return value
    class Client:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def settimeout(self,seconds): assert seconds==2
        def connect_ex(self,path):
            connect_calls.append(path)
            if scenario=='live-endpoint': return 0
            if scenario=='unknown-endpoint': return errno.EACCES
            return errno.ECONNREFUSED
    with patch.object(product.os.path,'ismount',return_value=True),patch.object(product.socket,'socket',return_value=Client()),patch.object(Path,'lstat',lstat),patch.object(sys,'argv',['archive_failed_02.py','--case',case,'--label','archive-test','--approval-ref','local supplied probes']):
        with contextlib.redirect_stdout(io.StringIO()): rc=product.main()
    if scenario=='normal':
        assert rc==0, 'Absent writer fixture must archive successfully'
        report=json.loads((product.HERE/'archive-test.run.json').read_text(encoding='utf-8'))
        assert report['source_writes']==0 and report['process_reads']==21*len(targets)
        for item in report['targets']:
            assert item['files']==3 and item['bytes']==25, 'Archive must contain independent fixture payload and literal symlink bytes only'
            copied=product.BASE/item['label']/'fixture'
            assert (copied/'repo/value.txt').read_bytes()==b'text\n'
            assert (copied/'link').is_symlink() and (copied/'link').readlink()==Path('repo/value.txt')
            assert not (copied/'operator-1.json').exists() and not (copied/'state/control.sock').exists()
            manifest=json.loads((product.HERE/(item['label']+'-archive-test.archive.json')).read_text(encoding='utf-8'))
            assert set(manifest['excluded'])=={'operator-1.json','state/control.sock'} and manifest['comparison']
    else:
        assert rc==1 and not any((product.BASE/t['label']/'fixture').exists() for t in targets), 'Live/unknown/later run must remain unarchived'
        report=json.loads((product.HERE/'archive-test.run.json').read_text(encoding='utf-8'))
        assert report['handoff']['targets']==targets, 'Handoff must name only the selected failed run'
    assert all(path.read_bytes()==value for path,value in originals.items()), 'Every original file and old summary must remain unchanged'
    assert len(reads)<=56

report=dict(status='INCOMPLETE',scope='actual archive entry, temporary real file copies; supplied PID/socket probes; no actual failed fixture action',checks=[])
try:
    actual=module(source)
    assert {t['fixture']:set(t['pids']) for t in actual.TARGETS}=={
        '/private/tmp/t078-2-t096-dkri52ul':{15789,15840,15841,15853,15864,15857,15858},
        '/private/tmp/t078-2-t096-j4p4ocqz':{16015,16098,16099,16115,16200,16199,16208}}
    assert 'os.kill(' not in source and '.unlink(' not in source and 'operator_request(' not in source
    for scenario in ['normal','live-pid','live-endpoint','unknown-endpoint','later-epoch']:
        exercise(source,scenario); report['checks'].append(scenario)
    assert actual.RED03['fixture']=='/private/tmp/t078-2-t096-7sh2mwtq' and set(actual.RED03['pids'])=={26509,26605,26607,26727,26759,26750,26751}
    exercise(source,'normal','red-b-03'); exercise(source,'live-pid','red-b-03'); report['checks'].append('red03_fixed_case_and_handoff')
    assert actual.RED04['fixture']=='/private/tmp/t078-2-t096-mhufgnng' and set(actual.RED04['pids'])=={53370,53458,53459,53506,53533,53550,53534}
    for scenario in ['normal','live-pid','live-endpoint','unknown-endpoint','later-epoch']: exercise(source,scenario,'red-b-04')
    report['checks'].append('red04_fixed_case_and_handoff')
    mutant=source.replace('symlinks=True,ignore=ignore','symlinks=True,ignore=lambda directory,names:[]')
    assert mutant!=source
    try: exercise(mutant,'normal')
    except AssertionError as error:
        report['mutant']=dict(rejected=str(error).startswith('Absent writer fixture'),error=str(error))
    assert report['mutant']['rejected'], 'Copying excluded paths must fail independent count/byte contract'
    report['checks']+=['fixed_pid_sets','no_source_mutation','private_and_ipc_excluded','counts_and_bytes','literal_symlink_copy','original_failure_preserved']
    report['status']='PASS'
except BaseException as error: report['error']=str(error); report['traceback']=__import__('traceback').format_exc()
with Path(sys.argv[1]).open('x',encoding='utf-8') as output: output.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
