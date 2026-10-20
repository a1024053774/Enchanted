#!/bin/zsh
# T-110 第一轮独立审查。默认运行真实 Electron；--local 只跑无 GUI 合同。
# 所有候选/变异来自冻结提交的 git archive；不改主仓库 Git 元数据，不调用模型。
set -euo pipefail
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
REVIEW_REPO=/Users/luckye/Documents/Code/a2a-wt-t110
cd "$REVIEW_REPO"
/usr/bin/python3 -B - "$REVIEW_REPO" "$@" <<'PY'
import io, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path
repo=Path(sys.argv[1]); argv=sys.argv[2:]; local='--local' in argv
args=[x for x in argv if x!='--local']
output=Path(args[0] if args else '/private/tmp/t110-review-outside-01.json')
assert output.is_absolute() and not output.exists(), '必须使用新的绝对结果路径'
revision='c5ac40c0b4cf60c30407af1a00953a297eb55005'
root=Path(tempfile.mkdtemp(prefix='t110-review-01-',dir='/private/tmp')).resolve()
copy=root/'candidate'; copy.mkdir()
env=dict(os.environ,LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
for key in ['GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE']:env.pop(key,None)
report=dict(status='INCOMPLETE',candidate=revision,mode='local' if local else 'electron',root=str(root),commands=[],model_calls=0,vendor_calls=0,mutations=[])
def run(command, label, cwd=repo, timeout=180):
    p=subprocess.run([str(x) for x in command],cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    item=dict(label=label,argv=[str(x) for x in command],cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
    report['commands'].append(item)
    return p
try:
    archived=subprocess.check_output(['git','archive',revision,'workbench'],cwd=repo,env=env)
    with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
        members=archive.getmembers()
        archive.extractall(copy,members=[m for m in members if not (m.issym() or m.islnk())])
        report['materialized_archive_links']=[]
        for m in members:
            if m.issym() or m.islnk():
                # archive 中已有的 Git hook 链接展开为普通文件，不创建链接。
                destination=copy/m.name
                destination.write_bytes(archive.extractfile(m).read()); destination.chmod(0o755)
                report['materialized_archive_links'].append(m.name)
    ipc=copy/'workbench/tests/test_t091_pane_ipc.mjs'
    center=copy/'workbench/app/notificationCenter.ts'; original=center.read_text(encoding='utf-8')
    def contract(label):
        target=root/(label+'.json')
        p=run(['node','--experimental-vm-modules',ipc,target,'--source',copy],label)
        v=json.loads(target.read_text(encoding='utf-8'))
        report.setdefault('contracts',[]).append(dict(label=label,result=v))
        return p,v
    p,v=contract('candidate-ipc');assert p.returncode==0 and v['status']=='PASS',v
    # 独立故障探针：真实 main/preload，供应的传输边界只注入一次断连。
    ipc_original=ipc.read_text(encoding='utf-8')
    fault=ipc_original.replace("let questionId = 'question-one', focusedWindow = null;", "let questionId = 'question-one', focusedWindow = null, reviewerDisconnected = false;")
    fault=fault.replace("    if (input.command === 'sidebar_snapshot') return", "    if (input.command === 'sidebar_snapshot' && reviewerDisconnected) throw new Error('reviewer-socket-unavailable');\n    if (input.command === 'sidebar_snapshot') return")
    marker="    assert.equal(badgeCalls.at(-1), 1, 'Background Dock badge counts pending user questions');"
    assert fault.count(marker)==1
    fault=fault.replace(marker,marker+"\n    reviewerDisconnected = true;\n    await assert.rejects(() => bridge.sidebar(), /reviewer-socket-unavailable/);\n    assert.equal(badgeCalls.at(-1), 0, 'Disconnected unknown state must clear Dock badge');\n    reviewerDisconnected = false;")
    ipc.write_text(fault,encoding='utf-8')
    p,v=contract('disconnect-probe')
    report['disconnect_probe']=dict(exit=p.returncode,error=v.get('error'),stack=v.get('stack'),business_failure=p.returncode!=0 and 'Disconnected unknown state must clear Dock badge' in v.get('error',''))
    ipc.write_text(ipc_original,encoding='utf-8')
    # 三个独立单处错误；每次从原文开始，业务断言才算拒绝。
    cases=[
      ('unknown-notifies',"agent.state === 'waiting_user_answer' && agent.question_id","['waiting_user_answer', 'unknown'].includes(agent.state) && agent.question_id",'test_t091_pane_ipc.mjs:322:'),
      ('answer-keeps-notice','if (!pending.has(id)) this.active.delete(id);','if (false) this.active.delete(id);','Other states do not notify'),
      ('switch-ignored','const enabled = this.setting();','const enabled = true;','Enabling while already waiting is not a new question')]
    for label,old,new,expected in cases:
        assert original.count(old)==1
        center.write_text(original.replace(old,new),encoding='utf-8')
        p,v=contract(label)
        rejected=p.returncode!=0 and expected in (v.get('error','')+'\n'+v.get('stack',''))
        report['mutations'].append(dict(label=label,file='workbench/app/notificationCenter.ts',old=old,new=new,expected=expected,business_rejected=rejected,exit=p.returncode,error=v.get('error')))
        assert rejected,v
        center.write_text(original,encoding='utf-8')
    # 独立输入序列：未知/权限等待/普通状态、取消/结束、同 ID 回放、不同 ID、持久设置。
    oracle=root/'independent.mjs'
    oracle.write_text('''import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const {NotificationCenter}=await import(pathToFileURL(process.argv[2]));
const c=new NotificationCenter(mkdtempSync(process.argv[3]+'/settings-'));
const a={id:'reviewer-session-73',project:'项目乙',role_label:'构思主控',task:'task-47',question_id:'q-unseen-73'};
for(const state of ['unknown','permission','running','idle','waiting_controller_answer','ended'])assert.equal(c.observe([{...a,state}]).length,0,state+'不提醒');
assert.deepEqual(c.observe([{...a,state:'waiting_user_answer'}]).map(n=>[n.id,n.launch,n.project]),[['q-unseen-73','reviewer-session-73','项目乙']]);
for(let i=0;i<4;i++)assert.equal(c.observe([{...a,state:'waiting_user_answer'}]).length,1);
assert.equal(c.observe([]).length,0,'取消或会话移除后清除');
assert.equal(c.observe([{...a,state:'waiting_user_answer'}]).length,0,'重连后旧 ID 不重放');
assert.equal(c.observe([{...a,question_id:'q-next-74',state:'waiting_user_answer'}]).length,1);
assert.equal(c.observe([{...a,question_id:'q-next-74',state:'ended'}]).length,0,'结束后清除');
c.setting(false);assert.equal(c.observe([{...a,question_id:'q-disabled-75',state:'waiting_user_answer'}]).length,0);
c.setting(true);assert.equal(c.observe([{...a,question_id:'q-disabled-75',state:'waiting_user_answer'}]).length,0);
c.setting(false,'dockBadges');assert.equal(c.badgeCount(),0);c.setting(true,'dockBadges');assert.equal(c.badgeCount(),1);
console.log(JSON.stringify({status:'PASS',checks:['未知和权限等待不提醒','新 ID 和来源正确','重复读取单条','移除与结束清除','旧 ID 回放不重放','关闭后不补发','独立 Dock 设置']}));
''',encoding='utf-8')
    p=run(['node',oracle,center,root],'independent-sequences');assert p.returncode==0,p.stderr
    report['independent_sequences']=json.loads(p.stdout)
    # 将合同的临时夹具限定在本脚本私有根目录；只换路径，不改断言。
    report['fixture_path_redirects']=[]
    for name in ['test_t108_questions.mjs','test_t107_sidebar.mjs','t108_hook_failure_contracts.mjs','t108_answer_lifecycle_contracts.mjs']:
        fixture_file=copy/'workbench/tests'/name
        text=fixture_file.read_text(encoding='utf-8').replace('/private/tmp/t108-',str(root)+'/t108-').replace('/private/tmp/t107-projection-',str(root)+'/t107-projection-')
        fixture_file.write_text(text,encoding='utf-8');report['fixture_path_redirects'].append(name)
    shutil.copytree(repo/'workbench/node_modules',copy/'workbench/node_modules',symlinks=False)
    for name in ['test_t108_questions.mjs','test_t107_sidebar.mjs']:
        target=root/(name+'.json');p=run(['node',copy/'workbench/tests'/name,target],name)
        v=json.loads(target.read_text(encoding='utf-8'))
        report.setdefault('regressions',[]).append(dict(test=name,result=v));assert p.returncode==0 and v['status']=='PASS',v
    if not local:
        # 只复制依赖，不建链接；spawn-helper 执行位仅在私有副本修改。
        native_runner=copy/'workbench/tests/run_t108_native_e2e.py'
        native_runner.write_text(native_runner.read_text(encoding='utf-8').replace("dir='/private/tmp'",'dir='+repr(str(root))),encoding='utf-8')
        helper=copy/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper';helper.chmod(0o755)
        dist=Path(os.environ.get('T110_ELECTRON_DIST','/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist')).resolve()
        assert not str(dist).startswith('/Volumes/'), 'Electron 必须位于内置盘'
        driver=copy/'workbench/tests/t108_questions_driver.mjs'
        driver_text=driver.read_text(encoding='utf-8').replace("readFileSync, appendFileSync", "readFileSync, appendFileSync, renameSync, existsSync")
        driver_marker="      else if(request.command==='background')"
        assert driver_text.count(driver_marker)==1
        driver_text=driver_text.replace(driver_marker,"      else if(request.command==='reload-window'){await new Promise(resolve=>{window.webContents.once('did-finish-load',resolve);window.webContents.reload();});value=true;}\n      else if(request.command==='refresh-list')value=await window.webContents.executeJavaScript(\"(()=>{[...document.querySelectorAll('button')].find(n=>n.textContent==='刷新列表').click();return true;})()\");\n      else if(request.command==='disconnect-sidebar'){renameSync(join(values.state,'control.sock'),join(values.state,'control.sock.review-off'));value=true;}\n      else if(request.command==='reconnect-sidebar'){if(existsSync(join(values.state,'control.sock.review-off')))renameSync(join(values.state,'control.sock.review-off'),join(values.state,'control.sock'));value=true;}\n"+driver_marker)
        driver.write_text(driver_text,encoding='utf-8')
        scenario=copy/'workbench/tests/t110_notifications_scenario.py';scenario_original=scenario.read_text(encoding='utf-8')
        probe_append="""
    # 私有 socket 暂时改名；只断开本次夹具的连接，daemon/原生会话仍存活。
    window.call('background')
    window.wait(lambda v: v['badge'] == 1, 'Probe starts with verified waiting badge')
    window.call('disconnect-sidebar')
    try:
        disconnected=window.wait(lambda v: not v['notices'] and v['agents'] and all(a['state']=='unknown' for a in v['agents']), 'Disconnected sidebar becomes unknown')
        report['reviewer_disconnect_observation']={'badge':disconnected['badge'],'notices':disconnected['notices'],'agents':disconnected['agents']}
        assert disconnected['badge']==0, 'Disconnected unknown state must clear Dock badge'
    finally:
        window.call('reconnect-sidebar')
        window.call('foreground')
    recovered=window.wait(lambda v: any(a['state']=='waiting_user_answer' for a in v['agents']), 'Same native question after reconnect')
    assert recovered['notices']==[], 'Same question must not remind again after reconnect'
    report['checks'].append('reviewer_unknown_clears_badge_and_reconnect_does_not_repeat')
"""
        refresh_append="""
    window.call('refresh-list')
    time.sleep(3.2)
    refreshed=window.call('inspect')
    assert len(refreshed['notices'])==1 and refreshed['notices'][0]['id']==notice['id'] and refreshed['notice_additions']==1, 'List refresh must not add another reminder'
    window.call('reload-window')
    reloaded=window.wait(lambda v: len(v['notices'])==1 and v['notices'][0]['id']==notice['id'], 'Reload preserves one pending question entry')
    window.call('watch-notices')
    time.sleep(6.2)
    stable=window.call('inspect')
    assert len(stable['notices'])==1 and stable['notice_additions']==0, 'Re-render after reload must not append reminders'
    report['checks'].append('reviewer_list_refresh_renderer_reload_and_rerender_keep_one_question')
"""
        # 真实候选先跑绿态；再验证单处变异与额外断连场景。
        for label,disabled,mutant in [('electron-green',False,False),('electron-disabled',True,False),('electron-answer-keeps-notice',False,True),('electron-disconnect-probe',False,False)]:
            center.write_text(original.replace(cases[1][1],cases[1][2]) if mutant else original,encoding='utf-8')
            if label=='electron-disconnect-probe':
                boundary='\n\ndef after_answer'
                assert scenario_original.count(boundary)==1
                scenario.write_text(scenario_original.replace(boundary,'\n'+probe_append+boundary),encoding='utf-8')
            elif label=='electron-green':
                scenario.write_text(scenario_original.replace('\n\ndef after_answer','\n'+refresh_append+'\n\ndef after_answer'),encoding='utf-8')
            else:scenario.write_text(scenario_original,encoding='utf-8')
            target=root/(label+'.json')
            command=['/usr/bin/python3','-B',copy/'workbench/tests/run_t108_native_e2e.py','--summary',target,'--electron-dist',dist,'--source-revision',revision,'--notifications']+(['--disable-notifications'] if disabled else [])
            p=run(command,label,cwd=copy,timeout=240)
            if target.exists():
                v=json.loads(target.read_text(encoding='utf-8'));report.setdefault('electron',[]).append(dict(label=label,result=v))
            else:raise AssertionError('真实入口没有结果 JSON：'+p.stderr)
            if label=='electron-disconnect-probe':
                report['electron_disconnect_probe']=dict(exit=p.returncode,error=v.get('error'),observation=v.get('reviewer_disconnect_observation'),business_failure=p.returncode!=0 and 'Disconnected unknown state must clear Dock badge' in v.get('error',''))
                assert p.returncode==0 and v['status']=='PASS' or report['electron_disconnect_probe']['business_failure'],v
                assert not any(v.get(k) for k in ['window_cleanup_error','daemon_cleanup_error','process_cleanup_errors']),v
            elif mutant:
                assert p.returncode!=0 and 'Answered question removes notification and waiting highlight' in v.get('error',''),v
                assert not any(v.get(k) for k in ['window_cleanup_error','daemon_cleanup_error','process_cleanup_errors']),v
                report['electron_mutation_business_rejected']=True
            else:assert p.returncode==0 and v['status']=='PASS',v
            center.write_text(original,encoding='utf-8')
    report['product_status']='NO_GO' if report['disconnect_probe']['business_failure'] else ('INCOMPLETE' if local else 'PASS')
    report['status']='PASS' # 审查脚本执行完成；产品结论另见 product_status 与各业务断言。
except Exception as error:report.update(error=str(error),traceback=traceback.format_exc())
finally:
    # 仅删除本脚本创建的私有副本；各 JSON 内容先归入总结果，失败也不覆盖。
    for path in report.get('native_fixture_paths',[]):
        if Path(path).exists():shutil.rmtree(path)
    report['cleanup']='只清理本次私有副本与夹具；结果保存在指定 JSON'
    shutil.rmtree(root)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],summary=str(output),error=report.get('error')),ensure_ascii=False))
sys.exit(0 if report['status']=='PASS' else 1)
PY
