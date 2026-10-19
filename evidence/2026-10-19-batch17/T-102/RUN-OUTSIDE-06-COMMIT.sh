#!/bin/bash
# 主控运行：真实入口成功并核对截图后提交；不 submit，不 push，不手写尾注。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
python3 - "$@" <<'PY'
import json, os, pathlib, subprocess, sys

repo=pathlib.Path.cwd(); evidence=repo/'evidence/2026-10-19-batch17/T-102'
assert len(sys.argv)==3, '参数：本轮 E2E 摘要、本轮构建摘要'
e2e=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
build=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
assert all(r['task']=='T-102' and r['attempt']=='a2' and r['status']=='PASS' for r in [e2e,build])
assert e2e['exit']==0 and e2e['cleanup_complete'] and e2e['unmounted_counterexample']['exit']!=0
run=pathlib.Path(e2e['run_json']).parent
assert all((run/name).is_file() for name in ['01-no-task-picker.png','02-projects-tasks.png','03-zsh-command.png','04-reopened-same-shell.png'])
driver=repo/'workbench/tests/run_t102_packaged.mjs'
assert driver.read_bytes()==(run/'source-snapshot'/driver.name).read_bytes(), '验收驱动在运行后变化'
assert (evidence/'RUN-OUTSIDE-05-E2E.sh').read_bytes()==(run/'source-snapshot/RUN-OUTSIDE-05-E2E.sh').read_bytes()
snapshot=pathlib.Path(build['run'])/'workbench'
for name in ['app/desktop.mjs','app/package.mjs','app/main.ts','app/preload.ts','app/renderer.tsx','app/style.css','app/build.mjs','package.json','package-lock.json']:
    assert (repo/'workbench'/name).read_bytes()==(snapshot/name).read_bytes(), '产品与打包候选不符：'+name
for source in (repo/'workbench/src').rglob('*'):
    if source.is_file(): assert source.read_bytes()==(snapshot/'src'/source.relative_to(repo/'workbench/src')).read_bytes(), '后台源码在构建后变化'
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='exec/t102'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='18f943d81e1bbf290a363bf312b479a43f9fec9a'
subprocess.run(['git','diff','--cached','--quiet'],check=True)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'],check=True)
paths=['workbench/README.md','workbench/package.json','workbench/package-lock.json','workbench/src/transport.ts',
       'workbench/app/desktop.mjs','workbench/app/package.mjs','workbench/tests/test_t102_desktop.mjs',
       'workbench/tests/run_t102_packaged.mjs','workbench/tests/test_t096_daemon_restart.mjs',str(evidence.relative_to(repo))]
for p in evidence.iterdir():
    assert p.is_file() and p.suffix in ['.md','.py','.sh','.json','.txt'] and p.stat().st_size<1024*1024, '大块证据或异常文件留给主控核对：'+str(p)
env=dict(os.environ)
env.update(A2A_PROJECT='a2a',A2A_TASK='T-102',A2A_ATTEMPT='a2',A2A_ROLE='worker',
           A2A_SESSION='f6caedda-1ea1-4345-84df-efc8e4ed1d94',A2A_LAUNCH='launch-8343ffbef3274434ab0d956e8c0beb80',
           A2A_LAUNCHES='/Users/luckye/Documents/Code/a2a/records/launches.jsonl',CODEX_THREAD_ID='01a15354-f762-73e3-aa78-c8c1c909260e',
           GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0='/Users/luckye/Documents/Code/a2a/scripts/git-hooks')
assert os.access(pathlib.Path(env['GIT_CONFIG_VALUE_0'])/'prepare-commit-msg',os.X_OK)
subprocess.run(['git','add','--sparse','--',*paths],env=env,check=True)
subprocess.run(['git','diff','--cached','--check'],env=env,check=True)
subprocess.run(['git','commit','-m','feat(T-102): package the macOS workbench and start its detached daemon',
                '-m',f'Packaged entry evidence: {sys.argv[1]}\nBuild evidence: {sys.argv[2]}\nDetails: evidence/2026-10-19-batch17/T-102/RESULTS-a2.md'],env=env,check=True)
subprocess.run(['git','log','-1','--format=fuller'],check=True)
subprocess.run(['git','status','--short','--branch'],check=True)
subprocess.run(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'],check=True)
PY
