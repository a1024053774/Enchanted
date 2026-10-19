#!/bin/bash
# 主控代为在沙箱外提交已完成的worker候选；尾注仍由现有钩子生成。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t105
python3 - <<'PY'
import json,os,pathlib,subprocess
root=pathlib.Path.cwd();evidence=root/'evidence/2026-10-19-batch17/T-105'
env=dict(os.environ);env.update(json.loads((evidence/'worker-commit-environment.json').read_text()))
def git(*args,**kwargs):return subprocess.check_output(['git',*args],cwd=root,env=env,text=True,**kwargs).strip()
assert git('branch','--show-current')=='exec/t105','分支已改变，停止'
assert git('rev-parse','HEAD')=='37c8a9e77c7c0a0e7426accbec077f0e33946bf4','候选起点已改变，停止并核对'
files=['workbench/README.md','workbench/app/main.ts','workbench/app/preload.ts','workbench/app/renderer.tsx',
       'workbench/app/style.css','workbench/src/daemon.ts','workbench/src/gates/cli.ts','workbench/src/panes.ts',
       'workbench/src/store.ts','workbench/tests/test_electron_e2e.py','workbench/tests/test_t091_pane_ipc.mjs',
       'workbench/tests/run_t105_panes.py','workbench/tests/t105_panes_driver.mjs','workbench/tests/test_t105_panes.mjs']
changed=set(git('diff','--cached','--name-only').splitlines())
assert all(p in files or p.startswith('evidence/2026-10-19-batch17/T-105/') for p in changed),'暂存区出现本票之外的文件，停止'
subprocess.run(['git','add','--sparse',*files,str(evidence.relative_to(root))],cwd=root,env=env,check=True)
subprocess.run(['git','diff','--cached','--check'],cwd=root,env=env,check=True)
subprocess.run(['git','commit','-m','feat(workbench): add free terminals and persistent split pane controls'],cwd=root,env=env,check=True)
print(git('show','-s','--format=fuller','HEAD'))
print('STATUS: INCOMPLETE — 提交已完成；真实Electron与独立验收结果另核对。')
PY
