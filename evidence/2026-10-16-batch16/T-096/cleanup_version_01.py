#!/usr/bin/env python3
"""CONTROLLER ONLY: stop/archive ONLY version-b-01, fixture lqlqpvha.

No CLI, daemon, Electron, model, keys, hooks, signals or force quit are started.
Require exact journal-bound PID/start/full command for daemon 79664, epoch 2,
exact native argv, matching authenticated socket, and no daemon children.
Every other registered PID, including Electron 79678, must already be absent.
Recheck all identities and socket epoch immediately before ONE daemon_stop.
<=120 owned PID queries plus two process tables (unrelated argv is never saved),
two native argv reads, <=5 operator requests (30s each), 20s bounded exit wait.
Any preflight mismatch stops before daemon_stop. No retry of a mutation.
After exit, copy/compare the fixture to its original external run/fixture; retain
all originals, exclude only private operator-1/2.json. No credential contents in
evidence, hashes or overwrite. One bounded stdout result; old run stays unchanged.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'T-091'))
BASE=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')
FIXTURE=Path('/private/tmp/t078-2-t096-lqlqpvha')
DAEMON=79664
ELECTRON=79678
from restart_cleanup import probe_process, native_argv, operator_request
from archive_failed_02 import copy_view
from run_red import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True); parser.add_argument('--approval-ref',required=True)
    args=parser.parse_args()
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.label): raise RuntimeError('invalid cleanup label')
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('mounted external evidence volume required')
    summary=HERE/(args.label+'.run.json'); output=BASE/args.label
    if summary.exists(): raise RuntimeError('new summary label required')
    output.mkdir(parents=True,exist_ok=False)
    state=FIXTURE/'state'; folder=BASE/'version-b-01'; credential=FIXTURE/'operator-2.json'
    result=dict(status='INCOMPLETE',argv=sys.argv,approval_ref=args.approval_ref,fixture=str(FIXTURE),process_reads=0,stop_commands=0,cleanup_complete=False,model_turns=0,keys=[])
    owners=[]
    def inspect(pid):
        result['process_reads']+=1
        if result['process_reads']>120: raise RuntimeError('process read budget exceeded')
        return probe_process(pid)
    def identities(require_daemon):
        for owner in owners:
            current=inspect(owner['pid'])
            if owner['pid']==DAEMON and require_daemon:
                if current!=owner: raise RuntimeError('fixed daemon PID/start/full command changed')
            elif current is not None: raise RuntimeError('another registered PID is present: '+str(owner['pid']))
    def no_children():
        value=subprocess.run(['/bin/ps','-ww','-axo','pid=,ppid=,command='],capture_output=True,text=True,timeout=5,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'})
        if value.returncode or value.stderr.strip() or len(value.stdout)>1024*1024: raise RuntimeError('PID/PPID table unavailable')
        rows=[line.strip().split(maxsplit=2) for line in value.stdout.splitlines() if line.strip()]
        if any(len(row)!=3 for row in rows): raise RuntimeError('PID/PPID table invalid')
        for pid,parent,command in rows:
            if int(parent)==DAEMON: raise RuntimeError('fixed daemon has an unexpected child; preserve fixture')
            if int(pid)!=DAEMON and (str(FIXTURE) in command or str(folder) in command):
                raise RuntimeError('unexpected fixture writer remains: '+pid)
    def request(command): return operator_request(state,command,credential)
    try:
        if FIXTURE.resolve(strict=True)!=FIXTURE: raise RuntimeError('fixture path changed')
        original=json.loads((HERE/'version-b-01.run.json').read_text(encoding='utf-8'))
        if original['fixture']!=str(FIXTURE) or original['daemon_start_receipt']!=dict(epoch=2,pid=DAEMON,state=str(state)) or original['electron_start_receipt']['pid']!=ELECTRON:
            raise RuntimeError('fixed fixture/epoch/PID binding changed')
        journal=[]
        for line in (folder/'ownership.jsonl').read_text(encoding='utf-8').splitlines():
            owner=json.loads(line)['owner']
            prior=next((old for old in journal if old['pid']==owner['pid']),None)
            if prior is not None and prior!=owner: raise RuntimeError('ownership journal changed a PID identity')
            if prior is None: journal.append(owner)
        if journal!=original['owned']: raise RuntimeError('ownership journal differs from original run')
        owners=list(original['owned'])
        expected=next(owner for owner in owners if owner['pid']==DAEMON)
        if ELECTRON not in [owner['pid'] for owner in owners] or len({owner['pid'] for owner in owners})!=len(owners): raise RuntimeError('fixed writer set invalid')
        if (folder/'fixture').exists() or (FIXTURE/'operator-3.json').exists(): raise RuntimeError('archive/later epoch exists; preserve it')
        if (state/'daemon.pid').is_symlink() or (state/'daemon.pid').read_text(encoding='utf-8').strip()!=str(DAEMON): raise RuntimeError('daemon.pid changed')
        identities(True); no_children()
        status=request('daemon_status')
        if status['pid']!=DAEMON or status['root']!=str(state): raise RuntimeError('socket does not belong to the fixed daemon')
        started=[e for e in request('orchestration_events')['events'] if e['type']=='daemon_started' and e['data']['pid']==DAEMON]
        if len(started)!=1: raise RuntimeError('fixed daemon start event is not unique')
        argv=started[0]['data']['argv']
        if argv[1]!=str(Path('/Users/luckye/Documents/Code/a2a-wt-t096/workbench/src/daemon.ts')) or argv[2]!=str(state) or native_argv(DAEMON)!=argv:
            raise RuntimeError('fixed daemon native argv changed')
        write_json(output/'preflight.json',dict(fixture=str(FIXTURE),owners=owners,daemon=expected,epoch=2,other_registered_pids_absent=True,children=[],daemon_argv=argv))
        identities(True); no_children()
        if request('daemon_status')!=status or native_argv(DAEMON)!=argv: raise RuntimeError('daemon epoch/argv changed before stop')
        result['stop_commands']=1
        try:
            result['stop_receipt']=request('daemon_stop')
            if result['stop_receipt'].get('stopping') is not True: raise RuntimeError('daemon_stop not acknowledged')
        except BaseException as error:
            result['stop_error']=str(error)  # No replay: independently check exit below.
        deadline=time.monotonic()+20
        remaining=list(owners)
        while True:
            present=[]
            pending=[]
            for owner in remaining:
                current=inspect(owner['pid'])
                if current is not None:
                    if current['started']!=owner['started']: raise RuntimeError('registered PID reused during exit; preserve fixture')
                    present.append(current['pid']); pending.append(owner)
            remaining=pending
            if not present and not (state/'daemon.pid').exists() and not (state/'control.sock').exists(): break
            if time.monotonic()>=deadline: raise TimeoutError('registered writer/endpoint exit unconfirmed')
            time.sleep(.25)
        identities(False)
        excluded={}
        for name in ['operator-1.json','operator-2.json']:
            path=FIXTURE/name
            if path.is_symlink(): raise RuntimeError('private credential path changed')
            if path.exists(): excluded[name]=dict(reason='private operator credential; original retained, contents not archived')
        stats=copy_view(FIXTURE,folder/'fixture',excluded)
        manifest=dict(original=str(FIXTURE),archive=str(folder/'fixture'),**stats,excluded=excluded,
            comparison_scope='source fixture excluding listed private credentials; all originals retained',replay=shlex.join(sys.argv))
        write_json(HERE/('version-b-01-'+args.label+'.archive.json'),manifest)
        result.update(cleanup_complete=True,files=stats['files'],bytes=stats['bytes'],comparison=stats['comparison'])
        if 'stop_error' not in result: result['status']='PASS'
    except BaseException as error:
        result['error']=str(error); result['traceback']=traceback.format_exc()
        result['handoff']=dict(reason=str(error),fixture=str(FIXTURE),daemon=DAEMON,electron=ELECTRON,owned=owners,policy='No force quit, retry, new epoch or overwrite')
    finally:
        try: write_json(summary,result)
        except BaseException as error: result['status']='INCOMPLETE'; result['error']='summary write failed: '+str(error)
        print(json.dumps(dict(status=result['status'],summary=str(summary),cleanup=result['cleanup_complete'],handoff=result.get('handoff'),stop_error=result.get('stop_error'))))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
