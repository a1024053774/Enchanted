#!/bin/bash
set -euo pipefail
# 交执行主控在沙箱外运行；只写新建的 /tmp 目录，不安装、不构建、不提交。
# 结果路径见最后的 output；未确认的进程保留身份和现场，不发送终止信号。
/usr/bin/python3 -B - <<'T103_REVIEW_PY'
import datetime, importlib.util, json, os, sqlite3, subprocess, sys, tempfile, time, traceback, uuid
from pathlib import Path
from contextlib import closing

source = Path('/Users/luckye/Documents/Code/a2a-wt-t103')
revision = '1acfeccf86e7b7b6962cc289b8af48037627ef8e'
out = Path(tempfile.mkdtemp(prefix='t103-review-outside-01-', dir='/tmp')).resolve()
report = {'status':'INCOMPLETE', 'candidate':revision, 'output':str(out), 'checks':[], 'model_calls':0,
          '范围':'独立新输入；真实 CLI/SQLite 与同一内置盘 Electron；复用已保存的候选构建，不重新构建'}
commands, owned, daemons = [], [], []
env = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','GIT_'))}
for key in ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE']: env.pop(key,None)
env.update(A2A_OPERATOR_CREDENTIAL=str(out/'operator.json'), TMPDIR=str(out), TMP=str(out), TEMP=str(out))

