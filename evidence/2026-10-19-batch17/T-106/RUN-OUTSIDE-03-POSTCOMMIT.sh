#!/bin/bash
# 主控在沙箱外运行；提交后结果故障复验，不需手选目录，不证明新的原生目录选择。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
python3 - "$@" <<'PY'
import datetime,json,os,pathlib,re,shutil,subprocess,sys,tempfile
source=pathlib.Path.cwd()
label=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
summary=source/'evidence/2026-10-19-batch17/T-106'/('postcommit-electron-'+label+'.json')
assert not summary.exists(),'已有摘要不覆盖'
root=pathlib.Path(tempfile.mkdtemp(prefix='t106-postcommit-outside-',dir='/private/tmp'))
candidate=root/'candidate';baseline=root/'baseline';baseline.mkdir()
revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
diff=subprocess.check_output(['git','diff','HEAD','--','workbench'],text=True)
dependencies=pathlib.Path(os.environ.get('T106_DEPENDENCIES','/Users/luckye/Documents/Code/a2a/workbench/node_modules')).resolve(strict=True)
runtime=pathlib.Path(os.environ.get('T106_ELECTRON_DIST',str(dependencies/'electron/dist'))).resolve(strict=True)
assert not runtime.is_relative_to('/Volumes') and (runtime/'version').read_text(encoding='utf-8').strip()=='43.4.1'
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_','OPENAI_')) and k not in ('NODE_OPTIONS','NODE_PATH','ELECTRON_RUN_AS_NODE')}
env.update(TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
result=None
try:
 shutil.copytree(source/'workbench',candidate/'workbench',ignore=shutil.ignore_patterns('node_modules','__pycache__'))
 with (root/'baseline.tar').open('xb') as handle:subprocess.run(['git','archive','24cacef60','workbench'],stdout=handle,check=True)
 subprocess.run(['/usr/bin/tar','-xf',str(root/'baseline.tar'),'-C',str(baseline)],check=True)
 for tree in [candidate,baseline]:
  shutil.copytree(dependencies,tree/'workbench/node_modules',symlinks=True)
  (tree/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
 argv=['python3',str(candidate/'workbench/tests/run_t106_postcommit_electron.py'),'--source',str(candidate),'--baseline',str(baseline),'--electron-dist',str(runtime),'--summary',str(summary)]
 print('COMMAND:',' '.join(argv),flush=True)
 result=subprocess.run(argv,env=env)
finally:
 data=json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {}
 if data:
  data.update(candidate_revision=revision,candidate_diff=diff,baseline_revision='24cacef60f9e88103213c0bb93eecb0cb5c41cf3')
  summary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if data.get('cleanup_complete'):
  for tree in [candidate,baseline]:
   if (tree/'workbench/node_modules').exists():shutil.rmtree(tree/'workbench/node_modules')
 if data.get('status')=='PASS' and data.get('cleanup_complete'):shutil.rmtree(root)
 else:print('INCOMPLETE: 保留隔离源码或失败现场：',root,flush=True)
if result is None:raise SystemExit(1)
raise SystemExit(result.returncode)
PY
