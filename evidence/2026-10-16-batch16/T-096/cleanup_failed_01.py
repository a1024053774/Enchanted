#!/usr/bin/env python3
"""CONTROLLER ONLY: close ONLY red-b-01 and tracer-b-01 from controller #90.

No Electron/daemon/CLI/model starts; no keys/hooks/login; no signals/force quit.
Reads /bin/ps and macOS sysctl for the six fixed PIDs plus recorded Electron
PIDs, verifies original argv, start-time bounds, parentage and fixture identity.
Uses each fixture's private operator credential on its existing control.sock to
send daemon_status/orchestration_events/pane_process_info and daemon_stop.
Two stop commands maximum, no replay. <=120 runner ps readbacks, <=6 native argv
reads and two server process-info reads; 20-second exit wait.
All six PIDs are preflighted before the first stop; identities are read again
immediately before stopping each daemon. Any mismatch stops without more writes.
The old runner did not persist daemon/shell/CLI lstart. Their birth-time checks
use the ORIGINAL launch-created/daemon-started/first-Electron timestamps, then
require exact equality with this cleanup's preflight lstart before each stop.
This limitation is recorded; it is not presented as a historical exact lstart.
After all registered writers exit, remove private operator files, copy fixtures
into their original external run directories/fixture, compare files and bytes,
retain originals. No overwrite; no hashes. New cleanup summary only, old failed
run summaries remain unchanged. Stdout is one bounded result line.
"""
import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import shlex
import sys
import time
import traceback

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'T-091'))
from run_red import archive_fixture, write_json
from owned_electron import read_process
from restart_cleanup import native_argv, operator_request

TARGETS=[
    dict(label='red-b-01',fixture='/private/tmp/t078-2-t096-bn5td39u',source='/Users/luckye/Documents/Code/a2a',daemon=67586,shell=67659,cli=67660),
    dict(label='tracer-b-01',fixture='/private/tmp/t078-2-t096-20qgx07u',source='/Users/luckye/Documents/Code/a2a-wt-t096',daemon=67769,shell=67833,cli=67839),
]
BASE=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')


def birth_seconds(owner):
    return time.mktime(time.strptime(owner['started'],'%a %b %d %H:%M:%S %Y'))


def within_original_interval(owner, lower, upper):
    started=birth_seconds(owner)
    if not math.floor(lower)<=started<=math.ceil(upper):
        raise RuntimeError('PID birth is outside its original launch interval: '+str(owner['pid']))


