"""真实 Electron → main.run → daemon → zsh；不启动供应商 CLI 或模型。

只观察真实 DOM/IPC/PTY。独立 nonce、cwd 与子进程由本夹具给出；历史 agent
输出仅作只读并存夹具，不冒称运行过 agent。原始证据写到挂载外置盘。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from run_t103_picker import Window, save


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--electron-dist',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--red-only',action='store_true')
    args=parser.parse_args()
    source,baseline,out=args.source.resolve(),args.baseline.resolve(),args.output.resolve()
    disk=Path('/Volumes/WD-Elements')
    assert disk.is_mount() and out.is_relative_to(disk),'外置盘未挂载或输出路径错误'
    out.mkdir(exist_ok=False); (out/'tmp').mkdir()
    dist=args.electron_dist.resolve(strict=True)
    binary=(dist/'Electron.app/Contents/MacOS/Electron').resolve(strict=True)
    assert not binary.is_relative_to('/Volumes') and binary.stat().st_dev!=disk.stat().st_dev
    assert (dist/'version').read_text().strip()=='43.4.1'
    runtime=dict(dist=str(dist),executable=str(binary),version='43.4.1')
    fixture=Path(tempfile.mkdtemp(prefix='a2at104ui-',dir='/private/tmp')).resolve()
    home=fixture/'home'; home.mkdir()
    (home/'.zprofile').write_text('export T104_LOGIN_RC=loaded\n',encoding='utf-8')
    (home/'.zshrc').write_text("PS1='T104% '\n",encoding='utf-8')
    state=fixture/'state'
    env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','GIT_','CLAUDE_','ANTHROPIC_'))}
    env.pop('NODE_OPTIONS',None);env.pop('ELECTRON_RUN_AS_NODE',None)
    env.update(HOME=str(home),SHELL='/bin/zsh',ELECTRON_OVERRIDE_DIST_PATH=str(dist),
               GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_COUNT='2',
               GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign',GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T104 fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T104 fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid',
               TMPDIR=str(out/'tmp'),TMP=str(out/'tmp'),TEMP=str(out/'tmp'))
    report=dict(status='INCOMPLETE',task='T-104',attempt='a1',part=2,argv=sys.argv,checks=[],commands=[],
                fixture=str(fixture),archive=str(out),electron=runtime,screenshots=[],model_calls=0,
                revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip())
    names=['README.md','app/main.ts','app/preload.ts','app/renderer.tsx','app/start.mjs','app/style.css',
           'src/panes.ts','src/daemon.ts','src/store.ts','src/gates/cli.ts',
           'tests/run_t104_shell_ui.py','tests/t104_shell_driver.mjs',
           'tests/test_t104_shell_e2e.py',
           'tests/test_t091_pane_ipc.mjs','tests/test_electron_e2e.py']
    report['source_files']=['workbench/'+name for name in names]
    for name in names:
        dest=out/'source-snapshot/workbench'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/'workbench'/name,dest)
    (out/'candidate.diff').write_bytes(subprocess.check_output(['git','diff','HEAD','--','workbench'],cwd=source))
    windows=[];active=None;daemon_pid=None;credential=None;epoch=0;pids=set()
    nonce='T104-'+uuid.uuid4().hex
    checkpoint='setup'

    def run(argv,cwd=source):
        result=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
        report['commands'].append(dict(argv=list(map(str,argv)),exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
        save(out/'commands.json',report['commands'])
        assert result.returncode==0,report['commands'][-1]
        return result.stdout

    def call(command,*fields):
        return json.loads(run(['node',active/'workbench/src/gates/cli.ts','--state',state,command,*fields]))

    def absent(pid):
        result=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,stat=,command='],capture_output=True,text=True,timeout=5)
        report.setdefault('process_checks',[]).append(dict(pid=pid,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
        assert result.returncode in (0,1) and not result.stderr
        return not result.stdout.strip() or result.stdout.split()[1].startswith('Z')

    def until(read,description):
        end=time.monotonic()+10
        while time.monotonic()<end:
            result=read()
            if result:return result
            time.sleep(.1)
        raise AssertionError(description)

    def start(root):
        nonlocal active,daemon_pid,credential,epoch
        epoch+=1;active=root;credential=fixture/f'operator-{epoch}.json'
        env['A2A_OPERATOR_CREDENTIAL']=str(credential)
        result=call('daemon_start');daemon_pid=result['pid']
        until(lambda: not call('pane_layout').get('recovering'), '后台恢复没有结束')

    def stop():
        nonlocal daemon_pid
        if daemon_pid is None:return
        call('daemon_stop')
        until(lambda: not (state/'control.sock').exists() and absent(daemon_pid),'后台退出未确认')
        daemon_pid=None

    def build(root,label):
        return Path(json.loads(run(['node',root/'workbench/app/build.mjs','--slot','t104-'+label+'-'+uuid.uuid4().hex[:10]]).splitlines()[-1])['out'])

    def window(root,build_dir,label,task=None):
        return Window(root,source/'workbench/tests/t104_shell_driver.mjs',build_dir,state,fixture/(label+'-ui'),
                      out/label,env,windows,runtime,task,through_start=False)

    def capture(win,label,name):
        value=win.call('capture',name=name)
        report['screenshots'].append(str(out/label/(name+'.png')))
        return value

    def check(name):report['checks'].append(dict(name=name,status='PASS'))

    try:
        checkpoint='baseline setup';start(baseline)
        tasks=[]
        for project in ['alpha','beta']:
            repo=fixture/('中文项目 '+project);repo.mkdir()
            run(['git','init','-b','main',repo]);(repo/'criterion.py').write_text('assert True\n',encoding='utf-8')
            run(['git','-C',repo,'add','criterion.py']);run(['git','-C',repo,'commit','-m','T104 isolated fixture'])
            for number in range(2 if project=='alpha' else 1):
                task=f'{project}-{number}';card=fixture/(task+'.json')
                save(card,dict(id=task,source=None,goal='普通终端界面验收',non_goals=['不调用模型'],
                     paths=dict(allow=['criterion.py'],deny=[]),oracle_paths=['criterion.py'],
                     completion_conditions=[dict(argv=['python3','criterion.py'])],red_commands=[],task_type='前端界面',
                     repair_target=None,complexity='M',executor=dict(cli='Codex',model='gpt-6.1-sol',effort='xhigh'),base_commit=None,writer=None))
                call('card_save','--task',task,'--card',card,'--expected-version','0')
                call('create','--task',task,'--repo',repo,'--branch','refs/heads/main','--card-version','1','--project',project,'--title','终端验收 '+task)
                tasks.append(dict(task=task,project=project,repo=str(repo)))
        # Independently supplied, read-only historical agent to check coexistence.
        agent=dict(id='fixture-agent',task='alpha-0',project='alpha',attempt='historical-a1',session='historical',
                   fence=1,spec_rev=1,thread='fixture-agent-thread',role='worker',preset=None,cli='fixture-only',
                   cli_version='只读历史夹具',model_requested='无模型',created_at='2026-10-19T00:00:00Z')
        trace=state/'traces/fixture-agent';trace.mkdir(parents=True)
        (trace/'pty.raw').write_text('T104 只读 agent 历史夹具\r\n',encoding='utf-8')
        with sqlite3.connect(state/'state.sqlite3') as db:
            db.execute('INSERT INTO launch_records VALUES (?,?,?,?)',('fixture-agent','alpha-0','historical-a1',json.dumps(agent)))
            db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                       ('2026-10-19T00:00:00Z','pane_layout_opened','fixture-agent','alpha-0','historical-a1',json.dumps(dict(position=0,native_session=None,resume_argv=None))))
        checkpoint='real UI red'
        red=window(baseline,build(baseline,'red'),'red','alpha-0')
        red_view=red.wait(lambda v:any(p.get('launch')=='fixture-agent' for p in v['panes']))
        assert red_view['newTerminal'] is None and 'newTerminal' not in red_view['bridge'] and 'a2a:new-terminal' not in red_view['channels']
        assert red.call('bridge',operation='newTerminal')['rejected'] is True
        capture(red,'red','red-no-terminal');red.close();check('已知坏版本：真实窗口无入口、无公开桥接与主进程 handler')
        stop()
        if not args.red_only:
            checkpoint='green start';start(source);green_build=build(source,'green')
            green=window(source,green_build,'green')
            initial=green.wait(lambda v:len(v['tasks'])==3 and v['newTerminal'] is not None)
            assert initial['newTerminal']['disabled'] is True
            assert green.call('bridge',operation='newTerminal')['rejected'] is True
            green.call('select',task='alpha-0')
            green.wait(lambda v:any(p.get('launch')=='fixture-agent' for p in v['panes']) and v['newTerminal'] and not v['newTerminal']['disabled'])
            checkpoint='new terminal';green.call('new-terminal')
            view=green.wait(lambda v:any(p.get('role')=='shell' and p['input'] for p in v['panes']))
            shell=next(p for p in view['panes'] if p.get('role')=='shell')
            assert any(p.get('role')=='worker' and not p['input'] for p in view['panes'])
            assert shell.get('task') in (None,'') and '普通终端' in shell['text']
            assert '人工介入' not in shell['text'] and '历史 attempt' not in shell['text']
            record=call('launch_show','--launch',shell['launch'])['launch']
            assert record['project']=='alpha' and record['task'] is None and record['attempt'] is None
            command=f"printf '\\n%s\\n' '{nonce}'; pwd; print -r -- LOGIN=$options[login],RC=$T104_LOGIN_RC"
            green.call('terminal-input',key=shell['key'],text=command)
            view=green.wait(lambda v:any(nonce in p['terminal'] and tasks[0]['repo'] in p['terminal'] and 'LOGIN=on,RC=loaded' in p['terminal'] for p in v['panes'] if p.get('role')=='shell'))
            capture(green,'green','green-terminal');check('点击新建终端，经 xterm 输入的 echo/pwd 与项目 cwd 正确，登录 zsh 与只读 agent 并存')
            checkpoint='close processes';green.call('terminal-input',key=shell['key'],text='/bin/sleep 300 & /bin/sleep 300')
            tree=until(lambda:(lambda r:r if len(r.get('processes',[]))>=3 else None)(call('pane_process_info','--thread',record['thread'])),'子进程未启动')
            owned=[p['pid'] for p in tree['processes']];pids.update(owned);save(out/'before-close-processes.json',tree)
            assert sum(p['command']=='/bin/sleep' for p in tree['processes'])==2
            green.call('close-pane',key=shell['key'])
            green.wait(lambda v:all(p.get('launch')!=shell['launch'] for p in v['panes']))
            until(lambda:all(absent(pid) for pid in owned),'关闭窗格后子进程仍活动')
            assert green.call('bridge',operation='input',args=[shell['key'],'stale-input'])['rejected'] is True
            capture(green,'green','green-closed');check('界面关闭结束 shell 及前后台子进程，旧 pane key 拒绝输入')
            green.call('new-terminal');view=green.wait(lambda v:any(p.get('role')=='shell' and p['input'] for p in v['panes']))
            second=next(p for p in view['panes'] if p.get('role')=='shell')
            second_record=call('launch_show','--launch',second['launch'])['launch']
            second_pid=call('pane_status','--thread',second_record['thread'])['shell_pid'];pids.add(second_pid)
            green.call('select',task='alpha-1');green.wait(lambda v:any(t['id']=='alpha-1' and t['current']=='page' for t in v['tasks'])
                and any(p.get('launch')==second['launch'] and p['input'] for p in v['panes']))
            green.call('select',task='beta-0');green.wait(lambda v:any(t['id']=='beta-0' and t['current']=='page' for t in v['tasks'])
                and not any(p.get('role')=='shell' for p in v['panes']))
            green.call('select',task='alpha-0');green.wait(lambda v:any(t['id']=='alpha-0' and t['current']=='page' for t in v['tasks'])
                and any(p.get('launch')==second['launch'] and p['input'] for p in v['panes']))
            capture(green,'green','green-project-shell');green.close()
            assert not absent(second_pid);assert call('daemon_status')['pid']==daemon_pid
            check('项目内跨任务保留同一终端，跨项目隔离；关界面不结束终端或后台')
            checkpoint='restart';stop();until(lambda:absent(second_pid),'后台停止未结束终端');start(source)
            reopened=window(source,green_build,'reopened','alpha-0')
            ended=reopened.wait(lambda v:any(p.get('launch')==second['launch'] and p['lifecycle']=='ended' for p in v['panes']))
            ended_shell=next(p for p in ended['panes'] if p.get('launch')==second['launch'])
            assert not ended_shell['input'] and '已结束' in ended_shell['text'] and not ended_shell['alerts']
            historical_agent=next(p for p in ended['panes'] if p.get('launch')=='fixture-agent')
            assert not historical_agent['input'] and '未恢复' in historical_agent['text']
            assert absent(second_pid)
            capture(reopened,'reopened','green-ended');reopened.close();check('真实界面重开后原 shell 显示已结束，只读且不自动拉起')
            checkpoint='privacy';events=call('orchestration_events')['events']
            assert nonce not in json.dumps(events,ensure_ascii=False),'shell 输入正文进入事件流'
            with sqlite3.connect(state/'state.sqlite3') as db:
                assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0]==0
                assert db.execute('SELECT count(*) FROM user_input_ingress').fetchone()[0]==0
                assert db.execute('SELECT count(*) FROM dispatch_records').fetchone()[0]==0
            for launch in [shell['launch'],second['launch']]:
                mine=[e for e in events if e.get('launch')==launch]
                assert sum(e['type']=='shell_created' for e in mine)==1 and sum(e['type']=='shell_closed' for e in mine)==1
                assert not any(e['type'].startswith('pane_restore') for e in mine)
            save(out/'events.json',events);check('创建关闭事件齐全；nonce 不进事件流、agent 输入或人工介入；无自动恢复事件')
        for name in names:assert (source/'workbench'/name).read_bytes()==(out/'source-snapshot/workbench'/name).read_bytes(),'运行期间源码变化：'+name
        report['status']='PASS'
    except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc(),checkpoint=checkpoint)
    finally:
        try:
            for win in windows:win.close()
            stop()
            for pid in pids:until(lambda:absent(pid),f'夹具进程 {pid} 未退出')
            for path in fixture.glob('operator-*.json'):path.unlink()
            shutil.copytree(fixture,out/'fixture',symlinks=True)
            old=[p for p in fixture.rglob('*') if p.is_file()];new=[p for p in (out/'fixture').rglob('*') if p.is_file()]
            assert len(old)==len(new) and sum(p.stat().st_size for p in old)==sum(p.stat().st_size for p in new)
            report.update(cleanup_complete=True,fixture_bytes=sum(p.stat().st_size for p in old));shutil.rmtree(fixture)
        except Exception as error:report.update(status='INCOMPLETE',cleanup_complete=False,cleanup_error=repr(error))
        save(out/'run.json',report)
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
