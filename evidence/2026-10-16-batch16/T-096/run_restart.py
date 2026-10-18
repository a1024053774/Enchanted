#!/usr/bin/env python3
"""CONTROLLER ONLY — first T-096 single-pane red/Tracer bullet.
CLI/process inventory: Node 26.5, standard Vite build on mounted external disk,
production daemon, one zsh PTY and controlled C Codex receiver per daemon epoch;
clang once; one isolated Electron at a time (two sequential starts), Git init/add/
commit in a new fixture. NO real Codex or Claude, login, hooks or model calls.
Keys: ZERO. No prompt release, Enter, Esc, focus, paste or permission answers.
Budget: model rounds 0; receiver starts <=2; Electron starts <=2; ps <=100;
kill only the exact registered PIDs after checking their start time and command.
Kill stage uses SIGKILL (daemon, its verified shell/receiver, and owned Electron
process tree), required crash injection. No user applications are touched.
Output: raw files on the mounted external volume; one short terminal summary.
Cleanup: only the fixture daemon/children and Electron; retain failed originals;
archive stopped fixture with file-count/byte comparison, do not delete originals.
--expect-red succeeds only for the baseline historical/unrestored pane assertion.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'T-091'
sys.path.insert(0, str(OLD))
from run_red import Observer, archive_fixture, write_json
from capture_window import process_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--expect-red', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    volume = Path('/Volumes/WD-Elements')
    output = args.output.resolve()
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
    result = dict(status='INCOMPLETE', argv=sys.argv, approval_ref=args.approval_ref,
        fixture=str(fixture), model_turns=0, keys=[], checks=[], cleanup_complete=False)
    observer = None
    owners = []
    daemon_live = False
    commands = []

    def run(argv, timeout=60, allow_failure=False):
        p = subprocess.run(list(map(str,argv)), cwd=source, env=env, capture_output=True, text=True, timeout=timeout)
        ident = len(commands)+1
        write_json(output/f'command-{ident}.json', dict(argv=list(map(str,argv)), exit=p.returncode, stdout=p.stdout, stderr=p.stderr))
        commands.append(dict(id=ident, exit=p.returncode))
        if p.returncode and not allow_failure: raise RuntimeError(f'command-{ident} failed')
        return p

    def call(command, **values):
        if command == 'pane_layout':
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(15)
                client.connect(str(fixture/'state/control.sock'))
                client.sendall((json.dumps(dict(input=dict(command=command, **values)))+'\n').encode())
                data=b''
                while b'\n' not in data: data += client.recv(65536)
                return json.loads(data.split(b'\n')[0])
        argv = [*cli, command]
        for key,value in values.items(): argv += ['--'+key.replace('_','-'), str(value)]
        p = run(argv)
        value = json.loads(p.stdout)
        if not value.get('ok'): raise RuntimeError(value)
        return value

    def wait(fn, description, timeout=30):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            value=fn()
            if value: return value
            time.sleep(.15)
        raise TimeoutError(description)

    def alive(owner):
        p=run(['/bin/ps','-ww','-p',owner['pid'],'-o','pid=,lstart=,command='], allow_failure=True)
        if p.returncode==1 and not p.stdout.strip(): return False
        now=process_identity(owner['pid'])
        if now != owner: raise RuntimeError('PID identity changed; refusing to signal')
        return True

    def kill(owner):
        if alive(owner): os.kill(owner['pid'],signal.SIGKILL)

    def start_daemon(epoch):
        nonlocal daemon_live
        env['A2A_OPERATOR_CREDENTIAL']=str(fixture/f'operator-{epoch}.json')
        p=call('daemon_start', launch_config=fixture/'launch.json')
        owner=process_identity(p['pid']); owners.append(owner); daemon_live=True
        return owner

    def open_window(epoch, launch=None):
        nonlocal observer
        folder=output/f'window-{epoch}'; folder.mkdir()
        env['A2A_ELECTRON_DIAGNOSTICS']=str(folder/'stages.jsonl')
        rel=(source/'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        electron=(source/'workbench/node_modules/electron/dist'/rel).resolve(strict=True)
        argv=[str(electron),str(source/'workbench/tests/electron_driver.mjs'),'--build',build['out'],
            '--state',str(fixture/'state'),'--task','t096-fixture','--user-data',str(fixture/'ui'),'--output',str(folder)]
        if launch: argv += ['--launch',launch]
        observer=Observer(argv,env,folder,max_calls=6,max_stdout_bytes=4*1024*1024)
        observer.identify(argv,folder)
        ready=observer.receive(timeout=50)
        if ready.get('ready') is not True: raise RuntimeError(dict(electron_not_ready=ready))
        observer.ready_confirmed=True
        return observer.call('inspect-all')

    try:
        result['revision']=run(['git','rev-parse','HEAD']).stdout.strip()
        result['node']=run([node,'--version']).stdout.strip()
        repo=fixture/'repo'
        run(['git','-C',repo,'init','-b','main'])
        (repo/'value.txt').write_text('fixture\n',encoding='utf-8')
        (repo/'criterion.py').write_text('assert True\n',encoding='utf-8')
        run(['git','-C',repo,'add','value.txt','criterion.py'])
        run(['git','-C',repo,'commit','-m','T096 fixture'])
        receiver=fixture/'bin/receiver'
        # Runner/fixture stay in the candidate even when --source points to main.
        run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',HERE.parents[2]/'workbench/tests/t096_resume_receiver.c','-o',receiver])
        role=fixture/'role.md'; role.write_text('只收字节，不调用模型。\n',encoding='utf-8')
        write_json(fixture/'launch.json',dict(codex_bin=str(receiver),codex_home=str(fixture/'codex-home'),role_card=str(role),
            role_card_revision='T096',code_revision=result['revision'],source_snapshot=str(source),
            hook_authorization=args.approval_ref,turn_limit=1,turn_authorization=args.approval_ref))
        card=dict(id='t096-fixture',source=None,goal='重启恢复',non_goals=['不调用模型'],
            paths=dict(allow=['value.txt'],deny=[]),oracle_paths=['criterion.py'],
            completion_conditions=[dict(argv=[sys.executable,'-I','-B','criterion.py'])],red_commands=[],
            task_type='后端逻辑',repair_target=None,complexity='L',executor=dict(cli='Codex',model='gpt-6.1-sol',effort='xhigh'),
            base_commit=None,writer=None)
        write_json(fixture/'card.json',card)
        daemon=start_daemon(1)
        call('card_save',task='t096-fixture',card=fixture/'card.json',expected_version=0)
        call('create',task='t096-fixture',repo=repo,branch='refs/heads/main',card_version=1,project='t096')
        attempt=call('dispatch',task='t096-fixture',runtime_mode='workspace-write')['attempt']
        before=wait(lambda: (v if (v:=call('pane_process_info',thread=attempt['thread_id'])).get('native_session') and v.get('leader') else None),'receiver identity')
        launch=call('workbench_snapshot',task='t096-fixture')['launch']['id']
        original=call('launch_show',launch=launch)['launch']
        build=json.loads(run([node,source/'workbench/app/build.mjs','--slot','t096-'+fixture.name.rsplit('-',1)[-1]],timeout=180).stdout)
        first=open_window(1,launch)
        write_json(output/'before.json',dict(process=before,launch=original,view=first))
        children=[process_identity(before[key]) for key in ['leader','shell_pid']]
        # Deliberate full crash. Electron children are discovered from the owned
        # main process only; never enumerate or signal unrelated application roots.
        ps=run(['/bin/ps','-axo','pid=,ppid=']).stdout
        descendants={observer.owner['pid']}
        rows=[list(map(int,row.split())) for row in ps.splitlines() if row.strip()]
        while True:
            added={pid for pid,parent in rows if parent in descendants}-descendants
            if not added: break
            descendants.update(added)
        electron_owners=[process_identity(pid) for pid in descendants]
        for owner in electron_owners: kill(owner)
        observer.process.wait(timeout=10)
        remaining=observer.process.stdout.read()
        observer.stdout.write(remaining); observer.stdout.flush()
        observer.selector.close(); observer.log.close(); observer.stderr.close(); observer.stdout.close()
        observer.process.stdin.close(); observer.process.stdout.close(); observer=None
        for owner in [daemon,*children]: kill(owner)
        daemon_live=False
        wait(lambda: all(not alive(o) for o in [daemon,*children]),'crashed writers absent')
        # The baseline has no stale-endpoint recovery; preserve endpoint diagnosis
        # and remove ONLY its dead fixture endpoint so its restart can be observed.
        if args.expect_red:
            for name in ['control.sock','daemon.pid']:
                p=fixture/'state'/name
                if p.exists(): p.unlink()
        daemon=start_daemon(2)
        if not args.expect_red:
            wait(lambda: not call('pane_layout',task='t096-fixture').get('recovering'),'restore completion')
        second=open_window(2)
        after=call('workbench_snapshot',task='t096-fixture',launch=launch)
        write_json(output/'after.json',dict(snapshot=after,view=second))
        if args.expect_red:
            if after['pane'].get('historical') is not True or after['pane']['lifecycle']=='running': raise AssertionError('baseline did not exhibit expected historical pane')
            result['checks'].append('expected_red_restart_leaves_no_live_pane')
        else:
            if after['pane'].get('restoration',{}).get('status')!='restored': raise AssertionError('pane was not restored')
            process=call('pane_process_info',thread=attempt['thread_id'])
            if process.get('native_session')!=before['native_session'] or process.get('failed') or not process.get('leader'): raise AssertionError('restored identity mismatch')
            receipt=json.loads((fixture/'codex-home'/f"receiver-{process['leader']}.json").read_text(encoding='utf-8'))
            if receipt['argv'] != [*original['argv'],'resume',before['native_session']]: raise AssertionError('argv field mismatch')
            write_json(output/'after-process.json',process)
            result['checks'].extend(['same_native_identity','same_task_role_launch','argv_every_field_equal','zero_model_turns'])
        result['status']='PASS'
    except Exception as error:
        result['error']=str(error); result['traceback']=traceback.format_exc()
    finally:
        try:
            if observer: observer.close(); observer=None
            if daemon_live:
                call('daemon_stop')
                wait(lambda: not (fixture/'state/daemon.pid').exists(),'daemon cleanup')
                daemon_live=False
            result['cleanup_complete']=True
            stats=archive_fixture(fixture,output/'fixture')
            write_json(HERE/(args.label+'.archive.json'),dict(original=str(fixture),archive=str(output/'fixture'),bytes=stats['bytes'],files=stats['files'],comparison=stats['comparison'],replay=' '.join(sys.argv)))
        except Exception as error:
            result['cleanup_error']=str(error); result['status']='INCOMPLETE'
        result['commands']=commands
        write_json(summary,result)
        print(json.dumps(dict(status=result['status'],summary=str(summary),error=result.get('error'),cleanup=result['cleanup_complete'])))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
