#!/bin/zsh
# T-112 第一轮独立审查复验；默认合同与变异，传 --native 加跑真实 CLI/Electron。
# 所有副本和输出均在 /private/tmp；源码和 Git 元数据只读，不调用模型。
set -euo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
TASK_SOURCE=${T112_SOURCE:-/Users/luckye/Documents/Code/a2a-wt-t112}
TASK_ELECTRON_DIST=${T112_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
TASK_MODE=${1:---contracts}
python3 -B - "$TASK_SOURCE" "$TASK_ELECTRON_DIST" "$TASK_MODE" <<'PY_REVIEW'
import io, json, os, posixpath, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path, PurePosixPath
source, dist, mode = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
assert mode in ('--contracts', '--native')
candidate = '4bdf0721c5f80fa848d07500ec60327723eac898'
root = Path(tempfile.mkdtemp(prefix='t112-review-01-', dir='/private/tmp'))
results = root / 'results'; results.mkdir()
env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
for key in list(env):
    if key.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_')) and key != 'GIT_OPTIONAL_LOCKS':
        env.pop(key)
report = dict(status='INCOMPLETE', candidate=candidate, source=str(source), mode=mode, commands=[], model_calls=0)

def run(argv, label, exits=(0,), timeout=240):
    p = subprocess.run(list(map(str, argv)), cwd=source, env=env, capture_output=True, text=True, timeout=timeout)
    (results / (label + '.stdout.txt')).write_text(p.stdout, encoding='utf-8')
    (results / (label + '.stderr.txt')).write_text(p.stderr, encoding='utf-8')
    report['commands'].append(dict(label=label, argv=list(map(str, argv)), exit=p.returncode))
    assert p.returncode in exits, (label, p.returncode, p.stderr[-1500:], p.stdout[-1500:])
    return p

def materialize(archive, destination):
    # Git 原有的内部 hook 链接复制为普通文件；不创建符号链接或 worktree。
    assert not destination.exists()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = {m.name: m for m in tar.getmembers()}
        def content(name, seen=()):
            assert name not in seen and name in members
            m = members[name]
            if m.isfile(): return m, tar.extractfile(m).read()
            assert m.issym() or m.islnk()
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), m.linkname) if m.issym() else m.linkname)
            assert not target.startswith('/') and '..' not in PurePosixPath(target).parts
            return content(target, seen + (name,))
        destination.mkdir(parents=True)
        for name, m in members.items():
            assert not name.startswith('/') and '..' not in PurePosixPath(name).parts
            p = destination / name
            if m.isdir(): p.mkdir(parents=True, exist_ok=True)
            else:
                original, data = content(name)
                p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); p.chmod(original.mode & 0o777)

