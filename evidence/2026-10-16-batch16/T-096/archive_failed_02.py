#!/usr/bin/env python3
"""CONTROLLER ONLY — archive exactly the two failed -02 fixtures from #91.

No CLI/daemon/Electron/model starts, signals, daemon_stop, keys or source writes.
Read-only ps: <=56 PID queries (5s each); <=6 Unix endpoint probes (2s each).
Require all 14 fixed, journal-bound PIDs absent. rc1 plus empty stdout/stderr
means absent; all other errors stop. A live or unknown endpoint also stops.
Copy the stopped fixture view and compare file counts/bytes/path entries; retain
ALL original files. Dead control.sock cannot be copied as a regular file, and
operator credentials must not enter evidence: exclude only those exact paths,
record their metadata/reasons, never read credentials or remove source files.
No hashes, overwrite, cleanup of another run, or inference of test PASS.
New summary/manifests only; original failed .run.json files remain unchanged.
"""
import argparse
import errno
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import stat
import sys
import traceback

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'T-091'))
from run_red import inventory, write_json
from restart_cleanup import probe_process

BASE=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096')
TARGETS=[
    dict(label='red-b-02',fixture='/private/tmp/t078-2-t096-dkri52ul',daemon=15789,pids=[15789,15840,15841,15853,15864,15857,15858]),
    dict(label='tracer-b-02',fixture='/private/tmp/t078-2-t096-j4p4ocqz',daemon=16015,pids=[16015,16098,16099,16115,16200,16199,16208]),
]


def endpoint_state(fixture,daemon):
    result={}
    state=fixture/'state'
    for name in ['daemon.pid','control.sock']:
        path=state/name
        try: info=path.lstat()
        except FileNotFoundError:
            result[name]=dict(state='absent'); continue
        if info.st_uid!=os.getuid(): raise RuntimeError('endpoint owner changed')
        meta=dict(mode=stat.S_IMODE(info.st_mode),uid=info.st_uid,inode=info.st_ino,device=info.st_dev)
        if name=='daemon.pid':
            if not stat.S_ISREG(info.st_mode): raise RuntimeError('daemon.pid is not a regular file')
            value=path.read_text(encoding='utf-8')
            if value.strip()!=str(daemon): raise RuntimeError('daemon.pid does not belong to this fixed run')
            result[name]=dict(meta,state='stale_pid_file',pid=daemon)
        else:
            if not stat.S_ISSOCK(info.st_mode): raise RuntimeError('control.sock is not a socket')
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(2); code=client.connect_ex(str(path))
            if code!=errno.ECONNREFUSED:
                raise RuntimeError('control.sock is live or unknown: '+str(code))
            result[name]=dict(meta,state='stale_socket',probe='ECONNREFUSED')
    return result


def fixture_view(root,excluded):
    if not stat.S_ISDIR(root.lstat().st_mode): raise RuntimeError('fixture root must be a real directory')
    entries=[]; pending=[root]
    while pending:
        for child in os.scandir(pending.pop()):
            path=Path(child.path); relative=path.relative_to(root).as_posix()
            if relative in excluded: continue
            info=child.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                target=os.readlink(path); entries.append(dict(path=relative,kind='symlink',bytes=len(os.fsencode(target)),target=target))
            elif stat.S_ISDIR(info.st_mode):
                entries.append(dict(path=relative,kind='directory')); pending.append(path)
            elif stat.S_ISREG(info.st_mode): entries.append(dict(path=relative,kind='file',bytes=info.st_size))
            else: raise RuntimeError('unexpected special file retained for controller: '+relative)
    return dict(entries=sorted(entries,key=lambda entry:entry['path']),files=sum(e['kind']!='directory' for e in entries),bytes=sum(e.get('bytes',0) for e in entries))


