#!/bin/sh
# T-096 独立审查的可复现合同探针；无需外部权限或逐屏批准。
# 不启动 Electron、daemon、PTY、供应商 CLI 或模型，不改候选或全局配置。
# 每次用 git archive 在 /tmp 新建副本；保留全部日志、变异源码和失败结果。
# 结合 results.json 判读：汇总 NO_GO 时退出 1；不能仅按退出码认定反例。
set -eu
REVIEW_REPO="${1:-/Users/luckye/Documents/Code/a2a-wt-t096}"
python3 - "$REVIEW_REPO" <<'PY'
from pathlib import Path
import io, json, subprocess, sys, tarfile, tempfile
repo=Path(sys.argv[1]).resolve()
candidate='11b32303bebf276d20026a6e718719d15f5d4068'
root=Path(tempfile.mkdtemp(prefix='t096-independent-replay-',dir='/tmp'))
print('证据目录：'+str(root),flush=True)
archive=subprocess.check_output(['git','-C',str(repo),'archive',candidate,'workbench'])
with tarfile.open(fileobj=io.BytesIO(archive)) as stream: stream.extractall(root)
deps=repo/'workbench/node_modules'
if not deps.is_dir(): raise SystemExit('INCOMPLETE：缺少已有依赖；本脚本不安装依赖。')
(root/'workbench/node_modules').symlink_to(deps,target_is_directory=True)
results={'candidate':candidate,'directory':str(root),'scope':'真实模块和 SQLite；替代进程、PTY、Electron、transport 边界'}
def run(label,test):
    out=root/(label+'.json')
    cmd=['node','--experimental-vm-modules',str(root/'workbench/tests'/test),str(out)]
    p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
    (root/(label+'.stdout.txt')).write_text(p.stdout,encoding='utf-8')
    (root/(label+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    return {'command':cmd,'exit':p.returncode,'result':json.loads(out.read_text(encoding='utf-8')) if out.exists() else None}
def rejected(result,message):
    return result['exit']==1 and result['result'] and result['result'].get('error','').startswith('AssertionError [ERR_ASSERTION]: '+message)
for label,test in [('restore','test_t096_restore.mjs'),('ipc','test_t091_pane_ipc.mjs'),('transport','test_t096_daemon_restart.mjs')]:
    results[label]=run(label,test)
    if results[label]['exit']!=0:
        (root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        raise SystemExit('INCOMPLETE：候选基线未通过；保留原件。')
# 独立 sentinel 约束实际交给 PTY 的命令，防止事件正确、启动参数错误。
test=root/'workbench/tests/test_t096_restore.mjs'
text=test.read_text(encoding='utf-8')
needle="      assert.deepEqual(event.data.argv, expected.get(record.id), 'Every resume argv token must equal the independently specified input');"
extra="""
      const spawned = starts.find(start => start.args[3].includes(record.session));
      assert.ok(spawned && spawned.args[3].includes("'--model' 'sentinel-" + label + "'") && spawned.args[3].includes("'--effort' 'low'"), 'Actual PTY command must carry the supplied model and effort sentinel');
"""
assert text.count(needle)==1
(root/'workbench/tests/review_spawn_argv.mjs').write_text(text.replace(needle,needle+extra),encoding='utf-8')
results['independent-baseline']=run('independent-baseline','review_spawn_argv.mjs')
if results['independent-baseline']['exit']!=0: raise SystemExit('INCOMPLETE：独立断言的候选基线未通过。')
source=root/'workbench/src/panes.ts';original=source.read_text(encoding='utf-8')
mutants={
    'm1-ignore-spawn-argv':('const shellArgv = ["-f", "-i", "-c", shellCommand(argv)', 'const shellArgv = ["-f", "-i", "-c", shellCommand([argv[0]!, "--resume", opened.native_session!])'),
    'm2-failed-recorded-restored':('this.store.event("pane_restore_failed", { daemon, error:', 'this.store.event("pane_restored", { daemon, error:'),
    'm3-worker-attempt-mutated':('async recover(daemon: string) {', 'async recover(daemon: string) {\n    this.store.db.exec(`UPDATE tasks SET data=json_set(data,\'$.current_attempt.state\',\'ready\')`);'),
}
try:
    for label,(old,new) in mutants.items():
        assert old in original
        changed=original.replace(old,new,1)
        (root/(label+'.panes.ts')).write_text(changed,encoding='utf-8')
        source.write_text(changed,encoding='utf-8')
        results[label]={'existing':run(label+'-existing','test_t096_restore.mjs'),'independent':run(label+'-independent','review_spawn_argv.mjs')}
finally: source.write_text(original,encoding='utf-8')
# 使用真实 main/preload；默认 snapshot 的当前 worker 由 daemon.ts:253 的规则提供。
text=(root/'workbench/tests/test_t091_pane_ipc.mjs').read_text(encoding='utf-8').replace('...records[input.launch]', "...records[input.launch ?? 'worker']")
needle="    assert.equal(snapshots[1].window_id, undefined, 'Unrestored worker gets no input credential');"
extra="""
    for (const k of keys) await invoke(restored, 'a2a:close-pane', k);
    assert.equal(layout.size, 0);
    restorations.delete('worker');
    const sole = await run({ ...options, launch: 'worker' });
    await invoke(sole, 'a2a:snapshot', key(sole));
    await invoke(sole, 'a2a:close-pane', key(sole));
    assert.equal(layout.size, 0, 'All explicit pane closes persisted an empty set');
    sole.close();
    const reopened = await run(options);
    await invoke(reopened, 'a2a:snapshot', key(reopened));
    assert.equal(layout.size, 0, 'Explicitly closed final pane must stay absent when app reopens');
"""
assert text.count(needle)==1
(root/'workbench/tests/review_empty_layout.mjs').write_text(text.replace(needle,needle+extra),encoding='utf-8')
results['empty-layout']=run('empty-layout','review_empty_layout.mjs')
expected=[('m1-ignore-spawn-argv','Actual PTY command must carry the supplied model and effort sentinel'),('m2-failed-recorded-restored','A failed pane must not have a success receipt'),('m3-worker-attempt-mutated','Worker attempt must remain byte-for-byte unchanged')]
results['all_mutants_rejected']=all(rejected(results[k]['independent'],m) for k,m in expected)
results['empty_layout_defect_reproduced']=rejected(results['empty-layout'],'Explicitly closed final pane must stay absent when app reopens')
results['status']='NO_GO' if results['all_mutants_rejected'] and results['empty_layout_defect_reproduced'] else 'INCOMPLETE'
(root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(results['status']+'；结果：'+str(root/'results.json'))
sys.exit(1 if results['status']=='NO_GO' else 2)
PY