def parse_saved_ps(text):
    pieces=text.strip().split(maxsplit=6)
    if len(pieces)!=7: raise RuntimeError('saved process identity incomplete')
    return dict(pid=int(pieces[0]),started=' '.join(pieces[1:6]),command=pieces[6])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--approval-ref',required=True)
    args=parser.parse_args()
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.label): raise RuntimeError('invalid cleanup label')
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('mounted external evidence volume required')
    output=BASE/args.label; output.mkdir(parents=True,exist_ok=False)
    summary=HERE/(args.label+'.run.json')
    if summary.exists(): raise RuntimeError('choose a new cleanup label')
    result=dict(status='INCOMPLETE',approval_ref=args.approval_ref,argv=sys.argv,targets=[],process_reads=0,model_turns=0,keys=[],stop_commands=0)
    plans=[]

    def inspect(pid):
        result['process_reads']+=1
        if result['process_reads']>120: raise RuntimeError('cleanup process read budget exhausted')
        return read_process(pid)

    def require_same(owner):
        current=inspect(owner['pid'])
        if current is not None and current!=owner: raise RuntimeError('PID/start/full command changed: '+str(owner['pid']))
        return current

    def request(plan,command,**fields):
        return operator_request(plan['state'],command,plan['credential'],**fields)

    def check_absent(plan):
        for owner in plan['owners']:
            if require_same(owner) is not None: return False
        return not (plan['state']/'daemon.pid').exists() and not (plan['state']/'control.sock').exists()

    try:
        # No daemon_stop is sent unless BOTH fixed fixtures have passed preflight.
        for target in TARGETS:
            fixture=Path(target['fixture']); folder=BASE/target['label']; state=fixture/'state'; credential=fixture/'operator-1.json'
            original=json.loads((HERE/(target['label']+'.run.json')).read_text(encoding='utf-8'))
            if original['fixture']!=str(fixture): raise RuntimeError('original fixture binding changed')
            source_arg=original['argv'][original['argv'].index('--source')+1]
            if source_arg!=target['source']: raise RuntimeError('original source binding changed')
            if (folder/'fixture').exists(): raise RuntimeError('archive destination exists; preserve it and choose a manual reconciliation')
            if (fixture/'operator-2.json').exists(): raise RuntimeError('a later daemon epoch exists; fixed cleanup no longer applies')
            before=json.loads((folder/'ideation.before.json').read_text(encoding='utf-8'))
            record,process=before['record'],before['process']
            manifest=json.loads((fixture/'roles/ideation/manifest.json').read_text(encoding='utf-8'))
            if record['session']!=manifest['session'] or record['id']!=manifest['launch'] or record['worktree']!=str(fixture/'repo'):
                raise RuntimeError('original session/fixture binding changed')
            if process['shell_pid']!=target['shell'] or process['leader']!=target['cli']:
                raise RuntimeError('recorded CLI/shell PID differs from controller #90')
            plan=dict(target=target,fixture=fixture,folder=folder,state=state,credential=credential,owners=[],record=record)
            daemon=inspect(target['daemon']); shell=inspect(target['shell']); cli=inspect(target['cli'])
            if daemon is None:
                if shell is not None or cli is not None: raise RuntimeError('daemon absent while its agent remains; no force cleanup is authorized')
            else:
                if (state/'daemon.pid').read_text(encoding='utf-8').strip()!=str(target['daemon']): raise RuntimeError('daemon.pid changed')
                status=request(plan,'daemon_status')
                if status['pid']!=target['daemon'] or status['root']!=str(state): raise RuntimeError('socket server is not the fixed fixture daemon')
                events=request(plan,'orchestration_events')['events']
                started=[e for e in events if e['type']=='daemon_started' and e['data']['pid']==target['daemon']]
                if len(started)!=1: raise RuntimeError('original daemon start record is not unique')
                expected_daemon_argv=started[0]['data']['argv']
                if expected_daemon_argv[1]!=str(Path(target['source'])/'workbench/src/daemon.ts') or expected_daemon_argv[2]!=str(state): raise RuntimeError('daemon launch argv is outside the fixed fixture')
                if native_argv(target['daemon'])!=expected_daemon_argv: raise RuntimeError('daemon full argv changed')
                within_original_interval(daemon,(fixture/'launch.json').stat().st_mtime,datetime.fromisoformat(started[0]['time'].replace('Z','+00:00')).timestamp())
                if shell is None or cli is None: raise RuntimeError('expected live shell/CLI disappeared; stop for controller reconciliation')
                stages=[json.loads(line) for line in (folder/'window-1/stages.jsonl').read_text(encoding='utf-8').splitlines()]
                upper=datetime.fromisoformat(stages[0]['time'].replace('Z','+00:00')).timestamp()
                lower=datetime.fromisoformat(record['created_at'].replace('Z','+00:00')).timestamp()
                for owner,expected in [(shell,[record['shell'],*record['shell_argv']]),(cli,record['argv'])]:
                    within_original_interval(owner,lower,upper)
                    if native_argv(owner['pid'])!=expected: raise RuntimeError('shell/CLI full argv changed: '+str(owner['pid']))
                live=request(plan,'pane_process_info',thread=record['thread'])
                if live['shell_pid']!=target['shell'] or live['leader']!=target['cli'] or live['native_session']!=record['session'] or live['failed']:
                    raise RuntimeError('daemon no longer owns the original native session')
                rows={row['pid']:row for row in live['processes']}
                if rows[target['shell']]['ppid']!=target['daemon'] or rows[target['cli']]['ppid']!=target['shell']:
                    raise RuntimeError('original daemon/shell/CLI ancestry changed')
                plan['owners'].extend([daemon,shell,cli])
            # Include every Electron PID whose complete identity the failed run
            # actually saved. An unexpected survivor stops before daemon_stop.
            electron_owner=json.loads((folder/'window-1/electron-owner.json').read_text(encoding='utf-8'))
            electron_records={electron_owner['pid']:{k:electron_owner[k] for k in ['pid','started','command']}}
            for command in original['commands']:
                argv=command['argv']
                if argv[:2]==['/bin/ps','-ww'] and '-p' in argv:
                    saved=(folder/f"command-{command['id']}.stdout.txt").read_text(encoding='utf-8')
                    if saved.strip():
                        owner=parse_saved_ps(saved)
                        if '/Electron.app/' in owner['command']: electron_records[owner['pid']]=owner
            for owner in electron_records.values():
                if require_same(owner) is not None: raise RuntimeError('recorded Electron process remains; controller must reconcile it: '+str(owner['pid']))
            plan['owners'].extend(electron_records.values()); plans.append(plan)
            # Recheck all live identities against the just-observed exact start
            # time and full command. Birth bounds remain separately disclosed.
            for owner in plan['owners']: require_same(owner)
            write_json(output/(target['label']+'.preflight.json'),dict(target=target,owners=plan['owners'],
                historical_lstart='not persisted by original runner; checked against original artifact interval',
                exact_pre_stop_check='this preflight PID/start/full command must still match before daemon_stop'))
        for plan in plans:
            target=plan['target']
            progress=dict(label=target['label'],cleanup_complete=False,writers_absent=False,original_status='INCOMPLETE')
            result['targets'].append(progress)
            for owner in plan['owners']: require_same(owner)
            current=inspect(target['daemon'])
            if current is not None:
                if request(plan,'daemon_status')['pid']!=target['daemon']: raise RuntimeError('daemon endpoint changed before stop')
                result['stop_commands']+=1
                progress['stop_accepted']=request(plan,'daemon_stop').get('stopping',False)
            deadline=time.monotonic()+20
            while not check_absent(plan):
                if time.monotonic()>=deadline: raise TimeoutError('registered writer exit not confirmed; preserve fixture')
                time.sleep(.25)
            progress['writers_absent']=True
            if plan['credential'].is_symlink(): raise RuntimeError('credential path changed; no archive')
            if plan['credential'].exists(): plan['credential'].unlink()
            stats=archive_fixture(plan['fixture'],plan['folder']/'fixture')
            manifest=dict(original=str(plan['fixture']),archive=str(plan['folder']/'fixture'),bytes=stats['bytes'],files=stats['files'],comparison=stats['comparison'],replay=shlex.join(sys.argv))
            write_json(HERE/(target['label']+'-'+args.label+'.archive.json'),manifest)
            progress.update(cleanup_complete=True,archive=manifest['archive'],files=stats['files'],bytes=stats['bytes'])
        result['status']='PASS'
    except BaseException as error:
        result['error']=str(error); result['traceback']=traceback.format_exc()
        result['handoff']=dict(reason=str(error),targets=TARGETS,ownership_directory=str(output),policy='No force kill, no new attempt, no overwrite; controller reconciliation required')
    finally:
        try: write_json(summary,result)
        except BaseException as error:
            result['status']='INCOMPLETE'; result['error']='Cleanup summary write failed: '+str(error)
        print(json.dumps(dict(status=result['status'],summary=str(summary),cleanup=[t['label'] for t in result['targets'] if t['cleanup_complete']],handoff=result.get('error'),ownership=str(output))))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
