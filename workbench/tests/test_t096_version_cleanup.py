"""Supplied-boundary regression; no actual ps, AppKit, CLI, socket or signal.
Failure list: pre-quit identity refusal suppressed; unaccepted quit adopted;
accepted quit's transient argv loss aborts cleanup; PID reuse accepted; exit
timeout swallowed; nonzero exit promoted; wrong fixture daemon stopped; old
writers survive; pre-stop identity changes; duplicate stop after lost receipt;
credentials copied; original failure overwritten. Real temporary copy/files.
"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType,SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
sys.path.insert(0,str(FOLDER)); sys.path.insert(0,str(FOLDER.parent/'T-091'))
import owned_electron


def module(name,text):
    value=ModuleType(name); value.__file__=str(FOLDER/(name+'.py'))
    exec(compile(text,value.__file__,'exec'),value.__dict__); return value


class Buffer(io.BytesIO):
    def close(self): self.saved=self.getvalue(); super().close()


def electron(text,case):
    product=module('restart_cleanup',text); process=SimpleNamespace(returncode=None)
    process.poll=lambda:process.returncode
    def wait(**kwargs):
        if case=='timeout': raise subprocess.TimeoutExpired('owned Electron',3)
        process.returncode=1 if case=='nonzero' else 0; return process.returncode
    process.wait=wait; process.stdout=io.BytesIO(b'tail'); process.stdin=io.BytesIO()
    owner=dict(pid=201,started='original birth',command='/fixture/Electron /fixture/driver',driver='/fixture/driver',executable='/fixture/Electron')
    observer=SimpleNamespace(process=process,owner=owner,ready_confirmed=True,exit_confirmed=False,stdout=Buffer(),stderr=Buffer(),log=io.StringIO(),selector=io.StringIO(),max_stdout_bytes=65536)
    quit_calls=[]; reads=[]
    def read(pid):
        reads.append(pid)
        if len(reads)==1: return {k:owner[k] for k in ['pid','started','command']}
        if case=='reused': return dict(pid=201,started='new birth',command='/other')
        return None
    def request(value):
        quit_calls.append(value['pid'])
        if case=='before-request': raise RuntimeError('electron_pid_start_or_command_changed')
        return dict(pid=201,method='NSRunningApplication.terminate',requested=case!='unaccepted')
    def confirm(value):
        raise RuntimeError('unrelated-error' if case=='unrelated' else 'electron_pid_start_or_command_changed')
    with patch.object(owned_electron,'request_normal_quit',request),patch.object(owned_electron,'confirm_owner',confirm):
        try: result=product.close_observer(observer,expected_crash=False,read_process=read,normal_quit=owned_electron.normal_quit)
        except (RuntimeError,subprocess.TimeoutExpired):
            assert case not in ['accepted','nonzero'], 'Accepted normal quit followed by actual child exit must finish cleanup'
            assert not observer.stdout.closed and len(quit_calls)==1
            return
    assert case in ['accepted','nonzero'], 'Unconfirmed/reused/non-quit error must not permit cleanup'
    assert result['exited'] and len(quit_calls)==1 and observer.stdout.saved==b'tail'
    assert bool(result['diagnostics'])==(case=='nonzero'), 'Nonzero actual exit must retain a diagnostic'
    assert observer.quit_events[0]['normal_quit']['requested'] is True


source=(FOLDER/'cleanup_version_01.py').read_text(encoding='utf-8')
def fixed(text,case):
    product=module('cleanup_version_01',text)
    root=Path(tempfile.mkdtemp(prefix='t096-version-unit-',dir='/private/tmp'))
    fixture=root/'fixture'; state=fixture/'state'; state.mkdir(parents=True)
    product.HERE=root/'reports'; product.HERE.mkdir(); product.BASE=root/'external'; product.BASE.mkdir(); product.FIXTURE=fixture
    folder=product.BASE/'version-b-01'; folder.mkdir()
    pids=[78717,78784,78785,79593,79613,79604,79605,79664,79678]
    owners=[dict(pid=pid,started='recorded birth',command='recorded command '+str(pid)) for pid in pids]
    original=dict(fixture=str(fixture),owned=owners,daemon_start_receipt=dict(epoch=2,pid=79664,state=str(state)),electron_start_receipt=dict(pid=79678))
    original_path=product.HERE/'version-b-01.run.json'; original_path.write_text(json.dumps(original),encoding='utf-8'); original_bytes=original_path.read_bytes()
    journal=[*owners[:4],owners[3],*owners[4:]]
    (folder/'ownership.jsonl').write_text(''.join(json.dumps(dict(owner=o))+'\n' for o in journal),encoding='utf-8')
    (state/'daemon.pid').write_text('79664\n',encoding='utf-8'); (state/'control.sock').write_bytes(b'IPC fixture')
    for epoch in [1,2]: (fixture/f'operator-{epoch}.json').write_bytes(b'PRIVATE fixture')
    (fixture/'payload').write_bytes(b'known payload\n')
    stopped=False; reads=0; requests=[]
    expected_argv=['node','/Users/luckye/Documents/Code/a2a-wt-t096/workbench/src/daemon.ts',str(state),'{}']
    daemon=next(o for o in owners if o['pid']==79664)
    def probe(pid):
        nonlocal reads
        reads+=1
        if pid!=79664: return owners[-1] if case=='electron-live' and pid==79678 else None
        if stopped and case!='stop-live': return None
        if case=='daemon-changed' or (case=='pre-stop-change' and reads>9): return dict(daemon,command='different')
        return daemon
    def request(state_path,command,credential):
        nonlocal stopped
        assert state_path==state and credential==fixture/'operator-2.json'; requests.append(command)
        if command=='daemon_status': return dict(ok=True,pid=1 if case=='wrong-socket' else 79664,root=str(state))
        if command=='orchestration_events': return dict(events=[dict(type='daemon_started',data=dict(pid=79664,argv=expected_argv))])
        assert command=='daemon_stop'; stopped=True
        if case!='stop-live':
            (state/'daemon.pid').unlink(); (state/'control.sock').unlink()
        if case=='lost-receipt': raise RuntimeError('stop receipt lost')
        return dict(ok=True,stopping=True)
    clock=[0]
    product.probe_process=probe; product.operator_request=request
    product.native_argv=lambda pid:['changed'] if case=='argv-changed' else expected_argv
    product.time=SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda seconds:clock.__setitem__(0,clock[0]+seconds))
    def ps(argv,**kwargs):
        assert argv==['/bin/ps','-ww','-axo','pid=,ppid=,command=']
        text='200 79664 child\n' if case=='unexpected-child' else '79664 1 fixture-daemon\n'
        if case=='unexpected-writer': text+='300 1 Electron --user-data='+str(fixture/'ui')+'\n'
        return SimpleNamespace(returncode=0,stdout=text,stderr='')
    with patch.object(product.os.path,'ismount',return_value=True),patch.object(product.subprocess,'run',ps),patch.object(sys,'argv',['cleanup_version_01.py','--label','fixed','--approval-ref','supplied unit authority']):
        with contextlib.redirect_stdout(io.StringIO()): rc=product.main()
    result=json.loads((product.HERE/'fixed.run.json').read_text(encoding='utf-8'))
    assert original_path.read_bytes()==original_bytes
    assert all((fixture/f'operator-{epoch}.json').read_bytes()==b'PRIVATE fixture' for epoch in [1,2])
    assert requests.count('daemon_stop')<=1
    if case in ['normal','lost-receipt']:
        assert result['cleanup_complete'] and rc==(1 if case=='lost-receipt' else 0)
        manifest=json.loads((product.HERE/'version-b-01-fixed.archive.json').read_text(encoding='utf-8'))
        assert manifest['files']==1 and manifest['bytes']==14 and manifest['comparison']
        assert set(manifest['excluded'])=={'operator-1.json','operator-2.json'}
        assert (folder/'fixture/payload').read_bytes()==b'known payload\n'
    else:
        assert rc==1 and not result['cleanup_complete'] and result.get('handoff'), 'Invalid fixed fixture must remain unarchived'
        if case!='stop-live': assert 'daemon_stop' not in requests, 'All preflight checks must precede stop'
    return result


report=dict(status='INCOMPLETE',argv=sys.argv,scope='actual cleanup callbacks and fixed entry over supplied ps/AppKit/operator boundaries; no native action',checks=[])
try:
    old=subprocess.check_output(['git','show','f2b96001d:evidence/2026-10-16-batch16/T-096/restart_cleanup.py'],cwd=ROOT,text=True)
    try: electron(old,'accepted')
    except AssertionError as error: report['known_bad']=dict(revision='f2b96001d',rejected=True,error=str(error))
    assert report['known_bad']['rejected']
    current=(FOLDER/'restart_cleanup.py').read_text(encoding='utf-8')
    for case in ['accepted','before-request','unaccepted','timeout','reused','unrelated','nonzero']: electron(current,case); report['checks'].append('electron_'+case)
    for case in ['normal','daemon-changed','electron-live','unexpected-child','unexpected-writer','wrong-socket','argv-changed','pre-stop-change','lost-receipt','stop-live']: fixed(source,case); report['checks'].append('fixed_'+case)
    mutant=source.replace("if current!=owner: raise RuntimeError('fixed daemon PID/start/full command changed')", "if False: raise RuntimeError('fixed daemon PID/start/full command changed')")
    assert mutant!=source
    try: fixed(mutant,'daemon-changed')
    except AssertionError as error: report['mutant']=dict(rejected=True,error=str(error))
    assert report['mutant']['rejected']
    report['status']='PASS'
except BaseException as error: report.update(error=str(error),traceback=__import__('traceback').format_exc())
with Path(sys.argv[1]).open('x',encoding='utf-8') as output: output.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
