#!/bin/bash
# 独立审查复验，只向新建的 /private/tmp 目录写入。
# 用法：bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-01.sh [electron|local]
# 默认 electron，由执行主控在沙箱外运行；不调用模型、不截图、不碰 Herdr。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t107
export LC_ALL=C
export PYTHONDONTWRITEBYTECODE=1
python3 -B - "$PWD" "$@" <<'PY'
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

repo = Path(sys.argv[1])
mode = sys.argv[2] if len(sys.argv) > 2 else "electron"
assert mode in ("electron", "local")
revision = "3c3f2e9e189ddf37eeec4091266c8701a2dde33f"
root = Path(tempfile.mkdtemp(prefix="t107-review-outside-01-", dir="/private/tmp"))
dependencies = Path("/Users/luckye/Documents/Code/a2a/workbench/node_modules")
dist = dependencies / "electron/dist"
env = dict(os.environ, LC_ALL="C", PYTHONDONTWRITEBYTECODE="1")
for key in list(env):
    if key.startswith(("A2A_", "CODEX_", "CLAUDE_", "ANTHROPIC_", "GIT_")):
        env.pop(key, None)
for key in ("NODE_OPTIONS", "ELECTRON_RUN_AS_NODE"):
    env.pop(key, None)
report = dict(candidate=revision, mode=mode, root=str(root), model_calls=0,
              commands=[], mutations=[], status="INCOMPLETE")
print("审查现场：" + str(root), flush=True)

