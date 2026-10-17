#!/usr/bin/env python3
"""T-078 input tracer bullet and credential contract, through real entry points.

Independent inputs come from T-078 A2/A4 and the approved PLAN, not production
output. A deterministic byte receiver replaces only the vendor process. The
Electron window, daemon, gate, SQLite and node-pty are the production versions.
No Claude fixture, real vendor CLI, model, auth file or global config is used.

Failures: UI input never reaches PTY; missing/misbound user input/intervention;
empty callbacks lose observation metadata or create input; an anonymous request
selects ideation by --from and appends an inbox record.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import time
import traceback

from command_evidence import CommandLog, command_json
from electron_client import ElectronClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-probe', action='store_true', help='Use a native byte receiver and extend the pane/runtime contracts')
    parser.add_argument('--input-failures', action='store_true', help='Extend the native receiver run with input failure contracts')
    parser.add_argument('--worker-inbox', action='store_true', help='Run the real inbox client as the launched worker and transfer at Stop')
    parser.add_argument('--backend-source', type=Path, help='Frozen backend mutant source root; test harness only')
    parser.add_argument('--reuse-build', type=Path, help='Reuse a build of this unchanged frontend during backend counterexamples')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    backend = args.backend_source.resolve(strict=True) if args.backend_source else source
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    fixture = Path(tempfile.mkdtemp(prefix='t78-', dir='/tmp')).resolve()
    repo, state, home = fixture / 'repo', fixture / 'state', fixture / 'receiver-home'
    repo.mkdir(); home.mkdir()
    commands = CommandLog(output)
    # These are fixture process variables, never modifications to user settings.
    env = {key:value for key,value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T078 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T078 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    credential = fixture / 'operator-credential.json'
    env['A2A_OPERATOR_CREDENTIAL'] = str(credential)
    node = shutil.which('node')
    cli = [node, backend / 'workbench/src/gates/cli.ts', '--state', state]
    task = 'input-contract'
    result = {'status':'INCOMPLETE','task':'T-078-1','ready_rev':1,'argv':sys.argv,
              'source':str(source),'backend_source':str(backend),'fixture':str(fixture),'checks':[],
              'runtime':'production Electron/daemon/node-pty with deterministic receiver',
              'receiver_is_vendor_cli':False,'claude_started':False,'real_model_turns':0,
              'user_input_source':'test-simulated-user','setup_complete':False,'cleanup_complete':False}
    started = False
    window = None
    failure = False

    def save(name, data):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    def run(argv, *, expected=0, timeout=60, command_env=None):
        p = commands.run(argv, cwd=source, env=env if command_env is None else command_env, timeout=timeout)
        if expected is not None and p.returncode != expected:
            raise RuntimeError({'command_failed':p.evidence})
        return p

    def call(command, *values):
        value = command_json(run([*cli, command, *values]))
        if value.get('ok') is not True:
            raise RuntimeError({'setup_or_cleanup_rejected':value})
        return value

    def query(table):
        with closing(sqlite3.connect((state / 'state.sqlite3').as_uri()+'?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM '+table+' ORDER BY rowid')]

    def check(name, passed, expected, observed):
        result['checks'].append({'name':name,'status':'PASS' if passed else 'INCOMPLETE',
                                 'kind':'contract','expected':expected,'observed':observed})
        save('results.json',result)

    try:
        if not node or not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('Node and mounted external build volume are required; no install or fallback')
        result['source_revision'] = run(['git','rev-parse','HEAD']).stdout.strip()
        result['product_diff'] = run(['git','diff','--','workbench/src','workbench/app','workbench/hooks']).stdout
        result['node_version'] = run([node,'--version']).stdout.strip()
        run(['git','-C',repo,'init','-b','main'])
        (repo / 'value.txt').write_text('夹具基线\n',encoding='utf-8')
        run(['git','-C',repo,'add','value.txt'])
        run(['git','-C',repo,'commit','-m','T078 independent input fixture'])
        receiver = fixture / 'terminal-receiver'
        if args.runtime_probe or args.input_failures or args.worker_inbox:
            run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',
                 source/'workbench/tests/t078_native_receiver.c','-o',receiver])
        else:
            original_receiver = Path(__file__).with_name('t078_terminal_receiver.py')
            # Pin Python to this harness executable; do not resolve a vendor CLI.
            receiver.write_text('#!'+sys.executable+'\n'+original_receiver.read_text(encoding='utf-8').split('\n',1)[1],encoding='utf-8')
            receiver.chmod(0o755)
        role = fixture / 'role.md'; role.write_text('仅收集输入字节，不运行任何模型或工具。\n',encoding='utf-8')
        config = {'codex_bin':str(receiver),'codex_home':str(home),'role_card':str(role),
                  'role_card_revision':'T078-deterministic-receiver','code_revision':result['source_revision'],
                  'hook_authorization':('T078 deterministic receiver: explicitly requested synthetic Stop through hook CLI; no vendor/model'
                                        if args.runtime_probe or args.input_failures or args.worker_inbox
                                        else 'fixture only; Python byte receiver invokes no hooks'),
                  'turn_limit':10,'turn_authorization':'zero model turns; deterministic receiver'}
        if args.worker_inbox:
            config['controllers']={}
            for preset,model,effort in [('ideation','static-model-A','medium'),('executor','static-model-B','high')]:
                controller_role=fixture/(preset+'-role.md')
                controller_role.write_text('静态角色卡：'+preset+'。待真实 Claude 复核。\n',encoding='utf-8')
                config['controllers'][preset]={'executable':str(fixture/'absent-claude'),'model':model,'effort':effort,
                    'settings':{'permissions':{'allow':['Read']},'hooks':{}},
                    'role_card':str(controller_role),'role_card_revision':'T078-static-'+preset}
        config_file = fixture / 'launch.json'; config_file.write_text(json.dumps(config),encoding='utf-8')
        result['daemon_start'] = call('daemon_start','--launch-config',config_file)
        started = True
        card = {'id':task,'source':None,'goal':'验证窗口用户输入及来源记录',
                'non_goals':['不运行模型','不交付或集成代码'],
                'paths':{'allow':['value.txt'],'deny':[]},
                'oracle_paths':['value.txt'],
                'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c',
                    "from pathlib import Path; assert Path('value.txt').read_text(encoding='utf-8') == '夹具基线\\n'"]}],
                'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L',
                'executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        card_file = fixture / 'card.json'; card_file.write_text(json.dumps(card,ensure_ascii=False),encoding='utf-8')
        call('card_save','--task',task,'--card',card_file,'--expected-version','0')
        call('create','--task',task,'--repo',repo,'--branch','refs/heads/main','--card-version','1','--project','t078-fixture')
        attempt = call('dispatch','--task',task,'--runtime-mode','workspace-write')['attempt']
        result['attempt'] = attempt
        if args.reuse_build:
            build=json.loads((args.reuse_build/'build.json').read_text(encoding='utf-8'))
            if Path(build['source']).resolve()!=source/'workbench/app' or Path(build['out']).resolve()!=args.reuse_build.resolve():
                raise RuntimeError('Reused frontend build is not bound to the source')
            result['reused_frontend_build']=str(args.reuse_build)
        else:
            build = command_json(run([node, source / 'workbench/app/build.mjs','--slot','t078-input-'+fixture.name],timeout=120))
        save('build.json',build)
        window = ElectronClient(source,Path(build['out']),state,task,fixture / 'ui',output / 'window',env)
        window.wait(lambda view:'T078_DETERMINISTIC_RECEIVER_READY' in view['terminal'])
        window.call('capture',name='before-input')
        result['setup_complete'] = True

        phrase = 'T078：中文输入与来源'
        expected_bytes = ('\x1b[200~'+phrase+'\x1b[201~\r').encode('utf-8')
        window.call('terminal-input',paste=phrase,submit=True)
        deadline = time.monotonic()+3
        received = home / 'received.bin'
        while (not received.exists() or received.stat().st_size < len(expected_bytes)) and time.monotonic() < deadline:
            time.sleep(0.025)
        actual = received.read_bytes() if received.exists() else b''
        (output / 'expected-input.bin').write_bytes(expected_bytes)
        (output / 'observed-input.bin').write_bytes(actual)
        check('window_input_reaches_pty',actual == expected_bytes,
              {'bytes':len(expected_bytes),'file':'expected-input.bin'},
              {'bytes':len(actual),'file':'observed-input.bin'})
        inputs = [json.loads(row['data']) for row in query('user_inputs')]
        matching = [row for row in inputs if row.get('form') == 'message' and row.get('text') == phrase
                    and row.get('target',{}).get('attempt') == attempt['attempt_id']]
        events = query('events')
        intervention = [row for row in events if row['type'] == 'human_intervention'
                        and json.loads(row['details']).get('input_id') in {item['id'] for item in matching}]
        check('user_input_and_intervention',len(matching) == 1 and len(intervention) == 1,
              '一句独立中文输入；一个同 attempt 且带 input_id 的人工介入',
              {'matching_inputs':matching,'interventions':intervention,'all_inputs':inputs})

        # Empty composition finalized by Enter produces an empty callback plus
        # a distinct CR. Only the CR can reach the PTY or become a user action.
        before_empty = received.read_bytes() if received.exists() else b''
        window.call('terminal-empty-composition')
        deadline = time.monotonic()+3
        while (not received.exists() or received.stat().st_size < len(before_empty)+1) and time.monotonic() < deadline:
            time.sleep(0.025)
        after_empty = received.read_bytes() if received.exists() else b''
        empty_events = [row for row in query('orchestration_events') if row['type'] == 'terminal_input_empty']
        empty_details = [json.loads(row['data']) for row in empty_events]
        empty_ids = {row.get('request_id') for row in empty_details if row.get('request_id')}
        after_inputs = [json.loads(row['data']) for row in query('user_inputs')]
        empty_inputs = [row for row in after_inputs if row.get('source_ref',{}).get('command_id') in empty_ids]
        empty_interventions = [row for row in query('events') if row['type'] == 'human_intervention'
                               and json.loads(row['details']).get('event_id') in empty_ids]
        valid_metadata = len(empty_details) == 1 and all(
            row.get('window_id') and isinstance(row.get('sequence'),int) and row['sequence'] > 0
            and isinstance(row.get('received_at'),str) and row.get('request_id')
            and row.get('byte_length') == 0 for row in empty_details)
        check('empty_callback_is_observation_only',bool(valid_metadata) and not empty_inputs and not empty_interventions
              and after_empty == before_empty+b'\r',
              '空回调有窗口、序号、时刻与 request_id；不产生输入记录；只有随后 Enter 的 CR 到达 PTY',
              {'empty_events':empty_events,'empty_inputs':empty_inputs,'empty_interventions':empty_interventions,
               'before_hex':before_empty.hex(),'after_hex':after_empty.hex()})

        before = query('inbox_records')
        anonymous = {key:value for key,value in env.items() if not key.startswith('A2A_')}
        spoof = run([*cli,'inbox_send','--from','ideation','--to','executor','--kind','assign',
                     '--body','T078 无凭据请求不得冒充构思主控'],expected=None,command_env=anonymous)
        reply = command_json(spoof)
        after = query('inbox_records')
        check('anonymous_role_spoof_rejected_before_append',reply.get('ok') is False and before == after,
              '没有会话凭据时拒绝，inbox_records 完全不变',
              {'exit':spoof.returncode,'reply':reply,'before':before,'after':after})
        if args.worker_inbox:
            from t078_worker_inbox_scenario import run_worker_inbox
            run_worker_inbox(source=source,repo=repo,home=home,state=state,attempt=attempt,window=window,call=call,
                             query=query,check=check,result=result,output=output)
        elif args.input_failures:
            from t078_input_failures import run_input_failures
            run_input_failures(home=home,state=state,attempt=attempt,window=window,call=call,query=query,
                               check=check,result=result,output=output,credential=credential)
            window = None
        elif args.runtime_probe:
            from t078_runtime_scenario import run_runtime
            closed = run_runtime(home=home,state=state,attempt=attempt,window=window,call=call,query=query,
                                 check=check,result=result,output=output,credential=credential)
            if closed: window = None
        for table in ['launch_records','dispatch_records','orchestration_events','user_inputs','events','inbox_records','inbox_deliveries']:
            save('readback-'+table+'.json',query(table))
        if window: window.call('capture',name='after-input')
    except Exception as error:
        failure = True
        result['setup_or_probe_error'] = {'error':repr(error),'traceback':traceback.format_exc()}
    finally:
        try:
            if window and not result.get('runtime_window_closed'):
                window.close()
            if started:
                call('daemon_stop')
                deadline = time.monotonic()+10
                while (state / 'daemon.pid').exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                if (state / 'daemon.pid').exists():
                    raise RuntimeError('Own daemon did not finish shutdown; no automatic kill/restart')
            result['cleanup_complete'] = True
            if credential.exists():
                credential.unlink()  # This run created it; never archive a capability.
                result['operator_credential_removed'] = True
        except Exception as error:
            failure = True
            result['cleanup_error'] = {'error':repr(error),'traceback':traceback.format_exc()}
        # A failed cleanup retains the private local capability for inspection,
        # but no archive includes it. The receiver home has no vendor auth.
        with tarfile.open(output / 'fixture.tar.gz','x:gz') as archive:
            archive.add(fixture,arcname=fixture.name,
                        filter=lambda item: None if item.name == fixture.name+'/operator-credential.json' else item)
        expected_count = 14 if args.worker_inbox else 11 if args.input_failures else 12 if args.runtime_probe else 4
        result['status'] = 'PASS' if not failure and len(result['checks']) == expected_count and all(row['status'] == 'PASS' for row in result['checks']) else 'INCOMPLETE'
        save('results.json',result)
    print(json.dumps({'status':result['status'],'setup_error':failure,'checks':[{k:row[k] for k in ['name','status']} for row in result['checks']]},ensure_ascii=False))
    return 2 if failure else 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
