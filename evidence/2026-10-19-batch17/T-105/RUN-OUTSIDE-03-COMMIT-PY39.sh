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
assert git('rev-parse','HEAD')=='ba23a605d2536c91668f6628a54ccf01ff9c25d7','候选起点已改变，停止并核对'
files=[] # 本轮只改T-105证据目录中的运行与验证脚本。
changed=set(git('diff','--cached','--name-only').splitlines())
assert all(p in files or p.startswith('evidence/2026-10-19-batch17/T-105/') for p in changed),'暂存区出现本票之外的文件，停止'
subprocess.run(['git','add','--sparse',*files,str(evidence.relative_to(root))],cwd=root,env=env,check=True)
subprocess.run(['git','diff','--cached','--check'],cwd=root,env=env,check=True)
subprocess.run(['git','commit','-m','fix(t105): prepare Electron replay with Python 3.9'],cwd=root,env=env,check=True)
print(git('show','-s','--format=fuller','HEAD'))
print('STATUS: INCOMPLETE — Python 3.9修复已提交；真实Electron与独立验收结果另核对。')
PY