def copy_view(fixture,destination,excluded):
    before=fixture_view(fixture,excluded)
    def ignore(directory,names):
        return [name for name in names if (Path(directory)/name).relative_to(fixture).as_posix() in excluded]
    shutil.copytree(fixture,destination,symlinks=True,ignore=ignore)
    after=inventory(destination)
    if before['files']!=after['files'] or before['bytes']!=after['bytes'] or before['entries']!=after['entries']:
        raise RuntimeError('archive file count/bytes/paths mismatch; both copies retained')
    if fixture_view(fixture,excluded)!=before: raise RuntimeError('source changed while copying; both copies retained')
    return dict(files=before['files'],bytes=before['bytes'],comparison=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True); parser.add_argument('--approval-ref',required=True)
    args=parser.parse_args()
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.label): raise RuntimeError('invalid archive label')
    if not os.path.ismount('/Volumes/WD-Elements'): raise RuntimeError('mounted external evidence volume required')
    summary=HERE/(args.label+'.run.json')
    if summary.exists(): raise RuntimeError('choose a new archive label')
    output=BASE/args.label; output.mkdir(parents=True,exist_ok=False)
    result=dict(status='INCOMPLETE',argv=sys.argv,approval_ref=args.approval_ref,targets=[],process_reads=0,model_turns=0,keys=[],source_writes=0)
    plans=[]
    def require_absent(target):
        for pid in target['pids']:
            result['process_reads']+=1
            if result['process_reads']>56: raise RuntimeError('PID read budget exceeded')
            if probe_process(pid) is not None: raise RuntimeError('registered PID is present; no archive: '+str(pid))
    try:
        for target in TARGETS:
            fixture=Path(target['fixture']); folder=BASE/target['label']
            original=json.loads((HERE/(target['label']+'.run.json')).read_text(encoding='utf-8'))
            journal=[json.loads(line)['owner'] for line in (folder/'ownership.jsonl').read_text(encoding='utf-8').splitlines()]
            owners={}
            for owner in journal:
                if owner['pid'] in owners and owners[owner['pid']]!=owner: raise RuntimeError('ownership journal changed identity')
                owners[owner['pid']]=owner
            if original['fixture']!=str(fixture) or set(owners)!=set(target['pids']) or {o['pid'] for o in original['owned']}!=set(target['pids']):
                raise RuntimeError('fixture or fixed PID set does not match original evidence')
            if original['daemon_start_receipt']['epoch']!=1 or (folder/'daemon-start-2.json').exists() or (fixture/'operator-2.json').exists():
                raise RuntimeError('a later epoch exists; this fixed archive command does not apply')
            if (folder/'fixture').exists(): raise RuntimeError('archive already exists; do not overwrite')
            require_absent(target); endpoints=endpoint_state(fixture,target['daemon'])
            excluded={}
            if endpoints['control.sock']['state']=='stale_socket': excluded['state/control.sock']=dict(reason='dead IPC endpoint; original retained',**endpoints['control.sock'])
            credential=fixture/'operator-1.json'
            if credential.exists() or credential.is_symlink():
                info=credential.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
                    raise RuntimeError('operator credential metadata unsafe; original retained')
                excluded['operator-1.json']=dict(reason='private operator credential; original retained, contents not read',bytes=info.st_size,mode=stat.S_IMODE(info.st_mode))
            plan=dict(target=target,fixture=fixture,folder=folder,endpoints=endpoints,excluded=excluded)
            plans.append(plan)
            write_json(output/(target['label']+'.preflight.json'),dict(target=target,all_registered_pids_absent=True,endpoints=endpoints,excluded=excluded))
        for plan in plans:
            target=plan['target']; fixture=plan['fixture']; destination=plan['folder']/'fixture'
            require_absent(target)
            if endpoint_state(fixture,target['daemon'])!=plan['endpoints']: raise RuntimeError('endpoint changed after preflight')
            counts=copy_view(fixture,destination,plan['excluded'])
            require_absent(target)
            if endpoint_state(fixture,target['daemon'])!=plan['endpoints']: raise RuntimeError('endpoint changed while copying; archive retained for controller')
            manifest=dict(original=str(fixture),archive=str(destination),**counts,replay=shlex.join(sys.argv),excluded=plan['excluded'],
                comparison_scope='source fixture excluding listed dead IPC and private credential paths; original unchanged')
            write_json(HERE/(target['label']+'-'+args.label+'.archive.json'),manifest)
            result['targets'].append(dict(label=target['label'],archive_complete=True,original_status='INCOMPLETE',**counts,excluded=list(plan['excluded'])))
        result['status']='PASS'
    except BaseException as error:
        result['error']=str(error); result['traceback']=traceback.format_exc()
        result['handoff']=dict(reason=str(error),targets=TARGETS,ownership=str(output),policy='No source mutation, signal, stop request or overwrite; controller reconciliation required')
    finally:
        try: write_json(summary,result)
        except BaseException as error:
            result['status']='INCOMPLETE'; result['error']='Archive summary write failed: '+str(error)
        print(json.dumps(dict(status=result['status'],summary=str(summary),archived=[t['label'] for t in result['targets']],handoff=result.get('error'))))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
