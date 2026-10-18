"""Fixed cleanup entry with supplied ps/sysctl/socket/archive boundaries only.

Failure list: wrong target accepted, a second fixture mismatch stops the first,
identity changes after preflight accepted, archive before exit/credential removal,
old summaries overwritten, force signals introduced. No process/socket/model run.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import ModuleType
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'evidence/2026-10-16-batch16/T-096'
sys.path.insert(0,str(FOLDER))
source=(FOLDER/'cleanup_failed_01.py').read_text(encoding='utf-8')


def module(text):
    value=ModuleType('t096_cleanup_entry'); value.__file__=str(FOLDER/'cleanup_failed_01.py')
    exec(compile(text,value.__file__,'exec'),value.__dict__)
    return value


def stamp(seconds): return datetime.fromtimestamp(seconds,timezone.utc).isoformat()
def owner(pid,seconds): return dict(pid=pid,started=time.strftime('%a %b %d %H:%M:%S %Y',time.localtime(seconds)),command='full command '+str(pid))
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data)+'\n',encoding='utf-8')


def exercise(text,scenario):
    product=module(text)
    home=Path(tempfile.mkdtemp(prefix='t096-fixed-cleanup-unit-',dir='/private/tmp'))
    product.HERE=home/'reports'; product.HERE.mkdir(); product.BASE=home/'archive'; product.BASE.mkdir()
    targets=[]; live={}; argv={}; counts={}; records={}; calls=[]; originals={}
    for index in range(2):
        fixture=home/('fixture-'+str(index)); state=fixture/'state'; state.mkdir(parents=True)
        daemon,shell,cli=201+index*10,202+index*10,203+index*10
        target=dict(label='run-'+str(index),fixture=str(fixture),source='/source-'+str(index),daemon=daemon,shell=shell,cli=cli)
        targets.append(target)
        (state/'daemon.pid').write_text(str(daemon),encoding='utf-8'); (state/'control.sock').write_text('fixture socket boundary',encoding='utf-8')
        credential=fixture/'operator-1.json'; credential.write_text('not read by supplied socket boundary',encoding='utf-8')
        write(fixture/'launch.json',{}); os.utime(fixture/'launch.json',(1000,1000))
        record=dict(id='launch-'+str(index),session='native-'+str(index),thread='thread-'+str(index),worktree=str(fixture/'repo'),
            created_at=stamp(1011),shell='/bin/zsh',shell_argv=['-f','-i','-c','fixture command'],argv=['/fixture/claude','--session-id','native-'+str(index),'--model','fixture-model'])
        records[str(state)]=(target,record)
        write(fixture/'roles/ideation/manifest.json',dict(session=record['session'],launch=record['id']))
        before=dict(record=record,process=dict(shell_pid=shell,leader=cli))
        write(product.BASE/target['label']/'ideation.before.json',before)
        stages=product.BASE/target['label']/'window-1/stages.jsonl'; write(stages,dict(time=stamp(1020)))
        write(stages.parent/'electron-owner.json',owner(601+index,1018))
        old=dict(fixture=str(fixture),argv=['runner','--source',target['source']],commands=[],status='INCOMPLETE')
        oldpath=product.HERE/(target['label']+'.run.json'); write(oldpath,old); originals[oldpath]=oldpath.read_text(encoding='utf-8')
        live.update({daemon:owner(daemon,1005),shell:owner(shell,1012),cli:owner(cli,1013)})
        argv[daemon]=['/fixture/node',target['source']+'/workbench/src/daemon.ts',str(state),'{}']
        argv[shell]=[record['shell'],*record['shell_argv']]; argv[cli]=record['argv']
    product.TARGETS=targets
    if scenario=='mismatch': live[targets[1]['cli']]=owner(targets[1]['cli'],9999)
    def read(pid):
        counts[pid]=counts.get(pid,0)+1
        value=live.get(pid)
        if scenario=='changed' and pid==targets[0]['daemon'] and counts[pid]>=3 and value is not None:
            return dict(value,command='replacement process')
        return value
    def request(state,command,credential,**fields):
        target,record=records[str(state)]; calls.append((target['label'],command))
        if command=='daemon_status': return dict(pid=target['daemon'],root=str(state))
        if command=='orchestration_events': return dict(events=[dict(type='daemon_started',time=stamp(1010),data=dict(pid=target['daemon'],argv=argv[target['daemon']]))])
        if command=='pane_process_info': return dict(shell_pid=target['shell'],leader=target['cli'],native_session=record['session'],failed=None,
            processes=[dict(pid=target['shell'],ppid=target['daemon']),dict(pid=target['cli'],ppid=target['shell'])])
        assert command=='daemon_stop'
        for key in ['daemon','shell','cli']: live[target[key]]=None
        (state/'daemon.pid').unlink(); (state/'control.sock').unlink(); return dict(ok=True)
    archives=[]
    def archive(fixture,destination):
        target=next(t for t in targets if t['fixture']==str(fixture))
        assert all(live[target[k]] is None for k in ['daemon','shell','cli']), 'Archive requires independent writer absence'
        assert not (fixture/'operator-1.json').exists(), 'Private credential must not enter archive'
        archives.append(target['label']); return dict(bytes=123,files=4,comparison=True)
    product.read_process=read; product.native_argv=lambda pid:argv[pid]; product.operator_request=request; product.archive_fixture=archive
    with patch.object(product.os.path,'ismount',return_value=True),patch.object(sys,'argv',['cleanup_failed_01.py','--label','cleanup-test','--approval-ref','local supplied boundaries']):
        with __import__('contextlib').redirect_stdout(__import__('io').StringIO()): rc=product.main()
    stopped=[label for label,command in calls if command=='daemon_stop']
    if scenario in ['mismatch','changed']:
        assert not stopped, 'All original identities must be confirmed before any stop'
        assert rc==1 and not archives
    else:
        assert rc==0 and stopped==['run-0','run-1'] and archives==stopped
    assert all(path.read_text(encoding='utf-8')==text for path,text in originals.items()), 'Original failure summaries must remain unchanged'

report=dict(status='INCOMPLETE',scope='fixed cleanup entry over supplied process/socket/archive boundaries; no actual residual process or archive proof',checks=[])
try:
    real=module(source)
    assert {t['fixture']:{t[k] for k in ['daemon','shell','cli']} for t in real.TARGETS}=={
        '/private/tmp/t078-2-t096-bn5td39u':{67586,67659,67660},'/private/tmp/t078-2-t096-20qgx07u':{67769,67833,67839}}
    assert 'os.kill(' not in source and 'killpg(' not in source and 'forceTerminate' not in source
    for scenario in ['normal','mismatch','changed']:
        exercise(source,scenario); report['checks'].append(scenario)
    needle="            for owner in plan['owners']: require_same(owner)"
    assert needle in source
    first,last=source.rsplit(needle,1); mutant=first+'            pass'+last
    try: exercise(mutant,'changed')
    except AssertionError as error:
        report['mutant']=dict(rejected=str(error).startswith('All original identities'),error=str(error))
    assert report['mutant']['rejected'], 'Removing the final identity check must permit an unsafe stop and fail this contract'
    report['checks']+=['six_fixed_pids_only','no_force_signal','exit_before_archive','credential_excluded','original_failures_preserved']
    report['status']='PASS'
except BaseException as error:
    report['error']=str(error); report['traceback']=__import__('traceback').format_exc()
with Path(sys.argv[1]).open('x',encoding='utf-8') as output: output.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)); sys.exit(0 if report['status']=='PASS' else 1)
