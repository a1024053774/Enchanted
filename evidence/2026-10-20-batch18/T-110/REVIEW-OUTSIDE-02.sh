#!/bin/zsh
# 第二轮独立审查；--local 只跑合同，默认另跑真实 Electron。
# 固定 git archive 候选；所有修改与依赖副本仅在本次 /tmp 目录中。
set -euo pipefail
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
REVIEW_REPO=/Users/luckye/Documents/Code/a2a-wt-t110
cd "$REVIEW_REPO"
/usr/bin/python3 -B - "$REVIEW_REPO" "$@" <<'PY'
import io, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path
repo=Path(sys.argv[1]); args=sys.argv[2:]; local='--local' in args
args=[x for x in args if x!='--local']
assert len(args)==1, '传入新的绝对结果 JSON 路径，可加 --local'
output=Path(args[0]); assert output.is_absolute() and not output.exists()
revision='aea89b9d51f7eab67d3ad4760e727ba4a275b16e'
root=Path(tempfile.mkdtemp(prefix='t078-2-review02-',dir='/private/tmp')).resolve()
copy=root/'candidate'; copy.mkdir()
env=dict(os.environ,LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
for key in ['GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE']:env.pop(key,None)
report=dict(status='INCOMPLETE',candidate=revision,mode='local' if local else 'electron',
            commands=[],contracts=[],mutations=[],model_calls=0,vendor_calls=0,screenshots=[])
def run(argv,label,cwd=repo,timeout=180):
    p=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
    report['commands'].append(dict(label=label,argv=list(map(str,argv)),cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    return p
def contract(name,label=None,extra=()):
    label=label or name; target=root/(label+'.json')
    command=['/usr/bin/python3','-B',copy/'workbench/tests'/name,'--summary',target] if name.endswith('.py') else ['node','--experimental-vm-modules',copy/'workbench/tests'/name,target,*extra]
    p=run(command,label)
    value=json.loads(target.read_text(encoding='utf-8'))
    report['contracts'].append(dict(label=label,result=value))
    return p,value
try:
    data=subprocess.check_output(['git','archive',revision,'workbench'],cwd=repo,env=env)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members=archive.getmembers()
        archive.extractall(copy,members=[m for m in members if not (m.issym() or m.islnk())])
        report['materialized_links']=[]
        for m in members:
            if m.issym() or m.islnk():
                target=copy/m.name; target.write_bytes(archive.extractfile(m).read()); target.chmod(0o755)
                report['materialized_links'].append(m.name)
    # 历史版本读取仍使用原仓库，只读 git show；不创建 .git 或 worktree。
    cleanup=copy/'workbench/tests/test_t110_cleanup.py'
    cleanup.write_text(cleanup.read_text(encoding='utf-8').replace('cwd=source, env=env','cwd='+repr(str(repo))+', env=env'),encoding='utf-8')
    center=copy/'workbench/app/notificationCenter.ts'; original=center.read_text(encoding='utf-8')
    p,v=contract('test_t091_pane_ipc.mjs','candidate-ipc',['--source',copy]);assert p.returncode==0 and v['status']=='PASS',v
    cases=[
      ('unknown-notifies',"agent.state === 'waiting_user_answer' && agent.question_id","['waiting_user_answer', 'unknown'].includes(agent.state) && agent.question_id",'test_t091_pane_ipc.mjs:326:14'),
      ('answer-keeps-notice','if (!pending.has(id)) this.active.delete(id);','if (false) this.active.delete(id);','Other states do not notify'),
      ('switch-ignored','const enabled = this.setting();','const enabled = true;','Enabling while already waiting is not a new question')]
    for label,old,new,expected in cases:
        assert original.count(old)==1
        center.write_text(original.replace(old,new),encoding='utf-8')
        p,v=contract('test_t091_pane_ipc.mjs',label,['--source',copy])
        rejected=p.returncode==1 and expected in (v.get('error','')+'\n'+v.get('stack',''))
        report['mutations'].append(dict(label=label,file='workbench/app/notificationCenter.ts',old=old,new=new,expected=expected,business_rejected=rejected,exit=p.returncode,error=v.get('error')))
        center.write_text(original,encoding='utf-8');assert rejected,v
    # 独立的新 ID 和不同项目；期望来自票，不导入产品期望常量。
    oracle=root/'independent.mjs'
    oracle.write_text('''import assert from 'node:assert/strict';
import {mkdtempSync} from 'node:fs';import {pathToFileURL} from 'node:url';
const {NotificationCenter}=await import(pathToFileURL(process.argv[2]));
const c=new NotificationCenter(mkdtempSync(process.argv[3]+'/settings-'));
const a={id:'review02-session-95',project:'复审项目丙',role_label:'构思主控',task:'task-review02',question_id:'q-review02-95'};
for(const state of ['unknown','permission','running','idle','waiting_controller_answer','ended']){assert.equal(c.observe([{...a,state}]).length,0);assert.equal(c.badgeCount(),0);}
assert.deepEqual(c.observe([{...a,state:'waiting_user_answer'}]).map(n=>[n.id,n.launch,n.project]),[['q-review02-95','review02-session-95','复审项目丙']]);
for(let i=0;i<5;i++)assert.equal(c.observe([{...a,state:'waiting_user_answer'}]).length,1);
c.invalidate();assert.equal(c.badgeCount(),0);assert.equal(c.observe([{...a,state:'waiting_user_answer'}]).length,0,'断连恢复旧 ID 不补发');assert.equal(c.badgeCount(),1);
assert.equal(c.observe([{...a,question_id:'q-review02-96',state:'waiting_user_answer'}]).length,1);
assert.equal(c.observe([]).length,0,'取消或会话移除后清除');
assert.equal(c.observe([{...a,question_id:'q-review02-97',state:'waiting_user_answer'}]).length,1);
assert.equal(c.observe([{...a,question_id:'q-review02-97',state:'ended'}]).length,0);
c.setting(false);assert.equal(c.observe([{...a,question_id:'q-disabled-98',state:'waiting_user_answer'}]).length,0);
c.setting(true);assert.equal(c.observe([{...a,question_id:'q-disabled-98',state:'waiting_user_answer'}]).length,0);
c.setting(false,'dockBadges');assert.equal(c.badgeCount(),0);c.setting(true,'dockBadges');assert.equal(c.badgeCount(),1);
console.log(JSON.stringify({status:'PASS',checks:['非等待用户状态静默','新 ID 与来源','重复读取单条','失效清零且恢复不补发','移除与结束清除','关闭后不补发','Dock 独立开关']}));
''',encoding='utf-8')
    p=run(['node',oracle,center,root],'independent-sequences');assert p.returncode==0,p.stderr
    report['independent_sequences']=json.loads(p.stdout)
    # 将合同产生的夹具限定在本次私有根目录；保留所有断言。
    for name in ['test_t108_questions.mjs','test_t107_sidebar.mjs','t108_hook_failure_contracts.mjs','t108_answer_lifecycle_contracts.mjs']:
        path=copy/'workbench/tests'/name
        path.write_text(path.read_text(encoding='utf-8').replace('/private/tmp/t108-',str(root)+'/t108-').replace('/private/tmp/t107-projection-',str(root)+'/t107-projection-'),encoding='utf-8')
    shutil.copytree(repo/'workbench/node_modules',copy/'workbench/node_modules',symlinks=False)
    for name in ['test_t108_questions.mjs','test_t107_sidebar.mjs','test_t110_window_sequence.mjs','test_t110_reconnect_view.mjs','test_t110_snapshot.mjs','test_t110_cleanup.py']:
        p,v=contract(name);assert p.returncode==0 and v['status']=='PASS',v
    # 自行检索生产路径：记录完整命令、退出码与输出。
    for label,pattern in [
      ('system-notification-api',r'new\s+(window\.)?Notification\b|Notification\.(isSupported|requestPermission)|\bNotification\s*[,}]|requestAuthorization|NSUserNotificationCenter|UNUserNotificationCenter|showNotification|registerForAPNSNotifications'),
      ('notification-and-permission-references',r'setPermissionRequestHandler|setPermissionCheckHandler|pushNotifications|setBadge|Notification')]:
        p=run(['rg','-n',pattern,copy/'workbench/app',copy/'workbench/src',copy/'workbench/hooks'],label)
        assert p.returncode== (1 if label=='system-notification-api' else 0)
    p=run(['git','diff','--check','e3102389e',revision],'diff-check');assert p.returncode==0
    p=run(['python3','/Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py','--cwd',repo,'--format','json'],'structural-locator');assert p.returncode==0
    # 外跑原件逐文件绑定。比较原文，不计算摘要或校验值。
    report['controller_evidence']=[]
    for name in ['/private/tmp/t110-outside-08.json','/private/tmp/t110-receipt-compare-01.json']:
        value=json.loads(Path(name).read_text(encoding='utf-8'))
        original_root=Path(value['fixture'])/'candidate'; equal=[];different=[];missing=[]
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'workbench'],cwd=repo,env=env,text=True).splitlines()
        for path in paths:
            if not path.startswith(('workbench/app/','workbench/src/','workbench/tests/')):continue
            file=original_root/path
            if not file.is_file():missing.append(path);continue
            raw=subprocess.check_output(['git','show',revision+':'+path],cwd=repo,env=env)
            (equal if file.read_bytes()==raw else different).append(path)
        report['controller_evidence'].append(dict(path=name,result=value,equal=equal,different=different,missing=missing))
        assert value['status']=='PASS'
        if name.endswith('outside-08.json'):assert value['source_head']==revision and not different and not missing
    if not local:
        helper=copy/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper';helper.chmod(0o755)
        dist=Path(os.environ.get('T110_ELECTRON_DIST','/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist')).resolve()
        assert not str(dist).startswith('/Volumes/')
        fixtures=root/'fixtures';fixtures.mkdir()
        # 先好候选，再两个单处错误。错误必须命中业务断言且清理无错误。
        for label,case,disabled in [('electron-green',None,False),('electron-disabled',None,True),
                                    ('electron-sticky',cases[1],False),('electron-switch',cases[2],True)]:
            center.write_text(original if case is None else original.replace(case[1],case[2]),encoding='utf-8')
            # 清除同问题去重对 sticky 的遮挡：只在该场景省略断连段，实际作答入口不变。
            scenario=copy/'workbench/tests/t110_notifications_scenario.py'; scenario_original=scenario.read_text(encoding='utf-8')
            if label=='electron-sticky':
                start=scenario_original.index("    window.call('refresh-list')")
                end=scenario_original.index('\n\ndef after_answer',start)
                scenario.write_text(scenario_original[:start]+scenario_original[end:],encoding='utf-8')
            if label=='electron-switch':
                marker="assert not view['notices'] and view['notice_additions'] == 0, view"
                assert scenario_original.count(marker)==1
                scenario.write_text(scenario_original.replace(marker,"assert not view['notices'] and view['notice_additions'] == 0, 'Disabled notification must stay silent'"),encoding='utf-8')
            target=root/(label+'.json')
            p=run(['/usr/bin/python3','-B',copy/'workbench/tests/run_t108_native_e2e.py','--summary',target,
                   '--electron-dist',dist,'--source-revision',revision,'--fixture-parent',fixtures,'--notifications',
                   *(['--disable-notifications'] if disabled else [])],label,cwd=copy,timeout=240)
            v=json.loads(target.read_text(encoding='utf-8'));report.setdefault('electron',[]).append(dict(label=label,result=v))
            scenario.write_text(scenario_original,encoding='utf-8');center.write_text(original,encoding='utf-8')
            assert not any(v.get(k) for k in ['window_cleanup_error','daemon_cleanup_error','process_cleanup_errors']),v
            if case is None:assert p.returncode==0 and v['status']=='PASS',v
            else:
                expected={'electron-sticky':'Answered question removes notification and waiting highlight',
                          'electron-switch':'Disabled notification must stay silent'}[label]
                rejected=p.returncode==1 and expected in v.get('error','')
                report['electron'][-1]['business_rejected']=rejected;assert rejected,v
    report['status']='PASS'
except Exception as error:report.update(error=str(error),traceback=traceback.format_exc())
finally:
    # 保存显式结果与命令，再只删除本次创建的私有副本。不会扫描/删除其他 /tmp 目录。
    try:shutil.rmtree(root);report['private_copy_removed']=True
    except Exception as error:report.update(status='INCOMPLETE',cleanup_error=str(error))
    with output.open('x',encoding='utf-8') as file:json.dump(report,file,ensure_ascii=False,indent=2);file.write('\n')
    print(json.dumps(dict(status=report['status'],summary=str(output),error=report.get('error')),ensure_ascii=False))
sys.exit(0 if report['status']=='PASS' else 1)
PY
