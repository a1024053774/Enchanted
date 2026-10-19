#!/bin/bash
# 主控 #19：合并后先跑后台，再跑 T-103 两处合同。无模型调用。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
LABEL=${1:?传入新运行编号，例如 merge-01}
case "$LABEL" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
git merge-base --is-ancestor ea206484b HEAD
git diff --check
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh "$LABEL-backend"
python3 - "$LABEL" <<'PY'
import datetime,json,os,shutil,subprocess,sys,traceback
from pathlib import Path
source=Path.cwd(); label=sys.argv[1]
disk=Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载'
runtime_source=Path('/Users/luckye/Documents/Code/a2a-wt-t103')
dist=runtime_source/'workbench/node_modules/electron/dist'
binary=(dist/'Electron.app/Contents/MacOS/Electron').resolve(strict=True)
assert binary.stat().st_dev != disk.stat().st_dev and os.access(binary,os.X_OK), '必须使用内置盘 Electron'
assert (dist/'version').read_text().strip()=='43.4.1'
out=disk/'a2a-evidence/2026-10-19-batch17/T-104'/label
out.mkdir(exist_ok=False)
(out/'tmp').mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','GIT_'))}
env.pop('NODE_OPTIONS',None); env.pop('ELECTRON_RUN_AS_NODE',None)
env.update(ELECTRON_OVERRIDE_DIST_PATH=str(dist),TMPDIR=str(out/'tmp'),TMP=str(out/'tmp'),TEMP=str(out/'tmp'),
           electron_config_cache=str(disk/'a2a-electron-cache'),npm_config_cache=str(disk/'a2a-t075-npm-cache'))
report=dict(status='INCOMPLETE',task='T-104',part=2,phase='merge checks',checks=[],archive=str(out),
            revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),electron=str(binary))
try:
    argv=['node','--experimental-vm-modules','workbench/tests/test_t091_pane_ipc.mjs',str(out/'ipc.json'),'--contract','picker']
    with (out/'ipc.log').open('x') as log:
        run=subprocess.run(argv,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    result=json.loads((out/'ipc.json').read_text())
    report['checks'].append(dict(name='T-103 IPC',argv=argv,exit=run.returncode,status=result['status']))
    assert run.returncode==0 and result['status']=='PASS'
    argv=['python3','-B','workbench/tests/test_electron_e2e.py','--source',str(source),'--output',str(out/'window'),
          '--stage','window','--ipc-contract','picker','--runtime-source',str(runtime_source)]
    with (out/'window.log').open('x') as log:
        run=subprocess.run(argv,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    verdict=json.loads((out/'window/verdict.json').read_text())
    report['checks'].append(dict(name='T-103 real window_contract',argv=argv,exit=run.returncode,status=verdict['status']))
    assert run.returncode==0 and verdict['status']=='PASS' and verdict['daemon_stopped'] is True
    # Freeze the merged pre-UI candidate for T-104's later known-bad UI run.
    baseline=out/'baseline'
    shutil.copytree(source/'workbench',baseline/'workbench',ignore=shutil.ignore_patterns('node_modules','__pycache__'))
    (baseline/'workbench/node_modules').symlink_to(source/'workbench/node_modules',target_is_directory=True)
    argv=['python3','-B','workbench/tests/run_t104_shell_ui.py','--source',str(source),'--baseline',str(baseline),
          '--electron-dist',str(dist),'--output',str(out/'ui-red'),'--red-only']
    with (out/'ui-red.log').open('x') as log:
        run=subprocess.run(argv,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    red=json.loads((out/'ui-red/run.json').read_text())
    report['checks'].append(dict(name='T-104 real UI red',argv=argv,exit=run.returncode,status=red['status']))
    assert run.returncode==0 and red['status']=='PASS' and red['cleanup_complete'] is True
    report.update(status='PASS',baseline=str(baseline),electron_dist=str(dist),runtime_source=str(runtime_source))
except Exception as error:
    report.update(error=repr(error),traceback=traceback.format_exc())
finally:
    text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    (out/'run.json').write_text(text,encoding='utf-8')
    summary=source/'evidence/2026-10-19-batch17/T-104'/f'{label}-summary.json'
    with summary.open('x',encoding='utf-8') as file:file.write(text)
    manifest=dict(original=str(out),archive=str(out),bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file() and not p.is_symlink()),
                  replay=f'bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-05-MERGE-CHECKS.sh 新编号')
    with summary.with_name(f'{label}.archive.json').open('x',encoding='utf-8') as file:json.dump(manifest,file,ensure_ascii=False,indent=2)
print(text)
raise SystemExit(0 if report['status']=='PASS' else 1)
PY
