#!/usr/bin/env python3
"""CONTROLLER ONLY — real daemon + Electron + Claude restart readback (decision B).

Inventory BEFORE running:
  --panes 1: one configured Claude 2.1.302 controller before and after crash.
  --panes 3: two configured Claude controllers before/after crash; ONE controlled
  C Codex receiver before crash only. Never real Codex, login or model rounds.
  Production per-session UserPromptSubmit/Stop/PermissionRequest hooks (3s)
  are passed by argv; no synthetic hook invocation.
  Each Claude start probes --version. <=4 interactive Claude starts, <=4 probes,
  one clang, two daemon epochs, two sequential Electron instances, isolated Git.
  Fake API binds loopback once; every POST is recorded/rejected. POST budget 0.
  Keys/paste/focus/release: ZERO. Only daemon terminal-protocol replies. Theme,
  trust, login and permission screens are observed; never automatically answered.
  After crash, a documented synthetic historical user/assistant pair is seeded
  into the exact recorded native session. It is NOT a model-produced transcript.
  Resume must display its unique history nonce; merely seeing a PID cannot pass.
  If onboarding blocks that readback: INCOMPLETE, preserve screens, no extra keys.
  Fault injection (--fault): only stopped fixture launch_records/native files;
  never tasks/attempts/gates. Missing argv/version/session each has its own run;
  --panes 3 --fault missing-argv also proves a failed sibling does not block others.
  SIGKILL only verified owned daemon, shell/CLI and Electron descendants. Every
  signal checks PID/start-time/command. <=200 journaled runner process reads;
  normal quit additionally uses its bounded 15-second owner/exit readback. Native argv read via macOS sysctl (argv only, never environment).
  <=64 observer RPCs per Electron. With --check-close: ONE close-pane button
  click after readbacks; no terminal keys or prompt submission. No screenshot.
  Standard build/new slot and all raw output on mounted external disk; bounded
  command/observer output, one short terminal summary. No auth.json/global writes.
  Every identified writer is journaled before the crash; cleanup sends an
  authenticated daemon_stop directly to the existing socket (no CLI subprocess).
  Cleanup: owned Electron normal quit only after ready, daemon_stop and PID
  absence. If ownership/startup/cleanup is unknown: stop, retain the live fixture,
  no archive. Ephemeral operator credentials are removed after all writers exit
  and before any archive; credential contents never enter evidence. Stopped fixtures copied with file-count/byte comparison, retained.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import shlex
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / 'T-091'))
from run_red import Observer, archive_fixture, write_json
from owned_electron import normal_quit
from restart_cleanup import native_argv, operator_request, close_observer, finish_cleanup, probe_process



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['source', 'output', 'claude']:
        parser.add_argument('--'+key, type=Path, required=True)
    for key in ['label', 'approval-ref', 'claude-version']:
        parser.add_argument('--'+key, required=True)
    parser.add_argument('--panes', type=int, choices=[1, 3], default=1)
    parser.add_argument('--fault', choices=['none', 'missing-argv', 'version-mismatch', 'missing-session'], default='none')
    parser.add_argument('--expect-red', action='store_true')
    parser.add_argument('--check-close', action='store_true')
    args = parser.parse_args()
    if args.expect_red and args.fault != 'none': raise RuntimeError('red_requires_unmodified_fixture')
    if not re.fullmatch('[a-z0-9_-]+', args.label): raise RuntimeError('invalid_label')
    if args.claude_version != '2.1.302': raise RuntimeError('this_fixture_requires_configured_2.1.302')
    source, volume, output = args.source.resolve(strict=True), Path('/Volumes/WD-Elements'), args.output.resolve()
    if not os.path.ismount(volume) or not output.is_relative_to(volume / 'a2a-evidence/2026-10-16-batch16/T-096'):
        raise RuntimeError('mounted_external_output_required')
    summary = HERE / (args.label + '.run.json')
    if summary.exists(): raise RuntimeError('new_label_required')
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t078-2-t096-', dir='/private/tmp')).resolve()
    for name in ['repo', 'state', 'home', 'codex-home', 'tmp', 'ui', 'bin']:
        (fixture / name).mkdir()
    env = {k: os.environ[k] for k in ['PATH', 'USER', 'LOGNAME'] if k in os.environ}
    env.update(HOME=str(fixture/'home'), TMPDIR=str(fixture/'tmp'), LANG='en_US.UTF-8', LC_ALL='C',
        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='2',
        GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
        GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
        GIT_AUTHOR_NAME='T096 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
        GIT_COMMITTER_NAME='T096 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    node = shutil.which('node', path=env.get('PATH'))
    cli = [node, str(source/'workbench/src/gates/cli.ts'), '--state', str(fixture/'state')]
    result = dict(status='INCOMPLETE', argv=sys.argv, approval_ref=args.approval_ref, fixture=str(fixture),
        model_turns=0, fake_posts=0, keys=[], checks=[], cleanup_complete=False, process_reads=0,
        history_source='synthetic fixture pair seeded after crash; no vendor/model-generated history')
    observer = None
    observer_expected_crash = False
    observer_start_unconfirmed = False
    daemon_start_unconfirmed = False
    expected_layout = None
    daemon_live = False
    owned = []
    commands, requests, controllers = [], [], []
    histories = {}
    api = None
    build = None

    def run(argv, timeout=60, allow_failure=False):
        ident = len(commands)+1
        stdout, stderr = output/f'command-{ident}.stdout.txt', output/f'command-{ident}.stderr.txt'
        with stdout.open('xb') as out, stderr.open('xb') as err:
            p = subprocess.run(list(map(str,argv)), cwd=source, env=env, stdout=out, stderr=err, timeout=timeout)
        meta = dict(id=ident, argv=list(map(str,argv)), exit=p.returncode)
        commands.append(meta); write_json(output/f'command-{ident}.json', meta)
        if max(stdout.stat().st_size, stderr.stat().st_size)>2*1024*1024: raise RuntimeError('command_output_budget_exceeded; raw output preserved')
        p.stdout=stdout.read_text(encoding='utf-8'); p.stderr=stderr.read_text(encoding='utf-8')
        if p.returncode and not allow_failure: raise RuntimeError(f'command-{ident} failed')
        return p

    def call(command, **values):
        if command == 'pane_layout':
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(15); client.connect(str(fixture/'state/control.sock'))
                client.sendall((json.dumps(dict(input=dict(command=command, **values)))+'\n').encode())
                data=b''
                while b'\n' not in data:
                    chunk=client.recv(65536)
                    if not chunk: raise RuntimeError('daemon disconnected')
                    data += chunk
                    if len(data)>1024*1024: raise RuntimeError('layout_output_budget_exceeded')
                value=json.loads(data.split(b'\n')[0])
        else:
            argv = [*cli, command]
            for key,value in values.items(): argv += ['--'+key.replace('_','-'), str(value)]
            value=json.loads(run(argv).stdout)
        if not value.get('ok'): raise RuntimeError(value)
        return value

    def check(name, condition):
        result['checks'].append(dict(name=name,status='PASS' if condition else 'INCOMPLETE'))
        if not condition: raise AssertionError(name)

    def wait(fn, description, timeout=30):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            value=fn()
            if value: return value
            time.sleep(.2)
        raise TimeoutError(description)

    def identify(pid):
        result['process_reads'] += 1
        if result['process_reads']>200: raise RuntimeError('process_read_budget_exhausted')
        current=probe_process(pid,run=run)
        if current is None: result.setdefault('exited_process_probes',[]).append(pid)
        return current

    def register(owner, kind):
        if owner is None: raise RuntimeError(kind+' exited before identity registration')
        identity={key:owner[key] for key in ['pid','started','command']}
        if identity not in owned: owned.append(identity)
        result['owned']=list(owned)
        with (output/'ownership.jsonl').open('a',encoding='utf-8') as journal:
            journal.write(json.dumps(dict(time=time.time(),kind=kind,fixture=str(fixture),owner=identity))+'\n')
            journal.flush(); os.fsync(journal.fileno())
        return identity

    def alive(owner):
        current=identify(owner['pid'])
        if current is None: return False
        if current!=owner: raise RuntimeError('PID identity changed; refusing to signal')
        return True

    def kill(owner):
        sent=False
        if alive(owner):
            try:
                os.kill(owner['pid'],signal.SIGKILL); sent=True
            except ProcessLookupError:
                pass  # The verified process exited between the read and signal.
        result.setdefault('signal_receipts',[]).append(dict(pid=owner['pid'],signal_sent=sent,already_exited=not sent))

    def start_daemon(epoch):
        nonlocal daemon_live, daemon_start_unconfirmed
        env['A2A_OPERATOR_CREDENTIAL']=str(fixture/f'operator-{epoch}.json')
        daemon_start_unconfirmed=True
        p=call('daemon_start',launch_config=fixture/'launch.json')
        result['daemon_start_receipt']=dict(epoch=epoch,pid=p['pid'],state=str(fixture/'state'))
        write_json(output/f'daemon-start-{epoch}.json',result['daemon_start_receipt'])
        daemon_live=True
        owner=register(identify(p['pid']),'daemon')
        daemon_start_unconfirmed=False
        return owner

    def inspect_window():
        view=observer.call('inspect-all')
        return view if len(view['panes'])==args.panes and all(p.get('snapshot') for p in view['panes']) else None

    def open_window(epoch, launches=None):
        nonlocal observer, observer_expected_crash, observer_start_unconfirmed
        observer_expected_crash=False
        folder=output/f'window-{epoch}'; folder.mkdir()
        env['A2A_ELECTRON_DIAGNOSTICS']=str(folder/'stages.jsonl')
        rel=(source/'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        electron=(source/'workbench/node_modules/electron/dist'/rel).resolve(strict=True)
        argv=[str(electron),str(source/'workbench/tests/electron_driver.mjs'),'--build',build['out'],
            '--state',str(fixture/'state'),'--task','t096-fixture','--user-data',str(fixture/'ui'),'--output',str(folder)]
        for launch in launches or []: argv += ['--launch',launch]
        result['electron_start_intent']=dict(argv=argv,state=str(fixture/'state'),output=str(folder))
        write_json(folder/'start-intent.json',result['electron_start_intent'])
        observer_start_unconfirmed=True
        observer=Observer(argv,env,folder,max_calls=64,max_stdout_bytes=8*1024*1024)
        result['electron_start_receipt']=dict(pid=observer.process.pid,epoch=epoch,output=str(folder))
        write_json(folder/'start-receipt.json',result['electron_start_receipt'])
        current=identify(observer.process.pid)
        if current is None: raise RuntimeError('Electron exited before startup identity registration; start receipt retained')
        observer.owner={**current,'driver':argv[1],'executable':argv[0]}
        write_json(folder/'electron-owner.json',observer.owner)
        register(observer.owner,'electron')
        observer_start_unconfirmed=False
        ready=observer.receive(timeout=50)
        if ready.get('ready') is not True: raise RuntimeError(dict(electron_not_ready=ready))
        observer.ready_confirmed=True
        return wait(inspect_window,'complete renderer snapshots',timeout=4)

    def crash_window():
        nonlocal observer, observer_expected_crash, observer_start_unconfirmed
        rows=[list(map(int,row.split())) for row in run(['/bin/ps','-axo','pid=,ppid=']).stdout.splitlines() if row.strip()]
        descendants={observer.owner['pid']}
        while True:
            added={pid for pid,parent in rows if parent in descendants}-descendants
            if not added: break
            descendants.update(added)
        electron_owners=[]
        for pid in descendants:
            owner=identify(pid)
            if owner is not None: electron_owners.append(register(owner,'electron-descendant'))
            else: result.setdefault('exited_before_crash_registration',[]).append(pid)
        observer_expected_crash=True
        # Kill descendants first, then the verified main process.
        for owner in sorted(electron_owners,key=lambda o:o['pid']==observer.owner['pid']): kill(owner)
        observer.process.wait(timeout=10)
        closed=close_observer(observer,expected_crash=True,read_process=identify,normal_quit=normal_quit)
        observer=None; observer_start_unconfirmed=False
        result['crash_observer']=closed
        if closed['diagnostics']: raise RuntimeError('crash observer stream cleanup incomplete: '+str(closed['diagnostics']))
        wait(lambda: all(not alive(owner) for owner in electron_owners),'owned Electron tree absent',timeout=5)

    def seed_history(record):
        config=Path(record['env']['CLAUDE_CONFIG_DIR'])
        directory=config/'projects'/re.sub('[^a-zA-Z0-9]','-',record['worktree'])
        directory.mkdir(parents=True,exist_ok=True)
        target=directory/(record['session']+'.jsonl')
        if target.exists():
            target.rename(target.with_suffix('.original-jsonl'))
        nonce='T096_HISTORY_'+uuid.uuid4().hex
        parent=str(uuid.uuid4()); stamp=datetime.now(timezone.utc).isoformat()
        common=dict(isSidechain=False,userType='external',cwd=record['worktree'],sessionId=record['session'],version=args.claude_version,gitBranch='main',timestamp=stamp)
        lines=[dict(common,parentUuid=None,type='user',message=dict(role='user',content='Fixture history only, do not execute.'),uuid=parent),
            dict(common,parentUuid=parent,type='assistant',uuid=str(uuid.uuid4()),requestId='fixture-request',
            message=dict(id='fixture-message',type='message',role='assistant',model='claude-haiku-5-5',
                content=[dict(type='text',text=nonce)],stop_reason='end_turn',stop_sequence=None,
                usage=dict(input_tokens=1,output_tokens=1)))]
        target.write_text(''.join(json.dumps(line)+'\n' for line in lines),encoding='utf-8')
        return dict(file=str(target),nonce=nonce,kind='synthetic historical pair',model_calls=0)

    try:
        result['revision']=run(['git','rev-parse','HEAD']).stdout.strip()
        result['node']=run([node,'--version']).stdout.strip()
        check('node_26_5',result['node'].startswith('v26.') and int(result['node'].split('.')[1])>=5)
        check('frozen_source',not run(['git','diff','HEAD','--','workbench/src','workbench/app','workbench/tests']).stdout)
        class FakeAPI(BaseHTTPRequestHandler):
            def log_message(self,*unused): pass
            def respond(self):
                requests.append(dict(method=self.command,path=self.path,time=time.time()))
                self.send_error(403,'T096 model budget zero')
            do_GET=respond
            do_POST=respond
        api=ThreadingHTTPServer(('127.0.0.1',0),FakeAPI); api.daemon_threads=True
        threading.Thread(target=api.serve_forever,daemon=True).start()
        api_url=f'http://127.0.0.1:{api.server_port}/'
        repo=fixture/'repo'
        run(['git','-C',repo,'init','-b','main'])
        (repo/'value.txt').write_text('fixture\n',encoding='utf-8')
        (repo/'criterion.py').write_text('assert True\n',encoding='utf-8')
        run(['git','-C',repo,'add','value.txt','criterion.py']); run(['git','-C',repo,'commit','-m','T096 fixture'])
        launch_config=dict(code_revision=result['revision'],source_snapshot=str(source))
        if args.panes==3:
            receiver=fixture/'bin/receiver'
            run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',HERE.parents[2]/'workbench/tests/t096_resume_receiver.c','-o',receiver])
            role=fixture/'role.md'; role.write_text('只收字节，不调用模型。\n',encoding='utf-8')
            launch_config.update(codex_bin=str(receiver),codex_home=str(fixture/'codex-home'),role_card=str(role),
                role_card_revision='T096',hook_authorization=args.approval_ref,turn_limit=1,turn_authorization=args.approval_ref)
        write_json(fixture/'launch.json',launch_config)
        card=dict(id='t096-fixture',source=None,goal='重启恢复',non_goals=['不调用模型'],paths=dict(allow=['value.txt'],deny=[]),
            oracle_paths=['criterion.py'],completion_conditions=[dict(argv=[sys.executable,'-I','-B','criterion.py'])],red_commands=[],
            task_type='后端逻辑',repair_target=None,complexity='L',executor=dict(cli='Codex',model='gpt-6.1-sol',effort='xhigh'),base_commit=None,writer=None)
        write_json(fixture/'card.json',card)
        daemon=start_daemon(1)
        call('card_save',task='t096-fixture',card=fixture/'card.json',expected_version=0)
        call('create',task='t096-fixture',repo=repo,branch='refs/heads/main',card_version=1,project='t096')
        for preset in (['ideation','executor'] if args.panes==3 else ['ideation']):
            folder=fixture/'roles'/preset
            for name in ['home','claude','tmp','shell','requests','hooks','user-data']: (folder/name).mkdir(parents=True)
            (folder/'claude/settings.json').write_text('{"theme":"dark"}\n',encoding='utf-8')
            (folder/'role.md').write_text('停在隔离首屏，不输入、不调用模型或工具。\n',encoding='utf-8')
            manifest=dict(schema=1,root=str(fixture),state=str(fixture/'state'),task='t096-fixture',preset=preset,
                launch=str(uuid.uuid4()),session=str(uuid.uuid4()),thread=str(uuid.uuid4()),executable=str(args.claude.absolute()),version=args.claude_version,
                role_file=str(folder/'role.md'),code_revision=result['revision'],source_snapshot=str(source),api_url=api_url,turn_limit=1)
            write_json(folder/'manifest.json',manifest)
            record=call('controller_start',task='t096-fixture',manifest=folder/'manifest.json')['launch']
            info=wait(lambda:(v if (v:=call('pane_process_info',thread=record['thread'])).get('leader') else None),'Claude foreground identity')
            [register(identify(info[k]),k) for k in ['shell_pid','leader']]; controllers.append(record)
            actual_argv=native_argv(info['leader'])
            check(preset+'_initial_native_argv',actual_argv==record['argv'])
            write_json(output/(preset+'.initial-argv.json'),actual_argv)
            write_json(output/(preset+'.before.json'),dict(record=record,process=info))
        worker=None
        if args.panes==3:
            attempt=call('dispatch',task='t096-fixture',runtime_mode='workspace-write')['attempt']
            info=wait(lambda:(v if (v:=call('pane_process_info',thread=attempt['thread_id'])).get('leader') and v.get('native_session') else None),'receiver identity')
            [register(identify(info[k]),k) for k in ['shell_pid','leader']]
            worker=call('workbench_snapshot',task='t096-fixture')['launch']
        task_before=call('status',task='t096-fixture')['task']
        write_json(output/'gate-before.json',task_before)
        build=json.loads(run([node,source/'workbench/app/build.mjs','--slot','t096-'+fixture.name.rsplit('-',1)[-1]],timeout=180).stdout)
        launches=[record['id'] for record in controllers]+([worker['id']] if worker else [])
        first=open_window(1,launches); write_json(output/'before-view.json',first)
        crash_window()
        for owner in owned: kill(owner)
        daemon_live=False
        wait(lambda:all(not alive(o) for o in owned),'crashed backend/CLI processes absent',timeout=5)
        if not args.expect_red:
            import sqlite3
            for record in controllers:
                if args.fault=='missing-session' and record==controllers[0]: continue
                histories[record['id']]=seed_history(record)
            # Missing-session must preserve, rather than delete, any CLI-created file.
            if args.fault=='missing-session':
                config=Path(controllers[0]['env']['CLAUDE_CONFIG_DIR'])/'projects'
                for path in config.rglob(controllers[0]['session']+'.jsonl'):
                    path.rename(path.with_suffix('.missing-session-original'))
            if args.fault in ['missing-argv','version-mismatch']:
                with sqlite3.connect(fixture/'state/state.sqlite3') as database:
                    row=database.execute('SELECT data FROM launch_records WHERE id=?',(controllers[0]['id'],)).fetchone()
                    record=json.loads(row[0]); write_json(output/'fault-original-launch.json',record)
                    if args.fault=='missing-argv': record.pop('argv')
                    else: record['cli_version']='0.0.0 (Claude Code)'
                    database.execute('DROP TRIGGER launch_records_no_update')
                    database.execute('UPDATE launch_records SET data=? WHERE id=?',(json.dumps(record),record['id']))
                    database.execute("CREATE TRIGGER launch_records_no_update BEFORE UPDATE ON launch_records BEGIN SELECT RAISE(ABORT,'append only'); END")
            write_json(output/'synthetic-history.json',[dict(launch=launch,**history) for launch,history in histories.items()])
        else:
            # Baseline cannot reopen its dead socket. Preserve then remove ONLY
            # these verified-dead fixture endpoint files to observe its UI state.
            write_json(output/'baseline-endpoint.json',dict(pid=(fixture/'state/daemon.pid').read_text(encoding='utf-8'),socket=str(fixture/'state/control.sock')))
            for name in ['control.sock','daemon.pid']:
                path=fixture/'state'/name
                if path.exists(): path.unlink()
        daemon=start_daemon(2)
        if not args.expect_red: wait(lambda:not call('pane_layout',task='t096-fixture')['recovering'],'recovery completion')
        second=open_window(2); write_json(output/'after-view.json',second)
        gate_after=call('status',task='t096-fixture')['task']; write_json(output/'gate-after.json',gate_after)
        check('worker_attempt_unchanged',gate_after['current_attempt']==task_before['current_attempt'])
        for index,record in enumerate(controllers):
            after=call('workbench_snapshot',task='t096-fixture',launch=record['id'])
            write_json(output/(record['preset']+'.after.json'),after)
            if args.expect_red:
                check('expected_red_historical_no_resume',after['pane'].get('historical') is True and after['pane']['lifecycle']!='running')
                continue
            restoration=after['pane']['restoration']
            expected_error={'missing-argv':'restore_argv_missing','version-mismatch':'restore_version_mismatch','missing-session':'restore_session_missing'}.get(args.fault)
            if index==0 and expected_error:
                check('fault_refused_without_success',restoration['status']=='failed' and restoration['error']==expected_error and after['pane'].get('historical') is True)
                view=next(p for p in second['panes'] if p['launch']==record['id'])
                check('fault_visible_readonly','未恢复' in view['text'] and not view['input_enabled'])
                events=call('orchestration_events')['events']
                check('failed_pane_never_recorded_restored',not any(e['type']=='pane_restored' and e['launch']==record['id'] for e in events))
                continue
            check(record['preset']+'_restored',restoration['status']=='restored')
            info=call('pane_process_info',thread=record['thread'])
            check(record['preset']+'_identity',info.get('leader') and not info.get('failed') and info['native_session']==record['session'])
            [register(identify(info[k]),k) for k in ['shell_pid','leader']]
            events=call('orchestration_events')['events']
            restored=[e for e in events if e['type']=='pane_restored' and e['launch']==record['id']]
            expected_argv=[record['argv'][0],'--resume',*record['argv'][2:]]
            check(record['preset']+'_argv_every_field',restored[-1]['data']['argv']==expected_argv)
            observed_argv=native_argv(info['leader'])
            write_json(output/(record['preset']+'.resumed-argv.json'),observed_argv)
            check(record['preset']+'_native_argv_every_field',observed_argv==expected_argv)
            check(record['preset']+'_launch_unchanged',call('launch_show',launch=record['id'])['launch']==record)
            view=next(p for p in second['panes'] if p['launch']==record['id'])
            check(record['preset']+'_binding',view['role']=='controller' and view['preset']==record['preset'] and view['task']==record['task'])
            # Actual CLI must show independently supplied history. An onboarding
            # screen, missing transcript or process-only success is INCOMPLETE.
            for unused in range(8):
                if histories[record['id']]['nonce'] in view['terminal']: break
                time.sleep(.5)
                refreshed=observer.call('inspect-all')
                view=next(p for p in refreshed['panes'] if p['launch']==record['id'])
            write_json(output/(record['preset']+'.resumed-view.json'),view)
            check(record['preset']+'_native_history_visible',histories[record['id']]['nonce'] in view['terminal'])
        if worker and not args.expect_red:
            after=call('workbench_snapshot',task='t096-fixture',launch=worker['id'])
            view=next(p for p in second['panes'] if p['launch']==worker['id'])
            check('worker_unrestored_visible',after['pane']['restoration']['error']=='restore_managed_attempt_requires_reclaim' and '未恢复' in view['text'] and not view['input_enabled'])
            events=call('orchestration_events')['events']
            check('worker_never_restored',not any(e['type']=='pane_restored' and e['launch']==worker['id'] for e in events))
            check('worker_receiver_not_restarted',len(list((fixture/'codex-home').glob('receiver-*.json')))==1)
        if args.check_close and not args.expect_red:
            target=second['panes'][-1]
            observer.call('close-pane',pane_key=target['pane_key'])
            wait(lambda:len(observer.call('inspect-all')['panes'])==args.panes-1,'explicit pane close reflected in renderer',timeout=4)
            layout=call('pane_layout',task='t096-fixture')['panes']
            check('explicit_close_persisted',all(p['launch']!=target['launch'] for p in layout) and len(layout)==args.panes-1)
            check('close_does_not_mutate_attempt',call('status',task='t096-fixture')['task']['current_attempt']==task_before['current_attempt'])
        check('zero_fake_posts',not any(r['method']=='POST' for r in requests))
        if not args.expect_red: expected_layout=call('pane_layout',task='t096-fixture')['panes']
        result['status']='PASS'
    except BaseException as error:
        result['error']=str(error); result['traceback']=traceback.format_exc()
    finally:
        def close_electron():
            nonlocal observer, observer_start_unconfirmed
            if observer is None:
                if observer_start_unconfirmed: raise RuntimeError('Electron constructor/start outcome unconfirmed; see start-intent and receipt')
                return dict(exited=True,diagnostics=[])
            closed=close_observer(observer,expected_crash=observer_expected_crash,read_process=identify,normal_quit=normal_quit)
            observer=None; observer_start_unconfirmed=False
            if expected_layout is not None:
                try: check('application_exit_preserves_panes',call('pane_layout',task='t096-fixture')['panes']==expected_layout)
                except BaseException as error: closed['diagnostics'].append('layout readback: '+str(error))
            return closed

        def stop_backend():
            nonlocal daemon_live
            if daemon_start_unconfirmed: raise RuntimeError('daemon_start outcome unconfirmed; preserve state and receipt')
            if daemon_live:
                credential=Path(env['A2A_OPERATOR_CREDENTIAL'])
                reply=operator_request(fixture/'state','daemon_status',credential)
                daemon_owner=next((owner for owner in reversed(owned) if owner['pid']==reply['pid']),None)
                if daemon_owner is None or not alive(daemon_owner): raise RuntimeError('daemon identity not confirmed; preserve fixture')
                receipt=operator_request(fixture/'state','daemon_stop',credential)
                wait(lambda:not (fixture/'state/daemon.pid').exists(),'daemon cleanup')
                daemon_live=False
                return dict(command='daemon_stop',pid=daemon_owner['pid'],stopping=receipt.get('stopping',False))
            return dict(command='none',reason='no live epoch owned by this runner')

        def confirm_writers():
            if daemon_start_unconfirmed: raise RuntimeError('unconfirmed daemon start cannot be treated as absent')
            wait(lambda:all(not alive(o) for o in owned),'all registered writers absent',timeout=5)
            if (fixture/'state/daemon.pid').exists() or (fixture/'state/control.sock').exists():
                raise RuntimeError('daemon endpoint remains; fixture retained')

        def archive_stopped():
            for epoch in [1,2]:
                credential=fixture/f'operator-{epoch}.json'
                if credential.is_symlink(): raise RuntimeError('unexpected credential link; preserve fixture')
                if credential.exists(): credential.unlink()
            stats=archive_fixture(fixture,output/'fixture')
            write_json(HERE/(args.label+'.archive.json'),dict(original=str(fixture),archive=str(output/'fixture'),bytes=stats['bytes'],files=stats['files'],comparison=stats['comparison'],replay=shlex.join(sys.argv)))

        cleanup=finish_cleanup(close_electron=close_electron,stop_daemon=stop_backend,confirm_writers=confirm_writers,archive=archive_stopped)
        result['cleanup']=cleanup; result['cleanup_complete']=cleanup['cleanup_complete']
        if not cleanup['cleanup_complete'] or cleanup['diagnostics']:
            result['status']='INCOMPLETE'
            result['cleanup_error']=cleanup['handoff'] or '; '.join(cleanup['diagnostics'])
        if not cleanup['cleanup_complete']:
            result['handoff']=dict(reason=cleanup['handoff'],fixture=str(fixture),source=str(source),state=str(fixture/'state'),
                operator_credential=env.get('A2A_OPERATOR_CREDENTIAL'),writers=owned,
                electron=observer.owner if observer else None,daemon_start=result.get('daemon_start_receipt'),electron_start=result.get('electron_start_receipt'),policy='No force quit or second crash attempt; controller must verify this fixture')
        if api:
            for operation in [api.shutdown,api.server_close]:
                try: operation()
                except BaseException as error:
                    result.setdefault('api_cleanup_errors',[]).append(str(error)); result['status']='INCOMPLETE'
        result['fake_posts']=sum(r['method']=='POST' for r in requests)
        if result['fake_posts']: result['status']='INCOMPLETE'
        result['commands']=commands
        for path,payload in [(output/'fake-api-requests.json',requests),(summary,result)]:
            try: write_json(path,payload)
            except BaseException as error:
                result.setdefault('evidence_write_errors',[]).append(dict(path=str(path),error=str(error)))
                result['status']='INCOMPLETE'
        handoff=None
        if result.get('handoff') or result.get('evidence_write_errors'):
            handoff=dict(fixture=str(fixture),ownership=str(output/'ownership.jsonl'),registered_pids=[o['pid'] for o in owned],
                reason=cleanup['handoff'] or 'Evidence write incomplete; original paths retained',unverified_electron=result.get('electron_start_receipt'))
        print(json.dumps(dict(status=result['status'],summary=str(summary),error=result.get('error'),cleanup=result['cleanup_complete'],handoff=handoff)))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
