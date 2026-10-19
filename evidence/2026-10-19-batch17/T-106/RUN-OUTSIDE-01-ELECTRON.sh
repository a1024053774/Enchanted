#!/bin/bash
# 主控在沙箱外运行；两次原生目录选择须在本测试窗口中操作，不替换选择结果。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
python3 - "$@" <<'PY'
import datetime,json,os,pathlib,re,shutil,subprocess,sys,tempfile
source=pathlib.Path.cwd()
label=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
assert re.fullmatch(r'[A-Za-z0-9_-]+',label), '使用新的运行编号'
summary=source/'evidence/2026-10-19-batch17/T-106'/('form-electron-'+label+'.json')
assert not summary.exists(), '已有摘要不覆盖，请换编号'
root=pathlib.Path(tempfile.mkdtemp(prefix='t106-outside-',dir='/private/tmp'))
candidate=root/'candidate';baseline=root/'baseline';candidate.mkdir();baseline.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CLAUDE_','CODEX_','ANTHROPIC_','OPENAI_'))}
env.update(TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
for key in ['NODE_OPTIONS','NODE_PATH','ELECTRON_RUN_AS_NODE']:env.pop(key,None)
runtime=pathlib.Path(os.environ.get('T106_ELECTRON_DIST','/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist')).resolve(strict=True)
assert not runtime.is_relative_to('/Volumes') and (runtime/'version').read_text().strip()=='43.4.1'
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
diff=subprocess.check_output(['git','diff','HEAD','--','workbench'],cwd=source,text=True)
baseline_revision='f88f6f692'
result=None
try:
 shutil.copytree(source/'workbench',candidate/'workbench',ignore=shutil.ignore_patterns('node_modules','__pycache__'))
 archive=root/'baseline.tar'
 with archive.open('wb') as handle:subprocess.run(['git','archive',baseline_revision,'workbench'],cwd=source,stdout=handle,check=True)
 subprocess.run(['/usr/bin/tar','-xf',str(archive),'-C',str(baseline)],check=True)
 # 只在内置盘临时副本安装依赖；不写共享 checkout，也不下载/启动模型。
 subprocess.run(['npm','ci','--ignore-scripts','--cache',str(root/'npm-cache')],cwd=candidate/'workbench',env=env,check=True)
 shutil.copytree(candidate/'workbench/node_modules',baseline/'workbench/node_modules',symlinks=True)
 for tree in [candidate,baseline]:
  helper=tree/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
  assert helper.is_file();helper.chmod(0o755)
 argv=['python3',str(candidate/'workbench/tests/run_t106_creation.py'),'--source',str(candidate),'--baseline',str(baseline),
       '--electron-dist',str(runtime),'--summary',str(summary)]
 print('COMMAND:', ' '.join(argv),flush=True)
 print('主控需观察本脚本的 NATIVE_DIALOG 提示，在本测试 Electron 的目录对话框中选择提示路径，共两次。',flush=True)
 result=subprocess.run(argv,env=env)
finally:
 data=json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {}
 if data:
  data.update(candidate_revision=revision,candidate_diff=diff,baseline_revision=baseline_revision,runtime=str(runtime))
  summary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if data.get('status')=='PASS' and data.get('cleanup_complete'):shutil.rmtree(root)
 else:print('INCOMPLETE: 保留隔离源码、依赖和失败现场：',root,flush=True)
if result is None:raise SystemExit(1)
raise SystemExit(result.returncode)
PY