def save():
    (out/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(argv, expected=0, timeout=30, local_env=env):
    value=subprocess.run([str(x) for x in argv],cwd=source,env=local_env,capture_output=True,text=True,timeout=timeout)
    commands.append({'argv':[str(x) for x in argv],'exit':value.returncode,'stdout':value.stdout,'stderr':value.stderr})
    save()
    assert value.returncode in (expected if isinstance(expected,tuple) else (expected,)), commands[-1]
    return value

def call(state, command, *args, expected=0, local_env=env):
    return json.loads(run(['node',source/'workbench/src/gates/cli.ts','--state',state,command,*args],expected,local_env=local_env).stdout)

def check(name):
    report['checks'].append({'name':name,'status':'PASS'});save()

def start(label):
    state=out/(label+'-state')
    local_env=dict(env,A2A_OPERATOR_CREDENTIAL=str(out/(label+'-operator.json')))
    result=call(state,'daemon_start',local_env=local_env)
    daemons.append((state,local_env,result['pid']))
    return state,local_env

try:
    assert run(['git','rev-parse','HEAD']).stdout.strip()==revision
    archive=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-20261019T063741Z')
    accepted=json.loads((archive/'run.json').read_text(encoding='utf-8'))
    assert accepted['status']=='PASS'
    for name in accepted['source_files']:
        assert (source/name).read_bytes()==(archive/'source-snapshot'/name).read_bytes(), name
    runtime=accepted['electron_runtime']
    assert runtime['version']=='43.4.1' and not Path(runtime['executable']).resolve().is_relative_to('/Volumes')
    env['ELECTRON_OVERRIDE_DIST_PATH']=runtime['dist']
    build=Path(json.loads((archive/'green-build.json').read_text(encoding='utf-8'))['out'])
    assert build.is_dir()
    report.update(electron_runtime=runtime, build=str(build), accepted_archive=str(archive))
    # 只复用观察边界；下面的输入与预期由本次 reviewer 给定。
    spec=importlib.util.spec_from_file_location('picker_observer', source/'workbench/tests/run_t103_picker.py')
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    state,local_env=start('populated')
    nonce=uuid.uuid4().hex[:7]
    rows=[]
    for p in range(2):
        for t in range(2):
            task=f'review-{p}-{t}-{nonce}'
            rows.append({'task_id':task,'project_id':f'review-project-{p}-{nonce}',
                         'title':f'独立审查 <项目{p}> 任务{t} · {nonce}',
                         'state':['ready','paused'][t], 'launch':'review-launch-'+uuid.uuid4().hex,
                         'trace':f'REVIEW {task} :: {uuid.uuid4().hex[:9]}'})
    (out/'expected.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with closing(sqlite3.connect(state/'state.sqlite3')) as db:
        for row in rows:
            task={k:row[k] for k in ['task_id','project_id','title','state']}
            task.update(spec_rev=1,current_attempt=None,candidate_commit=None,verification=None,integration_intent=None)
            db.execute('INSERT INTO tasks(id,data) VALUES (?,?)',(row['task_id'],json.dumps(task)))
            record={'id':row['launch'],'task':row['task_id'],'project':row['project_id'],'attempt':'historical-review',
                    'session':'historical-review','fence':1,'spec_rev':1,'thread':'thread-'+row['launch'],
                    'role':'worker','preset':None,'cli':'fixture-only','cli_version':'独立历史夹具','model_requested':'无模型',
                    'created_at':'2026-10-19T00:00:00Z'}
            db.execute('INSERT INTO launch_records(id,task,attempt,data) VALUES (?,?,?,?)',
                       (row['launch'],row['task_id'],'historical-review',json.dumps(record)))
            db.execute('INSERT INTO orchestration_events(time,type,launch,task,attempt,data) VALUES (?,?,?,?,?,?)',
                       ('2026-10-19T00:00:00Z','pane_layout_opened',row['launch'],row['task_id'],'historical-review',json.dumps({'position':0})))
            trace=state/'traces'/row['launch'];trace.mkdir(parents=True)
            (trace/'pty.raw').write_bytes((row['trace']+'\r\n').encode('utf-8'))
        db.commit()
    def db_bytes():
        return {p.name:p.read_bytes() for p in state.iterdir() if p.name.endswith(('.sqlite3','.sqlite3-wal'))}
    before=db_bytes();before_locks=sorted(p.name for p in (state/'locks').iterdir())
    assert call(state,'projects_list',local_env=local_env)['projects']==[{'project_id':f'review-project-{p}-{nonce}'} for p in range(2)]
    for p in range(2):
        expected=[{k:r[k] for k in ['task_id','project_id','title','state']} for r in rows if r['project_id']==f'review-project-{p}-{nonce}']
        assert call(state,'tasks_list','--project',f'review-project-{p}-{nonce}',local_env=local_env)['tasks']==expected
    assert call(state,'tasks_list','--project','absent-review-project',local_env=local_env)['tasks']==[]
    assert call(state,'tasks_list','--project','../invalid',expected=1,local_env=local_env)['error']=='invalid_id'
    assert before==db_bytes(), '列表命令改变 SQLite/WAL'
    assert before_locks==sorted(p.name for p in (state/'locks').iterdir()), '列表命令改变操作锁目录'
    report['readonly']={'equal':True,'files':{k:len(v) for k,v in before.items()}}
    check('新输入：真实列表 CLI 的内容、错误输入、库/WAL 字节与操作锁')
    def window(label, st, en, task=None):
        return observer.Window(source,source/'workbench/tests/t103_picker_driver.mjs',build,st,out/(label+'-ui'),
                               out/label,en,owned,runtime,task=task)
    win=window('picker',state,local_env)
    view=win.wait(lambda v:v['busy']=='false' and len(v['tasks'])==4)
    assert view['heading']=='选择任务' and not view['panes']
    assert set(view['projects'])=={r['project_id'] for r in rows}
    assert [r['id'] for r in view['tasks']]==[r['task_id'] for r in rows]
    old_key=None
    for index in [3,0,2,1]:
        row=rows[index];win.call('select',task=row['task_id'])
        view=win.wait(lambda v:len(v['panes'])==1 and v['panes'][0].get('task')==row['task_id'] and row['trace'] in v['panes'][0]['terminal'])
        assert view['heading']==row['title'] and view['panes'][0]['launch']==row['launch']
        if old_key: assert win.call('bridge',operation='snapshot',args=[old_key])['rejected']
        old_key=view['panes'][0]['key']
    assert win.call('bridge',operation='selectTask',args=['absent-review-task'])['rejected']
    assert win.call('inspect')['heading']==rows[1]['title']
    win.call('capture',name='review-switched')
    check('新输入：选择页、四任务跨项目切换、旧 key 与不存在任务拒绝')
    with closing(sqlite3.connect(state/'state.sqlite3')) as db:
        original=db.execute('SELECT data FROM tasks WHERE id=?',(rows[1]['task_id'],)).fetchone()[0]
        (out/'removed-row.json').write_text(original+'\n',encoding='utf-8')
        db.execute('DELETE FROM tasks WHERE id=?',(rows[1]['task_id'],));db.commit()
    win.call('refresh');view=win.wait(lambda v:v['busy']=='false' and len(v['tasks'])==3 and not v['panes'])
    assert view['heading']=='选择任务' and not view['alerts']
    win.call('capture',name='review-removed');win.close()
    check('隔离 SQL 删除后刷新；此项仍不宣称经门禁移除')
    win=window('explicit',state,local_env,rows[2]['task_id'])
    view=win.wait(lambda v:len(v['panes'])==1 and v['panes'][0].get('task')==rows[2]['task_id'] and rows[2]['trace'] in v['panes'][0]['terminal'])
    assert view['heading']==rows[2]['title'];win.call('capture',name='review-explicit');win.close()
    empty,empty_env=start('empty');win=window('empty',empty,empty_env)
    view=win.wait(lambda v:v['busy']=='false' and '还没有项目' in v['text'])
    assert not view['tasks'] and not view['panes'] and not view['alerts']
    win.call('capture',name='review-empty');win.close()
    check('显式 task 启动与空库中文提示')
    report['status']='PASS'
except Exception as error:
    report.update(error=repr(error),traceback=traceback.format_exc())
finally:
    try:
        for win in owned: win.close()
        for state,local_env,pid in reversed(daemons):
            call(state,'daemon_stop',local_env=local_env)
            deadline=time.monotonic()+10
            while True:
                value=run(['/bin/ps','-p',str(pid),'-o','pid=,command='],expected=(0,1))
                assert not value.stderr.strip(), '无法核对后台退出'
                if value.returncode==1 and not value.stdout.strip() and not (state/'daemon.pid').exists(): break
                if time.monotonic()>=deadline: raise RuntimeError(f'后台退出未确认：{pid}')
                time.sleep(.1)
    except Exception as error:
        report.update(status='INCOMPLETE',cleanup_error=repr(error),cleanup_traceback=traceback.format_exc())
    save()
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)

T103_REVIEW_PY
