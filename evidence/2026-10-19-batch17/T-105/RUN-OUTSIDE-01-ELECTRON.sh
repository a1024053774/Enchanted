#!/bin/bash
# 执行主控在沙箱外运行。隔离源码/依赖/家目录；不安装应用、不调用模型。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t105
python3 - "$@" <<'PY'
import datetime,json,os,pathlib,shutil,subprocess,sys,tarfile,tempfile
source=pathlib.Path.cwd()
label=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
assert __import__('re').fullmatch(r'[A-Za-z0-9_-]+',label)
summary=source/'evidence/2026-10-19-batch17/T-105'/('electron-'+label+'.json')
assert not summary.exists(),'已有摘要不覆盖，请换编号'
root=pathlib.Path(tempfile.mkdtemp(prefix='t105-outside-',dir='/private/tmp'))
candidate=root/'candidate';baseline=root/'baseline';candidate.mkdir();baseline.mkdir()
env=dict(os.environ);env.update(TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
env.pop('NODE_OPTIONS',None);env.pop('ELECTRON_RUN_AS_NODE',None)
runtime=pathlib.Path(os.environ.get('T105_ELECTRON_DIST','/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist')).resolve(strict=True)
assert not runtime.is_relative_to('/Volumes') and (runtime/'version').read_text().strip()=='43.4.1'
result=None
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
diff=subprocess.check_output(['git','diff','HEAD','--','workbench'],cwd=source,text=True)
try:
 shutil.copytree(source/'workbench',candidate/'workbench',ignore=shutil.ignore_patterns('node_modules','__pycache__'))
 archive=root/'baseline.tar'
 with archive.open('wb') as out:subprocess.run(['git','archive','37c8a9e77','workbench'],cwd=source,stdout=out,check=True)
 with tarfile.open(archive) as data:data.extractall(baseline,filter='data')
 subprocess.run(['npm','ci','--ignore-scripts','--cache',str(root/'npm-cache')],cwd=candidate/'workbench',env=env,check=True)
 shutil.copytree(candidate/'workbench/node_modules',baseline/'workbench/node_modules',symlinks=True)
 for tree in [candidate,baseline]:
  helper=tree/'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
  assert helper.is_file();helper.chmod(0o755) # 只改测试副本。
 argv=['python3',str(candidate/'workbench/tests/run_t105_panes.py'),'--source',str(candidate),'--baseline',str(baseline),'--electron-dist',str(runtime),'--summary',str(summary)]
 print('COMMAND:', ' '.join(argv),flush=True)
 result=subprocess.run(argv,env=env)
finally:
 # 子进程未确认退出时，保留夹具让主控按记录处理；不删除运行中的源码。
 data=json.loads(summary.read_text()) if summary.exists() else {}
 if data:
  data.update(candidate_revision=revision,candidate_diff=diff,baseline_revision='37c8a9e77',runtime=str(runtime))
  summary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if data.get('cleanup_complete'):shutil.rmtree(root)
 else:print('INCOMPLETE: 隔离目录保留：',root)
if result is None:raise SystemExit(1)
raise SystemExit(result.returncode)
PY