def run(name, argv, expected=0, extra_env=None):
    current = dict(env)
    current.update(extra_env or {})
    value = subprocess.run(list(map(str, argv)), cwd=repo, env=current,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    (root / (name + ".stdout.txt")).write_text(value.stdout, encoding="utf-8")
    (root / (name + ".stderr.txt")).write_text(value.stderr, encoding="utf-8")
    report["commands"].append(dict(name=name, argv=list(map(str, argv)),
                                   exit=value.returncode, expected=expected))
    (root / "review-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(name + " rc=" + str(value.returncode), flush=True)
    assert value.returncode == expected, name + "：查看现场日志"
    return value

archive = subprocess.check_output(["git", "archive", revision, "workbench"], cwd=repo, env=env)
mutations = [
    ("unknown-idle", "  return 'unknown';\n}\n\nexport function aggregate",
     "  return 'idle';\n}\n\nexport function aggregate", "Missing signal must remain unknown"),
    ("title-parent", "parent: senders.size === 1 ? [...senders][0] : null",
     "parent: senders.size === 1 ? [...senders][0] : launches.find(p => p.project === record.project && p.preset === 'executor' && String(record.title ?? 'executor').includes('executor'))?.id ?? null",
     "Role-only parent must be rejected"),
    ("read-write", "  const launches = store.launches()",
     "  store.event('sidebar_read', { source: 'sidebar' });\n  const launches = store.launches()", None),
]
for name in ["candidate"] + [item[0] for item in mutations]:
    tree = root / name
    tree.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree)
    (tree / "workbench/node_modules").symlink_to(dependencies, target_is_directory=True)
for name, old, new, expected_error in mutations:
    path = root / name / "workbench/src/sidebar.ts"
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1
    path.write_text(text.replace(old, new), encoding="utf-8")

candidate = root / "candidate"
run("candidate-projection", ["node", candidate / "workbench/tests/test_t107_sidebar.mjs", root / "candidate-projection.json"])
run("candidate-ipc", ["node", "--experimental-vm-modules", repo / "workbench/tests/test_t091_pane_ipc.mjs",
                      root / "candidate-ipc.json", "--source", candidate])
for name, old, new, expected_error in mutations:
    result_file = root / (name + "-projection.json")
    run(name, ["node", root / name / "workbench/tests/test_t107_sidebar.mjs", result_file], 1 if expected_error else 0)
    observed = json.loads(result_file.read_text(encoding="utf-8"))
    if expected_error:
        assert expected_error in observed.get("error", ""), observed
    else:
        assert observed["status"] == "PASS", observed
    report["mutations"].append(dict(name=name, rejected=bool(expected_error), observed=observed))

# 独立探针：实际 Panes/scan + SQLite，不启动 CLI。
# 预期来自票据：读取零写入；辅助原生会话不能解除根会话问题。
probe = root / "probe.mjs"
probe.write_text(r"""
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync, mkdtempSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
const source=process.argv[2];
const load=p=>import(pathToFileURL(join(source,'workbench/src',p)));
const {sidebarSnapshot,gitFacts}=await load('sidebar.ts');
const {OrchestrationStore}=await load('store.ts');
const {Panes}=await load('panes.ts');
const {RequestRelay}=await load('relay.ts');
const root=mkdtempSync('/private/tmp/t107-review-live-read-');
const home=join(root,'home'),logs=join(home,'sessions');
mkdirSync(logs,{recursive:true});mkdirSync(join(root,'traces','launch'),{recursive:true});
const store=new OrchestrationStore(root);new RequestRelay(store);
const record={id:'launch',thread:'thread',role:'worker',project:'p',task:'t',attempt:'a',
 cli_version:'codex-cli 0.163.0',env:{CODEX_HOME:home}};
store.launch(record);
const panes=new Panes(root,store,{},()=>{});
const pane={record,attempt:{workspace:root},pty:{pid:123},state:'busy',stopped:false,archived:false,
 failed:null,native:'root-session',turn:'root-turn',active:{id:'submission',nativeTurn:'root-turn'},
 queue:[],writing:false,offsets:new Map(),interrupted:false};
panes.panes.set('thread',pane);
const question={type:'response_item',payload:{type:'function_call',name:'request_user_input',call_id:'question-1'}};
writeFileSync(join(logs,'root-session.jsonl'),[
 {type:'session_meta',payload:{source:'cli',cwd:root,id:'root-session'}},question
].map(JSON.stringify).join('\n')+'\n');
const gates={listProjects:()=>[],listTasks:()=>[]};
const count=()=>Number(store.db.prepare('SELECT count(*) AS n FROM orchestration_events').get().n);
const before=count(),waiting=await sidebarSnapshot(gates,store,panes),after=count();
assert.equal(waiting.agents[0].state,'unknown');
writeFileSync(join(logs,'zz-subagent-session.jsonl'),[
 {type:'session_meta',payload:{source:{subagent:{parent_thread_id:'root-session'}},cwd:root,id:'subagent-session'}},
 {type:'event_msg',payload:{type:'task_started',turn_id:'subagent-turn'}}
].map(JSON.stringify).join('\n')+'\n');
const resumed=await sidebarSnapshot(gates,store,panes);
assert.equal(pane.turn,'root-turn');assert.equal(pane.active.nativeTurn,'root-turn');
const badgit=await gitFacts(join(root,'missing-repo'));
assert.equal(badgit.branch,null);assert.equal(badgit.ahead,null);assert.ok(badgit.error.includes('无法读取 Git'));
console.log(JSON.stringify({root,before,after,writes:after-before,waiting:waiting.agents[0].state,
 unrelated_start:resumed.agents[0].state,expected_unrelated_start:'unknown',git_failure:badgit},null,2));
store.close();
""", encoding="utf-8")
result = run("independent-probe", ["node", probe, candidate])
report["probe"] = json.loads(result.stdout)

if mode == "electron":
    # archive 副本不建 worktree。原脚本只读 Git 元数据以提取历史基线。
    # 它给 daemon 与 Git fixture 的环境会剥离 GIT_*。
    git_dir = subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"], cwd=repo, env=env, text=True).strip()
    assert not str(dist.resolve()).startswith("/Volumes/")
    assert (dist / "version").read_text(encoding="utf-8").strip() == "43.4.1"
    for name in ("candidate", "read-write"):
        tree = root / name
        result_file = root / (name + "-electron.json")
        run(name + "-electron", ["python3", "-B", tree / "workbench/tests/run_t107_sidebar.py",
              "--source", tree, "--dependencies", dependencies, "--electron-dist", dist,
              "--summary", result_file], extra_env={"GIT_DIR": git_dir})
        value = json.loads(result_file.read_text(encoding="utf-8"))
        assert value["implemented_slice_status"] == "PASS" and value["status"] == "INCOMPLETE"
        report[name + "_electron"] = value

# 已知缺陷或错误实现逃过检查不能记为 PASS。退出 1 表示审查 NO_GO。
report["status"] = "NO_GO" if (report["probe"]["writes"] or
    report["probe"]["unrelated_start"] != "unknown" or
    any(not row["rejected"] for row in report["mutations"])) else "INCOMPLETE"
(root / "review-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(status=report["status"], root=str(root), mode=mode), ensure_ascii=False))
raise SystemExit(1 if report["status"] == "NO_GO" else 2)
PY