PROBE_TEXT = r"""
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const tree=process.argv[2], output=process.argv[3];
const source=pathToFileURL(tree+'/workbench/');
const {OrchestrationStore}=await import(new URL('src/store.ts',source));
const {Panes}=await import(new URL('src/panes.ts',source));
const require=createRequire(new URL('src/panes.ts',source)), pty=require('node-pty');
const prior=pty.spawn;
pty.spawn=()=>({pid:99999,onData(){},onExit(){},write(){}});
const root=mkdtempSync('/private/tmp/t112-independent-security-');
const report={status:'INCOMPLETE',scope:'SQLite/Panes and exact shell argv with private capture executable; no native sandbox claim',checks:[],model_calls:0};
let store;
try {
  store=new OrchestrationStore(root);
  const known={model:'gpt-6.1-sol',effort:'high',fast:false};
  assert.deepEqual(store.executionSelection('worker'),known);
  store.saveExecutionSettings('worker',{model:'saved-unique-model',effort:'medium',fast:true});
  assert.deepEqual(store.executionSelection('worker',{model:'override-unique-model',effort:'ultra-review-819',fast:false}),
    {model:'override-unique-model',effort:'ultra-review-819',fast:false},'覆盖参数优先于设置');
  report.checks.push('independent_override_priority');
  for(const key of ['sandbox_mode','sandbox_workspace_write.network_access','sandbox_workspace_write.writable_roots','hooks.Stop','approval_policy','approval','__proto__','constructor']) {
    const selection=JSON.parse(JSON.stringify({model:'ordinary',effort:'low',fast:false}) .slice(0,-1)+','+JSON.stringify(key)+':"danger-full-access"}');
    assert.throws(()=>store.saveExecutionSettings('reviewer',selection),undefined,'权限键应拒绝：'+key);
    assert.throws(()=>store.executionSelection('reviewer',selection),undefined,'覆盖权限键应拒绝：'+key);
  }
  report.checks.push('eight_permission_keys_rejected_in_save_and_override');
  const bin=join(root,'capture-cli');
  writeFileSync(bin,'#!/usr/bin/python3\nimport sys,json,os\nif sys.argv[1:]==["--version"]: print("codex-cli 0.162.1"); sys.exit(0)\nopen(os.environ["CODEX_HOME"]+"/captured.json","w").write(json.dumps(sys.argv[1:]))\nsys.exit(29)\n',{mode:0o755});
  mkdirSync(join(root,'candidate'));
  mkdirSync(join(root,'worker-home'));
  const task={task_id:'independent',project_id:'review',spec_rev:1,card:{executor:{cli:'Codex',model:'old-card',effort:'xhigh'}}};
  const attacks=['normal-future-819','" -c sandbox_mode="danger-full-access"','low\\"; touch '+root+'/escaped; #',
    "$(touch "+root+"/escaped) '` -c hooks.Stop=[]",'--dangerously-bypass-approvals-and-sandbox','low\t-c\tapproval_policy=on-request'];
  for(let i=0;i<attacks.length;i++) {
    const payload=attacks[i],home=join(root,'home'+i);mkdirSync(home);
    store.saveExecutionSettings('reviewer',{model:payload,effort:payload,fast:i%2===1});
    const config={codex_bin:bin,codex_home:join(root,'worker-home'),role_card:bin,role_card_revision:'review-01',code_revision:'4bdf0721c',hook_authorization:'local capture only',turn_limit:1,
      reviewers:Array(20).fill({codex_home:home,role_card:bin,role_card_revision:'review-01',hook_authorization:'local capture only'})};
    const panes=new Panes(root,store,config,()=>{});
    const attempt={runtime_mode:'workspace-write',workspace:root,attempt_id:'a1',session_id:'session'+i,thread_id:'worker'+i,fence:1,spec_rev:1};
    await panes.createReview(task,{attempt,thread_id:'review'+i,session_id:'review-session'+i,candidate_workspace:join(root,'candidate'),workspace:root,review_id:'r'+i,verification_id:'v'+i},'local fixture');
    const r=store.threadLaunch('review'+i),a=r.argv;
    assert.equal(r.model_requested,payload,'模型原样记录');assert.equal(r.effort_requested,payload,'未知强度原样记录');
    assert.equal(a[a.indexOf('-m')+1],payload);assert.ok(a.includes('model_reasoning_effort='+JSON.stringify(payload)),'未知强度原样 argv');
    assert.equal(a[a.indexOf('--sandbox')+1],'workspace-write','reviewer 沙箱不得随设置改变');
    assert.equal(a[a.indexOf('-a')+1],'never');assert.equal(a[a.indexOf('-C')+1],join(root,'candidate'));
    for(const value of ['sandbox_workspace_write.network_access=false','features.network_proxy=false','sandbox_workspace_write.exclude_slash_tmp=true','sandbox_workspace_write.exclude_tmpdir_env_var=true']) assert.ok(a.includes(value));
    assert.equal(a.filter(v=>v.startsWith('hooks.')).length,5);
    // A payload can equal a flag as model data. Inspect config-key positions.
    const keys=a.flatMap((v,j)=>v==='-c'?[a[j+1].split('=')[0]]:[]);
    assert.deepEqual(keys,['model_reasoning_effort','service_tier','check_for_update_on_startup','tui.notifications',
      'sandbox_workspace_write.network_access','features.network_proxy','sandbox_workspace_write.exclude_slash_tmp',
      'sandbox_workspace_write.exclude_tmpdir_env_var','hooks.UserPromptSubmit','hooks.Stop','hooks.PermissionRequest','hooks.PreToolUse','hooks.PostToolUse']);
    const operation=spawnSync(r.shell,r.shell_argv,{cwd:root,env:{...r.env,HOME:root},encoding:'utf8',input:'',timeout:5000});
    assert.equal(operation.status,29,'原始 shell 必须保留子进程退出码');
    const captured=JSON.parse(readFileSync(join(home,'captured.json'),'utf8'));
    assert.deepEqual(captured,a.slice(1),'shell 不得拆分、执行或改写设置值');
    const {existsSync}=await import('node:fs'); assert.equal(existsSync(join(root,'escaped')),false);
    report.checks.push('reviewer_payload_'+i+'_exact_argv_and_fixed_permissions');
  }
  report.status='PASS';
} catch(error){report.error=String(error);report.stack=error.stack;}
finally {
  const requests=store?.launches().map(r=>r.request_dir).filter(Boolean)??[];
  store?.close();pty.spawn=prior;
  for(const p of requests)rmSync(p,{recursive:true});
  rmSync(root,{recursive:true});
}
writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;
"""

