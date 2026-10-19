"""T-105 real Electron/daemon/zsh. No model, no screenshots, temporary fixtures only.

Baseline and candidate use the same installed internal-disk Electron and independent
fixture oracle. Summaries retain the exact commands; raw driver output is temporary.
"""
import argparse, json, os, re, shutil, sqlite3, subprocess, tempfile, time, traceback, uuid
from pathlib import Path
from run_t103_picker import Window


def main():
    parser=argparse.ArgumentParser()
    for name in ['source','baseline','electron-dist','summary']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();source=args.source.resolve();baseline=args.baseline.resolve()
    out=args.summary.resolve();assert not out.exists(),'保留已有摘要，请换新文件名'
    fixture=Path(tempfile.mkdtemp(prefix='t105-run-',dir='/private/tmp')).resolve()
    home=fixture/'home';home.mkdir();(home/'.zshrc').write_text("PS1='T105% '\n",encoding='utf-8')
    state=fixture/'state';env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','CLAUDE_','ANTHROPIC_','GIT_'))}
    for key in ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE']:env.pop(key,None)
    dist=args.electron_dist.resolve(strict=True);binary=dist/'Electron.app/Contents/MacOS/Electron'
    assert not binary.is_relative_to('/Volumes') and (dist/'version').read_text().strip()=='43.4.1'
    env.update(HOME=str(home),SHELL='/bin/zsh',ELECTRON_OVERRIDE_DIST_PATH=str(dist),TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
    report=dict(status='INCOMPLETE',task='T-105',attempt='a1',argv=list(map(str,__import__('sys').argv)),checks=[],commands=[],model_calls=0)
    windows=[];pid=None;active=None;epoch=0;builds=[];owned=set()
    def run(argv,cwd=source):
        value=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,capture_output=True,text=True,timeout=180)
        report['commands'].append(dict(argv=list(map(str,argv)),exit=value.returncode,stdout=value.stdout[-8000:],stderr=value.stderr[-4000:]))
        assert value.returncode==0,report['commands'][-1]
        return value.stdout
    def call(command,*fields):return json.loads(run(['node',active/'workbench/src/gates/cli.ts','--state',state,command,*fields]))
    def until(read,description):
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            v=read()
            if v:return v
            time.sleep(.1)
        raise AssertionError(description)
    def absent(process):
        p=subprocess.run(['/bin/ps','-p',str(process),'-o','stat='],capture_output=True,text=True,timeout=5)
        assert p.returncode in (0,1) and not p.stderr
        return not p.stdout.strip() or p.stdout.strip().startswith('Z')
    def start(root):
        nonlocal active,pid,epoch
        active=root;epoch+=1;env['A2A_OPERATOR_CREDENTIAL']=str(fixture/f'operator-{epoch}.json')
        pid=call('daemon_start')['pid'];until(lambda:not call('pane_layout').get('recovering'),'recovery pending')
    def stop():
        nonlocal pid
        if pid is None:return
        call('daemon_stop');until(lambda:not (state/'control.sock').exists() and absent(pid),'daemon exit unconfirmed');pid=None
    def build(root,label):
        result=json.loads(run(['node',root/'workbench/app/build.mjs','--slot','t105-'+label+'-'+uuid.uuid4().hex[:8]]).splitlines()[-1])
        builds.append(Path(result['out']).parent);return Path(result['out'])
    def window(root,build_dir,label,task=None):
        return Window(root,source/'workbench/tests/t105_panes_driver.mjs',build_dir,state,fixture/(label+'-ui'),fixture/label,
                      env,windows,dict(executable=str(binary),dist=str(dist),version='43.4.1'),task,through_start=False)
    def check(text):report['checks'].append(text)
    def choose(win,key,label):win.call('menu',key=key);win.wait(lambda v:len(v['menu'])==6);win.call('menu-item',label=label)
    def inventory():
        with sqlite3.connect(state/'state.sqlite3') as db:
            return list(db.execute("SELECT id FROM launch_records WHERE json_extract(data,'$.role')='shell' ORDER BY id"))
    try:
        start(baseline);red=window(baseline,build(baseline,'red'),'red')
        view=red.wait(lambda v:v['newTerminal'] is not None and '正在读取列表' not in v['text'])
        assert view['newTerminal']['disabled'] and 'paneAction' not in view['bridge']
        assert red.call('bridge',operation='newTerminal')['rejected']
        assert not view['panes'];red.close();stop();check('真实 Electron 基线：空库禁用新建、无窗格菜单桥接，预期红态')
        start(source);green_build=build(source,'green');green=window(source,green_build,'green')
        green.wait(lambda v:v['newTerminal'] and not v['newTerminal']['disabled'])
        green.call('new-terminal');v=green.wait(lambda v:len(v['panes'])==1 and v['panes'][0]['input']);first=v['panes'][0]
        record=call('launch_show','--launch',first['launch'])['launch'];assert record['project'] is None and record['worktree']==str(home)
        marker='t105-'+uuid.uuid4().hex
        green.call('terminal-input',key=first['key'],text=f"printf '%s\\n' '{marker}'; pwd")
        green.wait(lambda v:marker in v['panes'][0]['terminal'] and str(home) in v['panes'][0]['terminal'])
        check('空库点击新建，真实 zsh 输入与家目录 cwd 正确')
        choose(green,first['key'],'向右分屏');v=green.wait(lambda v:len(v['panes'])==2 and all(p['input'] for p in v['panes']))
        second=next(p for p in v['panes'] if p['launch']!=first['launch']);assert second['rect']['x']>first['rect']['x']
        choose(green,second['key'],'向下分屏');v=green.wait(lambda v:len(v['panes'])==3 and all(p['input'] for p in v['panes']))
        third=next(p for p in v['panes'] if p['launch'] not in [first['launch'],second['launch']]);assert third['rect']['y']>next(p for p in v['panes'] if p['launch']==second['launch'])['rect']['y']
        green.call('menu',key=third['key']);green.wait(lambda v:'重命名窗格'==v['focused'])
        green.call('key',keyCode='Down');green.wait(lambda v:v['focused']=='向右分屏')
        green.call('key',keyCode='Escape');green.wait(lambda v:not v['menu']);check('右/下分屏几何位置正确，菜单方向键和 Escape 可用')
        choose(green,first['key'],'放大');v=green.wait(lambda v:sum(p['visible'] for p in v['panes'])==1)
        assert next(p for p in v['panes'] if p['visible'])['launch']==first['launch']
        choose(green,first['key'],'还原');green.wait(lambda v:sum(p['visible'] for p in v['panes'])==3)
        choose(green,first['key'],'重命名窗格');green.call('rename',name='我的终端');green.call('rename-save')
        green.wait(lambda v:any(p['name']=='我的终端' for p in v['panes']))
        green.call('resize',width=1050,height=760);v=green.wait(lambda v:all(p['rect']['w']>0 and p['rect']['h']>0 for p in v['panes']))
        assert not any(p['alerts'] for p in v['panes']);check('放大/还原、中文改名、缩小窗口保持分屏')
        # A real raw-tty receiver enables SGR mouse reporting and records its bytes.
        mouse=fixture/'mouse.py';received=fixture/'mouse.bin';ready=fixture/'mouse-ready'
        mouse.write_text("import os,sys,termios,tty\nfd=sys.stdin.fileno();old=termios.tcgetattr(fd)\ntry:\n tty.setraw(fd);os.write(1,b'\\x1b[?1000h\\x1b[?1006h');open(sys.argv[2],'w').close()\n with open(sys.argv[1],'ab',buffering=0) as out:\n  while True: out.write(os.read(fd,256))\nfinally:\n termios.tcsetattr(fd,termios.TCSANOW,old)\n",encoding='utf-8')
        green.call('terminal-input',key=first['key'],text=f"python3 {mouse} {received} {ready}")
        until(lambda:ready.exists(),'mouse receiver not ready');time.sleep(.3)
        green.call('right-click',key=first['key']);green.wait(lambda v:len(v['menu'])==6)
        assert received.stat().st_size==0
        green.call('menu-item',label='把右键发给窗格');green.wait(lambda v:not v['menu'])
        green.call('right-click',key=first['key']);until(lambda:received.stat().st_size>0,'right click not delivered')
        data=received.read_bytes();assert re.search(rb'\x1b\[<2;[0-9]+;[0-9]+M',data),repr(data)
        assert not green.call('inspect')['menu']
        choose(green,first['key'],'把右键发给窗格');size=received.stat().st_size
        green.call('right-click',key=first['key']);green.wait(lambda v:len(v['menu'])==6);assert received.stat().st_size==size
        green.call('key',keyCode='Escape');check('真实 PTY 程序：关时弹菜单且无鼠标字节，开时收到右键 SGR 协议，关回后恢复菜单')
        tree=call('pane_process_info','--thread',record['thread']);owned.update(p['pid'] for p in tree['processes'])
        choose(green,first['key'],'关闭窗格');green.wait(lambda v:len(v['panes'])==2)
        until(lambda:all(absent(p) for p in owned),'closed terminal child remains alive')
        check('菜单关闭结束 zsh 及鼠标程序子进程')
        choose(green,second['key'],'重命名窗格');green.call('rename',name='保留布局');green.call('rename-save')
        green.wait(lambda v:any(p['name']=='保留布局' for p in v['panes']))
        retained={second['launch'],third['launch']};before=inventory();green.close()
        same_daemon=window(source,green_build,'view-reopened');same_daemon.wait(lambda v:len(v['panes'])==2 and all(p['input'] for p in v['panes']) and any(p['name']=='保留布局' for p in v['panes']))
        assert inventory()==before;same_daemon.close();check('只重开界面保留布局/名字，仍连接原后台终端，没有重跑进程')
        stop();start(source)
        reopened=window(source,green_build,'reopened');v=reopened.wait(lambda v:len(v['panes'])==2 and all(p['lifecycle']=='ended' for p in v['panes']))
        assert inventory()==before and {p['launch'] for p in v['panes']}==retained and not any(p['input'] for p in v['panes'])
        assert any(p['name']=='保留布局' for p in v['panes']);rects=sorted([p['rect'] for p in v['panes']],key=lambda p:p['y']);assert rects[1]['y']>rects[0]['y']
        reopened.close();check('关闭并重启后台/应用后恢复下分屏及名字；普通终端已结束、只读，无新 shell launch')
        events=call('orchestration_events')['events'];assert marker not in json.dumps(events)
        forbidden={'window_input','window_composition','window_observation','window_release'}
        assert not any(e['type'] in ['request_received','request_result','request_rejected'] and (e['data'].get('command') or e['data'].get('input',{}).get('command')) in forbidden for e in events)
        with sqlite3.connect(state/'state.sqlite3') as db:
            assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0]==0
            assert db.execute('SELECT count(*) FROM user_input_ingress').fetchone()[0]==0
        check('普通终端输入正文和逐次输入元数据未进事件流/agent 输入记录')
        # Independent historical records: no CLI/model is started. Check that
        # pane controls cannot turn a view close into attempt reclamation.
        stop()
        attempt=dict(attempt_id='fixture-a1',session_id='fixture-session',thread_id='fixture-worker-thread',fence=1,spec_rev=1,reclaimed=False)
        task=dict(task_id='fixture-task',title='受管关闭反例',project_id='fixture-project',repo=str(home),state='claimed',spec_rev=1,
                  current_attempt=attempt,candidate_commit=None,verification=None,integration_intent=None)
        with sqlite3.connect(state/'state.sqlite3') as db:
            db.execute('INSERT INTO tasks VALUES (?,?)',(task['task_id'],json.dumps(task)))
            db.execute('INSERT INTO attempts VALUES (?,?)',(attempt['attempt_id'],json.dumps(attempt)))
            for i,role in enumerate(['controller','controller','worker','reviewer']):
                launch='fixture-agent-'+str(i);thread='fixture-worker-thread' if role=='worker' else 'fixture-thread-'+str(i)
                record=dict(id=launch,thread=thread,task=task['task_id'],project=task['project_id'],role=role,
                            preset=['ideation','executor',None,None][i],attempt=None if role=='controller' else attempt['attempt_id'],
                            session=attempt['session_id'],fence=1,spec_rev=1,created_at='2026-10-19T00:00:00Z',cli_version='只读夹具',model_requested='无模型')
                db.execute('INSERT INTO launch_records VALUES (?,?,?,?)',(launch,record['task'],record['attempt'],json.dumps(record)))
                db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                           ('2026-10-19T00:00:00Z','pane_layout_opened',launch,record['task'],record['attempt'],json.dumps(dict(position=i,native_session=None,resume_argv=None))))
                trace=state/'traces'/launch;trace.mkdir();(trace/'pty.raw').write_text('只读恢复夹具\r\n',encoding='utf-8')
        start(source);agents=window(source,green_build,'agents',task['task_id'])
        v=agents.wait(lambda v:len(v['panes'])==4 and all('未恢复' in p['text'] and not p['input'] for p in v['panes']))
        review=next(p for p in v['panes'] if p['role']=='reviewer');worker=next(p for p in v['panes'] if p['role']=='worker')
        choose(agents,review['key'],'重命名窗格');agents.call('rename',name='审查记录');agents.call('rename-save')
        agents.wait(lambda v:any(p['name']=='审查记录' for p in v['panes']))
        choose(agents,worker['key'],'向右分屏');v=agents.wait(lambda v:len(v['panes'])==5 and any(p['role']=='shell' and p['input'] for p in v['panes']))
        shell=next(p for p in v['panes'] if p['role']=='shell');choose(agents,shell['key'],'关闭窗格');agents.wait(lambda v:len(v['panes'])==4)
        before_task=call('status','--task',task['task_id'])['task']
        with sqlite3.connect(state/'state.sqlite3') as db:before_attempt=db.execute('SELECT data FROM attempts WHERE id=?',(attempt['attempt_id'],)).fetchone()[0]
        choose(agents,worker['key'],'关闭窗格');agents.wait(lambda v:len(v['panes'])==3)
        assert call('status','--task',task['task_id'])['task']==before_task
        with sqlite3.connect(state/'state.sqlite3') as db:assert db.execute('SELECT data FROM attempts WHERE id=?',(attempt['attempt_id'],)).fetchone()[0]==before_attempt
        agent_events=call('orchestration_events')['events']
        assert any(e['type']=='request_received' and e['data'].get('input',{}).get('command')=='pane_layout_close' and e['data']['input'].get('launch')==worker['launch'] for e in agent_events)
        assert not any(e['type']=='pane_archived' and e.get('launch')==worker['launch'] for e in agent_events)
        agents.close();check('恢复失败的主控/worker/reviewer保留只读；菜单可改名/分屏；关闭worker经既有入口，仅移除视图，task和attempt逐字段不变')
        report['limitations']=['受管窗格使用独立历史夹具；本脚本不调用模型，未复验活跃真实worker的人工介入。独立只读审查须由执行主控另开。']
        report['status']='PASS'
    except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:win.close()
            stop()
            assert all(absent(p) for p in owned)
            report['cleanup_complete']=True
        except Exception as error:report.update(status='INCOMPLETE',cleanup_error=repr(error),cleanup_complete=False,retained_fixture=str(fixture))
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if report.get('cleanup_complete'):
            shutil.rmtree(fixture)
            for build_root in builds:shutil.rmtree(build_root)
    print(json.dumps(report,ensure_ascii=False));return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
