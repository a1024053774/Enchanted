#!/bin/sh
# T-096 第二轮独立审查：固定候选的合同回放，不启动真实应用或模型。
# 无需沙箱升级、逐屏批准或安装依赖；所有副本和失败原件仅写 /tmp。
# PASS 仅指列出的合同及变异，不代替外置盘原生实跑原件核对。
set -eu
REVIEW_REPO="${1:-/Users/luckye/Documents/Code/a2a-wt-t096}"
python3 - "$REVIEW_REPO" <<'PYCODE'
from pathlib import Path
import io, json, subprocess, sys, tarfile, tempfile
repo=Path(sys.argv[1]).resolve()
candidate='17a8ec8f20b97b732ad561c4fa02213a4f0e23f7'
root=Path(tempfile.mkdtemp(prefix='t096-review-02-',dir='/tmp'))
print('证据目录：'+str(root),flush=True)
archive=subprocess.check_output(['git','-C',str(repo),'archive',candidate,'workbench'])
with tarfile.open(fileobj=io.BytesIO(archive)) as stream: stream.extractall(root)
deps=repo/'workbench/node_modules'
if not deps.is_dir(): raise SystemExit('INCOMPLETE：缺少已有依赖；不安装。')
(root/'workbench/node_modules').symlink_to(deps,target_is_directory=True)
results={'candidate':candidate,'directory':str(root),'scope':'真实模块及 SQLite，替代进程／PTY／Electron／transport 边界','checks':{}}
def save():
    (root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(label,test,folder=False):
    out=root/(label if folder else label+'.json')
    cmd=['node','--experimental-vm-modules',str(root/'workbench/tests'/test),str(out)]
    p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
    (root/(label+'.stdout.txt')).write_text(p.stdout,encoding='utf-8')
    (root/(label+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    f=out/'results.json' if folder else out
    return {'command':cmd,'exit':p.returncode,'result':json.loads(f.read_text(encoding='utf-8')) if f.exists() else None}
checks=[('restore','test_t096_restore.mjs',False),('ipc','test_t091_pane_ipc.mjs',False),
 ('transport','test_t096_daemon_restart.mjs',False),('version','test_t091_claude_version.mjs',False),
 ('driver','test_t091_driver_selection.mjs',False),('start','test_t091_start.mjs',False),
 ('controller-window','test_t078_controller_window.ts',True),('screen-key','test_t078_screen_key.ts',True)]
for label,test,folder in checks:
    result=run(label,test,folder);results['checks'][label]=result;save()
    if result['exit']!=0 or not result['result'] or result['result']['status']!='PASS':
        raise SystemExit('INCOMPLETE：候选合同基线未通过，保留现场。')
# 复用已审查的夹具边界与业务断言，替换外部 sentinel，并去掉其内部变异调度。
# 答案依据裁定 B：精确保留输入参数、失败无成功事件、完整 task 不变。
test=root/'workbench/tests/test_t096_restore.mjs'
source=test.read_text(encoding='utf-8')
body=source[:source.index('const report =')]
body=body.replace("'sentinel-' + label", "'review-' + randomUUID() + '-' + label")
body=body.replace("'--effort', 'low'", "'--effort', 'medium'")
body+="const report = { status: 'INCOMPLETE', scope: '独立变异调度；真实 SQLite，替代 PTY／版本／进程边界' };\ntry { report.checks = await exercise(readFileSync(panesURL, 'utf8')); report.status = 'PASS'; }\ncatch (error) { report.error = String(error); report.stack = error.stack; }\nwriteFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\\n', { flag: 'wx' });\nconsole.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;\n"
(root/'workbench/tests/review_02_restore.mjs').write_text(body,encoding='utf-8')
results['independent-baseline']=run('independent-baseline','review_02_restore.mjs');save()
if results['independent-baseline']['exit']!=0: raise SystemExit('INCOMPLETE：变异前基线未通过。')
file=root/'workbench/src/panes.ts';original=file.read_text(encoding='utf-8')
mutants={
 'm1-ignore-argv':('const shellArgv = ["-f", "-i", "-c", shellCommand(argv)', 'const shellArgv = ["-f", "-i", "-c", shellCommand([argv[0]!, "--resume", opened.native_session!])', 'Actual PTY command must carry every independently supplied argv field'),
 'm2-failed-as-restored':('this.store.event("pane_restore_failed", { daemon, error:', 'this.store.event("pane_restored", { daemon, error:', 'A failed pane must not have a success receipt'),
 'm3-modify-attempt':('async recover(daemon: string) {', "async recover(daemon: string) {\n    this.store.db.exec(`UPDATE tasks SET data=json_set(data,'$.current_attempt.state','ready')`);", 'Worker attempt must remain byte-for-byte unchanged'),
}
results['mutants']={}
try:
    for label,(old,new,message) in mutants.items():
        assert original.count(old)==(2 if label=='m1-ignore-argv' else 1)
        changed=original.replace(old,new,1)
        (root/(label+'.panes.ts')).write_text(changed,encoding='utf-8')
        file.write_text(changed,encoding='utf-8')
        r=run(label,'review_02_restore.mjs')
        r['business_rejection']=r['exit']==1 and bool(r['result']) and r['result'].get('error','').startswith('AssertionError [ERR_ASSERTION]: '+message)
        results['mutants'][label]=r;save()
finally: file.write_text(original,encoding='utf-8')
results['status']='PASS' if all(r['business_rejection'] for r in results['mutants'].values()) else 'INCOMPLETE'
save();print(results['status']+'；结果：'+str(root/'results.json'))
sys.exit(0 if results['status']=='PASS' else 2)
PYCODE