private = root / 'candidate'
try:
    assert run(['git', 'rev-parse', 'HEAD'], 'head').stdout.strip() == candidate, '候选改变，应重新派审'
    archive = subprocess.check_output(['git', 'archive', candidate, 'workbench/src', 'workbench/app', 'workbench/tests', 'workbench/package.json', 'workbench/LICENSE.synara'], cwd=source, env=env)
    materialize(archive, private)
    for name in ('effect', 'fast-check', 'pure-rand', 'node-pty'):
        shutil.copytree(source / 'workbench/node_modules' / name, root / 'node_modules' / name,
                        symlinks=False, ignore=shutil.ignore_patterns('win32-*', 'linux-*', '.bin'))
    (root / 'node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
    probe = root / 'security.mjs'
    probe.write_text(PROBE_TEXT, encoding='utf-8')
    run(['node', probe, private, results / 'security-good.json'], 'security-good')
    run(['node', private / 'workbench/tests/test_t112_execution.mjs', results / 'execution.json'], 'execution')
    run(['node', '--experimental-vm-modules', private / 'workbench/tests/test_t091_pane_ipc.mjs', results / 'ipc.json', '--source', private], 'ipc')
    run(['node', private / 'workbench/tests/test_t108_questions.mjs', results / 't108.json'], 't108')
    mutations = [
        ('saved_beats_override', 'store.ts', '...factoryExecution[role], ...saved, ...executionOverrides(overrides)',
         '...factoryExecution[role], ...executionOverrides(overrides), ...saved', '覆盖参数优先于设置'),
        ('reviewer_sandbox_disabled', 'panes.ts', 'const sandboxMode = "workspace-write";',
         'const sandboxMode = "danger-full-access";', 'reviewer 沙箱不得随设置改变'),
        ('unknown_effort_coerced', 'panes.ts', '`model_reasoning_effort=${JSON.stringify(effort)}`',
         '`model_reasoning_effort=${JSON.stringify("high")}`', '未知强度原样 argv'),
    ]
    report['mutations'] = []
    for name, filename, old, new, signal in mutations:
        tree = root / name
        shutil.copytree(private / 'workbench/src', tree / 'workbench/src')
        path = tree / 'workbench/src' / filename
        text = path.read_text(encoding='utf-8'); assert text.count(old) == 1
        path.write_text(text.replace(old, new), encoding='utf-8')
        p = run(['node', probe, tree, results / (name + '.json')], name, exits=(1,))
        row = json.loads((results / (name + '.json')).read_text(encoding='utf-8'))
        assert signal in row.get('error', ''), row
        report['mutations'].append(dict(name=name, file=filename, old=old, new=new, rejected=True, error=row['error']))
    if mode == '--native':
        # 仅在原生沙箱外执行；使用内置盘 Electron 和无凭据 loopback API。
        # 复用已审查的真实入口 runner；只改变 Git 夹具链接的落盘形式。
        assert not str(dist).startswith('/Volumes/')
        sys.path.insert(0, str(source / 'workbench/tests'))
        import run_t112_native as native
        native.extract_baseline = materialize
        sys.argv = ['run_t112_native.py', '--source', str(source), '--electron-dist', str(dist), '--summary', str(results / 'native.json')]
        assert native.main() == 0
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = str(error)
finally:
    # 保留文本和错误；清理本次产生的 SQLite、依赖及候选副本。
    t108 = results / 't108.json'
    if t108.exists():
        data = json.loads(t108.read_text(encoding='utf-8'))
        fixtures = [data.get('retained_fixture')] + [r.get('fixture') for k in ('failure_cases', 'answer_lifecycle_cases') for r in data.get(k, [])]
        for item in fixtures:
            if item and str(item).startswith('/private/tmp/t108-'):
                shutil.rmtree(item)
    for child in root.iterdir():
        if child.is_dir() and child != results:
            shutil.rmtree(child)
    (results / 'review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], results=str(results)), ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PY_REVIEW
