"""Controller-only real delivery, five turns, explicit executor score, no retry."""
import argparse
import contextlib
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback

from command_evidence import CommandLog, command_json
from fixture_artifacts import archive_stopped_database
from run_t076_quality_red import archive_directory

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / 'evidence/2026-10-11-batch13/T-076/card-2'
BUNDLE = CARD / 'real-delivery-02'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--approval-file', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    log = CommandLog(out); policy = json.loads((BUNDLE / 'launch-policy.json').read_text())
    root, state, repo = map(Path, (policy['root'], policy['state'], policy['repo']))
    source = root / 'source'; homes = [Path(policy[r]['home']) for r in ('worker', 'reviewer')]
    host = None; streams = []; own = False; started = False; reserved = False; pids = set(); launches = {}
    result = dict(status='INCOMPLETE', product_status='INCOMPLETE', real_turns_reserved=0, observed_main_turns=None,
                  home_removed=False, slots=policy['slots'], argv=sys.argv)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_', 'NODE_COMPILE_CACHE'))}
    env.update(GIT_AUTHOR_NAME='T076 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T076 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    git_env = {**env, 'GIT_CONFIG_NOSYSTEM':'1', 'GIT_CONFIG_GLOBAL':os.devnull, 'GIT_CONFIG_COUNT':'2',
               'GIT_CONFIG_KEY_0':'core.hooksPath', 'GIT_CONFIG_VALUE_0':os.devnull,
               'GIT_CONFIG_KEY_1':'commit.gpgsign', 'GIT_CONFIG_VALUE_1':'false'}

    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
    def run(argv, cwd=ROOT, command_env=env, check=True):
        p = log.run(argv, cwd=cwd, env=command_env, timeout=90)
        if check and p.returncode: raise RuntimeError({'command_failed':p.evidence})
        return p
    cli = [policy['node'], policy['cli'], '--state', str(state)]
    def call(command, *extra, check=True):
        p = run([*cli, command, *extra], check=False); value = command_json(p)
        if check and (p.returncode or not value.get('ok')): raise RuntimeError({'gate_failed':value, 'command':p.evidence})
        return value
    def git(*extra, cwd=repo): return run(['git', *extra], cwd=cwd, command_env=git_env).stdout.strip()
    def events(): return call('orchestration_events')['events']
    def records(rows, launch=None): return [e['data']['record'] for e in rows if e['type']=='native_record' and (launch is None or e['launch']==launch)]
    def turns(rows, launch, event):
        return [r['payload']['turn_id'] for r in records(rows, launch) if r['type']=='event_msg' and r['payload'].get('type')==event]
    def ledger(row):
        with (CARD / 'real-turn-budget.jsonl').open('a+', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX); f.seek(0); prior = [json.loads(l) for l in f if l.strip()]
            if row['kind']=='reservation':
                if sum(r['reserved'] for r in prior if r['kind']=='reservation')!=1 or \
                   [r['observed_main_turns'] for r in prior if r['kind']=='observation']!=[1]:
                    raise RuntimeError('Exactly the completed slot-1 probe is required; no repeat reservation.')
            f.seek(0,2); f.write(json.dumps(row)+'\n'); f.flush(); os.fsync(f.fileno())
    def guard(rows):
        if len(turns(rows,None,'task_started'))>5: raise RuntimeError('Unexpected sixth input; preserve and stop.')
        if any(r['type']=='event_msg' and r['payload'].get('type')=='error' for r in records(rows)):
            raise RuntimeError('Native CLI error; preserve and stop without changing account/model.')
        if any(e['type'] in ('permission_wait','stop_transfer_failed','event_write_failed','native_final_read_failed') for e in rows):
            raise RuntimeError('A permission or protocol boundary failed; no extra input.')
    def release(thread, label):
        deadline = time.monotonic()+90
        while True:
            info = call('pane_process_info','--thread',thread); pids.add(info['shell_pid'])
            pids.update(p['pid'] for p in info['processes'])
            if info.get('failed'): raise RuntimeError({'pane_failed':info})
            if info.get('leader'): break
            if time.monotonic()>deadline: raise RuntimeError('No confirmed foreground leader; do not inject input.')
            time.sleep(0.2)
        save(label+'-before-release.json',info)
        call('pane_release','--thread',thread,'--reason',approval['decision_ref'])
        return info
    def worker_boundary(count):
        deadline = time.monotonic()+600
        while True:
            rows = events(); guard(rows)
            starts, ends = turns(rows,launches['worker']['id'],'task_started'), turns(rows,launches['worker']['id'],'task_complete')
            if len(starts)>count: raise RuntimeError('Worker advanced beyond the approved boundary.')
            pane = call('pane_status','--thread',attempt['thread_id'])
            if pane.get('failed'): raise RuntimeError({'worker_failed':pane})
            if len(starts)==len(ends)==count and starts==ends and pane['state']=='idle' and not pane['queued'] and not pane['writing']:
                save('worker-boundary-'+str(count)+'.json',dict(starts=starts,ends=ends,pane=pane))
                return rows, starts
            if time.monotonic()>deadline: raise RuntimeError('Worker boundary timed out; no retry.')
            time.sleep(0.5)

    try:
        approval = json.loads(args.approval_file.read_text())
        if not (approval.get('approved') is True and approval.get('approved_by')=='executor' and approval.get('policy')==policy['id']
                and approval.get('slots')==[2,3,4,5,6] and approval.get('root_turn_limit')==5 and approval.get('decision_ref')):
            raise RuntimeError('Explicit approval of this five-turn instance is required.')
        save('approval-readback.json',approval)
        if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk missing.')
        if root.exists() or root.is_symlink(): raise RuntimeError('Owned fixed root exists; never reuse it.')
        if run([policy['node'],'--version']).stdout.strip()!='v26.5.0': raise RuntimeError('Pinned Node changed.')
        with tarfile.open(BUNDLE / 'approval-materials.tar.gz','r:gz') as archive:
            expected=['launch-policy.json','WORKER.md','REVIEWER.md','CONTRACT.txt','oracle.py','worker.rules',
                      'worker-config.toml','reviewer-config.toml','worker-argv.txt','reviewer-argv.txt']
            if sorted(archive.getnames())!=sorted(expected): raise RuntimeError('Approved material set differs.')
            for member in archive.getmembers():
                if not member.isfile() or archive.extractfile(member).read()!=(BUNDLE / member.name).read_bytes():
                    raise RuntimeError('Approved material changed: '+member.name)
        with tarfile.open(BUNDLE / 'source-snapshot.tar.gz','r:gz') as archive:
            for member in archive.getmembers():
                if not member.isfile() or '..' in Path(member.name).parts or archive.extractfile(member).read()!=(ROOT / member.name).read_bytes():
                    raise RuntimeError('Approved source changed: '+member.name)
            root.mkdir(mode=0o700); own=True; source.mkdir(); archive.extractall(source)
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(),target_is_directory=True)
        for name in ('WORKER.md','REVIEWER.md','oracle.py','launch-policy.json'): shutil.copyfile(BUNDLE / name,root / name)
        repo.mkdir(); (repo / 'src').mkdir(); (repo / '.a2a').mkdir()
        (repo / 'src/clamp.py').write_text('def clamp(value):\n    return value\n')
        shutil.copyfile(BUNDLE / 'CONTRACT.txt',repo / 'CONTRACT.txt')
        (repo / 'host.txt').write_text('baseline\n'); (repo / '.gitignore').write_text('__pycache__/\n*.pyc\n')
        (repo / '.a2a/quality.json').write_text(json.dumps({'schema':1,'rule_checks':[{'id':'syntax-only','argv':[policy['python'],'-I','-B','-c',
            'import ast,pathlib; ast.parse(pathlib.Path("src/clamp.py").read_text())']} ]})+'\n')
        git('init','-b','main'); git('add','.'); git('commit','-m','Independent baseline B'); B=git('rev-parse','HEAD')
        inherited_hooks=run(['git','config','--get','core.hooksPath'],cwd=repo,check=False)
        if inherited_hooks.returncode!=1 or inherited_hooks.stdout:
            raise RuntimeError('An inherited hooksPath could forward an unapproved hook; stop before copying credentials.')
        baseline_oracle=run([policy['python'],'-I','-B',root / 'oracle.py',repo],check=False)
        if baseline_oracle.returncode!=1: raise RuntimeError('Known bad baseline did not fail the independent oracle.')
        for role,home in zip(('worker','reviewer'),homes):
            home.mkdir(mode=0o700); shutil.copyfile(Path.home() / '.codex/auth.json',home / 'auth.json'); (home / 'auth.json').chmod(0o600)
            shutil.copyfile(BUNDLE / (role+'-config.toml'),home / 'config.toml')
            if role=='worker':
                (home / 'rules').mkdir(); shutil.copyfile(BUNDLE / 'worker.rules',home / 'rules/default.rules')
            if sorted(p.name for p in home.iterdir())!=sorted(['auth.json','config.toml']+(['rules'] if role=='worker' else [])):
                raise RuntimeError('Unexpected isolated home contents.')
        config=dict(codex_bin=policy['codex'],codex_home=str(homes[0]),role_card=str(root / 'WORKER.md'),
            role_card_revision='real-delivery-02 approved worker',code_revision=json.loads((BUNDLE / 'source-manifest.json').read_text())['head'],
            source_snapshot=str(BUNDLE / 'source-snapshot.tar.gz'),hook_authorization=approval['decision_ref'],
            turn_limit=5,turn_authorization=approval['decision_ref'],reviewers=[dict(codex_home=str(homes[1]),
            role_card=str(root / 'REVIEWER.md'),role_card_revision='real-delivery-02 approved reviewer',hook_authorization=approval['decision_ref'])])
        (root / 'config.json').write_text(json.dumps(config)); save('launch-config.json',config)
        ledger(dict(kind='reservation',slots=[2,3,4,5,6],reserved=5,output=str(out),authorization=approval['decision_ref'])); reserved=True
        result['real_turns_reserved']=5
        streams=[(out / 'host.stdout').open('xb'),(out / 'host.stderr').open('xb')]
        argv=[policy['node'],source / 'workbench/tests/quality_real_host.ts',root / 'launch-policy.json',root / 'config.json',root / 'ready.json']
        host=subprocess.Popen(list(map(str,argv)),env=env,stdout=streams[0],stderr=streams[1],start_new_session=True); pids.add(host.pid)
        save('host-start.json',dict(pid=host.pid,argv=list(map(str,argv))))
        deadline=time.monotonic()+15
        while not (root / 'ready.json').exists():
            if host.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Host did not become ready.')
            time.sleep(0.05)
        started=True; owner=call('daemon_status')
        if owner['pid']!=host.pid or os.getpgid(host.pid)!=host.pid or os.getsid(host.pid)!=host.pid: raise RuntimeError('Detached owner identity mismatch.')
        card=dict(id=policy['task'],source=dict(ticket=str(ROOT / '.project-map/tickets/T-076-quality-chain-scoring.md'),ready_rev=1),
            goal='这是T-076-2隔离clamp夹具；按WORKER角色卡先交有bool缺口的C1，收到门禁修复指令后交满足CONTRACT.txt的C2。来源ticket只作规格绑定，不到a2a源码实现功能。',
            non_goals=['不改合同、oracle、host.txt、.gitignore、.a2a；不联网、不开子agent、不追加回合或改权限'],
            paths=dict(allow=['src/clamp.py'],deny=[]),completion_conditions=[dict(argv=[policy['python'],'-I','-B',str(root / 'oracle.py'),'{worktree}'])],
            red_commands=[],task_type='后端逻辑',repair_target=None,complexity='M',executor=dict(cli='Codex',model='gpt-6.1-sol',effort='xhigh'),base_commit=None,writer=None)
        (root / 'card.json').write_text(json.dumps(card,ensure_ascii=False)); save('card.json',card)
        call('card_save','--task',policy['task'],'--card',root / 'card.json','--expected-version','0')
        call('create','--task',policy['task'],'--repo',repo,'--branch','refs/heads/main','--card-version','1','--project','T076-real')
        attempt=call('dispatch','--task',policy['task'],'--runtime-mode','workspace-write')['attempt']; save('attempt.json',attempt)
        pane=call('pane_status','--thread',attempt['thread_id']); launches['worker']=call('launch_show','--launch',pane['launch'])['launch']
        (repo / 'host.txt').write_text('independent G\n'); git('add','host.txt'); git('commit','-m','Independent G advance'); G=git('rev-parse','HEAD')
        worker_identity=release(attempt['thread_id'],'worker'); rows,tids=worker_boundary(2)
        first=call('status','--task',policy['task'])['task']; C1=first['candidate_commit']
        if first['current_attempt']['turn_id']!=tids[0] or first['current_attempt']['attempt_id']!=attempt['attempt_id']: raise RuntimeError('ACK1 changed the delivery binding.')
        oracle=run([policy['python'],'-I','-B',root / 'oracle.py',attempt['workspace']],check=False)
        if oracle.returncode!=1 or json.loads(oracle.stdout)['failed_case']!='bool-true': raise RuntimeError('C1 did not fail at the planned bool boundary.')
        rejected=call('verify','--task',policy['task'],'--attempt',attempt['attempt_id'],check=False)
        if rejected.get('error')!='oracle_failed': raise RuntimeError({'unexpected_first_verification':rejected})
        save('first-rejection.json',rejected)
        rows,tids=worker_boundary(4); second=call('status','--task',policy['task'])['task']; C2=second['candidate_commit']
        if C1==C2 or second['current_attempt']['attempt_id']!=attempt['attempt_id'] or second['current_attempt']['turn_id']!=tids[2]:
            raise RuntimeError('Repair/ACK2 did not retain the same attempt and bind delivery to turn 3.')
        identity=call('pane_process_info','--thread',attempt['thread_id'])
        if identity['leader']!=worker_identity['leader']: raise RuntimeError('Worker leader changed across the repair.')
        verified=call('verify','--task',policy['task'],'--attempt',attempt['attempt_id'])['task']; review=verified['review']
        launches['reviewer']=call('launch_show','--launch',review['launch_id'])['launch']; save('bindings.json',dict(B=B,G=G,C1=C1,C2=C2,attempt=attempt,review=review,launches=launches))
        release(review['thread_id'],'reviewer'); deadline=time.monotonic()+600
        while True:
            rows=events(); guard(rows); current=call('status','--task',policy['task'])['task']; r=current['review']
            if r['state'] in ('unknown','failed'): raise RuntimeError({'review_not_mergeable':r})
            gate=call('events','--task',policy['task'])['events']
            if any(e['type']=='review_reclaimed' and e['details']['review_id']==review['review_id'] for e in gate): break
            if time.monotonic()>deadline: raise RuntimeError('Reviewer deadline; no repair or ACK turn.')
            time.sleep(0.5)
        if r['state']!='passed' or r['result']['verdict']!='可合并' or r['candidate_commit']!=C2: raise RuntimeError('Independent review did not approve C2.')
        missing=call('integrate','--task',policy['task'],'--attempt',attempt['attempt_id'],check=False)
        if missing.get('error')!='score_required' or git('rev-parse','HEAD')!=G: raise RuntimeError('Missing-score refusal did not preserve G.')
        save('missing-score-refusal.json',missing)
        save('ready-for-score.json',dict(task=policy['task'],attempt=attempt['attempt_id'],C2=C2,review=r,score_file=str(out / 'executor-score.json'),
             required_fields=['result','boundary_discipline','boundary_reason','engineering_taste','engineering_reason','notes']))
        print(json.dumps({'boundary':'awaiting_executor_score','evidence':str(out / 'ready-for-score.json')}),flush=True)
        deadline=time.monotonic()+300; score=out / 'executor-score.json'
        while not score.exists():
            if time.monotonic()>deadline: raise RuntimeError('Executor score not provided; no auto score or integration.')
            time.sleep(0.5)
        if call('status','--task',policy['task'])['task']['candidate_commit']!=C2: raise RuntimeError('Candidate changed before explicit scoring.')
        integrated=call('integrate','--task',policy['task'],'--attempt',attempt['attempt_id'],'--score-file',score)['task']; M=git('rev-parse','HEAD')
        if git('rev-list','--parents','-n','1',M).split()!=[M,G,C2]: raise RuntimeError('Integrated Git parents differ from G/C2.')
        for C,turn in ((C1,tids[0]),(C2,tids[2])):
            text=git('log','-1','--format=%B',C); file=out / (C+'.message'); file.write_text(text+'\n')
            parsed=run(['git','interpret-trailers','--parse',file],command_env=git_env).stdout
            expected={'A2A-Task':policy['task'],'A2A-Attempt':attempt['attempt_id'],'A2A-Session':attempt['session_id'],
                'A2A-Role':'worker','A2A-Tool':'codex-cli 0.162.1','A2A-Model':'gpt-6.1-sol','A2A-Effort':'xhigh',
                'A2A-Native-Session':identity['native_session'],'A2A-Launch':launches['worker']['id']}
            actual=[line.partition(': ') for line in parsed.splitlines()]
            if {k:v for k,_,v in actual}!=expected or len(actual)!=9: raise RuntimeError('Observed commit trailers do not match this worker.')
        gate=call('events','--task',policy['task'])['events']; scores=[e['details'] for e in gate if e['type']=='score_recorded']
        expected_rejections={'identity_version':0,'path_boundary':0,'completion':1,'red_state':0,'rule_checks':0,'independent_review':0,'commit_trailers':0}
        if len(scores)!=1 or scores[0]['launch_id']!=launches['worker']['id'] or scores[0]['attempt']!=attempt['attempt_id'] or \
           scores[0]['model']!='gpt-6.1-sol' or scores[0]['effort']!='xhigh' or scores[0]['facts']['delivery_rounds']!=2 or \
           scores[0]['facts']['rejections']!=expected_rejections or scores[0]['facts']['human_interventions']!=0:
            raise RuntimeError('Score facts do not match the observed delivery chain.')
        save('score-payload.json',scores[0]); save('gate-events.json',gate); save('integration.json',dict(B=B,G=G,C1=C1,C2=C2,M=M,task=integrated))
        call('reclaim','--task',policy['task'],'--attempt',attempt['attempt_id'])
        result.update(status='PASS',B=B,G=G,C1=C1,C2=C2,M=M)
    except Exception as error:
        result.update(status='INCOMPLETE',error=repr(error),traceback=traceback.format_exc())
    finally:
        try:
            if started and host.poll() is None:
                owner=call('daemon_status')
                if owner['pid']!=host.pid or owner['root']!=str(state): raise RuntimeError('Unconfirmed owner; do not stop.')
                save('events-before-stop.json',events()); call('daemon_stop')
            if host is not None:
                host.wait(timeout=20); deadline=time.monotonic()+10
                while True:
                    p=run(['/bin/ps','-p',','.join(map(str,sorted(pids))),'-o','pid=,ppid=,command='],check=False)
                    if p.returncode not in (0,1): raise RuntimeError('Owned PID observation failed.')
                    if not p.stdout.strip(): break
                    if time.monotonic()>deadline: raise RuntimeError('Owned exit unconfirmed; preserve homes.')
                    time.sleep(0.1)
            if started:
                db=archive_stopped_database(state,out / 'database-after-stop/state.sqlite3'); save('database-after-stop.json',db)
                with contextlib.closing(sqlite3.connect(Path(db['path']).as_uri()+'?mode=ro',uri=True)) as connection:
                    connection.row_factory=sqlite3.Row
                    rows=[{**dict(r),'data':json.loads(r['data'])} for r in connection.execute('SELECT * FROM orchestration_events ORDER BY seq')]
                save('events-after-stop.json',rows); all_native=records(rows)
                result['observed_main_turns']=len(turns(rows,None,'task_started'))
                if any(e['type'] in ('native_final_read_failed','stop_transfer_failed','event_write_failed','queue_stopped') for e in rows):
                    result.update(status='INCOMPLETE',trace_error='Final trace or queue ended with an error; preserve its evidence.')
                if result['status']=='PASS':
                    metas=[r['payload'] for r in all_native if r['type']=='session_meta']
                    previous_native=json.loads((CARD / 'p-review-readback-01.json').read_text())['native_session']
                    if len(metas)!=2 or len({m['id'] for m in metas})!=2 or any(m['source']!='cli' for m in metas) or result['observed_main_turns']!=5 or \
                       turns(rows,None,'task_started')!=turns(rows,None,'task_complete') or any(m['id']==previous_native for m in metas) or \
                       len(turns(rows,launches['worker']['id'],'task_started'))!=4 or \
                       len(turns(rows,launches['reviewer']['id'],'task_started'))!=1:
                        result.update(status='INCOMPLETE',native_error='Final native budget/session mismatch.')
                    for role in ('worker','reviewer'):
                        contexts=[r['payload'] for r in records(rows,launches[role]['id']) if r['type']=='turn_context']
                        if not contexts or any(c['model']!='gpt-6.1-sol' or c['effort']!='xhigh' or c['approval_policy']!='never' or c['sandbox_policy']['type']!=policy[role]['sandbox'] for c in contexts):
                            result.update(status='INCOMPLETE',native_error='Native model/sandbox differs from its approved launch.')
                    wr=records(rows,launches['worker']['id']); active=None
                    for record in wr:
                        p=record['payload']
                        if record['type']=='event_msg' and p.get('type')=='task_started': active=p['turn_id']
                        if active in (tids[1],tids[3]) and record['type']=='response_item' and p.get('type') in ('function_call','custom_tool_call'):
                            result.update(status='INCOMPLETE',native_error='An ACK turn called a tool.')
            for role,home in zip(('worker','reviewer'),homes):
                if own and (home / 'sessions').exists(): shutil.copytree(home / 'sessions',out / (role+'-native-sessions'),symlinks=True)
                if own and home.exists(): shutil.rmtree(home)
            result['home_removed']=own and all(not h.exists() for h in homes)
            if own:
                archive=root / 'archive'; archive.mkdir()
                for p in (repo,state):
                    if p.exists(): shutil.copytree(p,archive / p.name,symlinks=True)
                for role,launch in launches.items(): shutil.copytree(launch['request_dir'],archive / (role+'-request-files'))
                if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk disappeared.')
                result['fixture_archive']=archive_directory(archive,out / 'fixture-artifacts.tar.gz',out.name)
        except Exception as error: result.update(status='BLOCKED',cleanup_error=repr(error))
        for stream in streams: stream.close()
        for path in list(out.rglob('*')):
            if path.is_file() and path.stat().st_size>5*1024*1024 and path.suffix!='.gz':
                compressed=path.with_name(path.name+'.gz')
                with path.open('rb') as src,gzip.open(compressed,'xb') as dest: shutil.copyfileobj(src,dest)
                if gzip.decompress(compressed.read_bytes())!=path.read_bytes(): raise RuntimeError('Compressed evidence differs.')
                path.unlink()
        result['oversize_files']=[str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size>5*1024*1024]
        if result['oversize_files']: result.update(status='INCOMPLETE',archive_required=True)
        if reserved: ledger(dict(kind='observation',slots=[2,3,4,5,6],output=str(out),observed_main_turns=result['observed_main_turns'],status=result['status'],home_removed=result['home_removed']))
        save('run.json',result)
    print(json.dumps({k:result[k] for k in ('status','product_status','real_turns_reserved','observed_main_turns','home_removed')}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
