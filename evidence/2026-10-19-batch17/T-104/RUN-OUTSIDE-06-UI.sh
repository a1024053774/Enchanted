#!/bin/bash
# 主控 #21：同一内置盘 Electron 的红/绿态、窗口合同及原后台回归。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
LABEL=${1:?传入新编号，例如 ui-01}
case "$LABEL" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh "$LABEL-backend"
python3 - "$LABEL" <<'PY'
import json,os,shutil,subprocess,sys,traceback
from pathlib import Path
source=Path.cwd();folder=source/'evidence/2026-10-19-batch17/T-104';label=sys.argv[1]
accepted=json.loads((folder/'merge-01-summary.json').read_text(encoding='utf-8'))
assert accepted['status']=='PASS'
disk=Path('/Volumes/WD-Elements');assert disk.is_mount(),'外置盘未挂载'
baseline=Path(accepted['baseline']);runtime_source=Path(accepted['runtime_source'])
dist=Path(accepted['electron_dist']);binary=Path(accepted['electron']).resolve(strict=True)
assert binary.stat().st_dev!=disk.stat().st_dev and not binary.is_relative_to('/Volumes') and os.access(binary,os.X_OK)
assert (dist/'version').read_text().strip()=='43.4.1'
out=disk/'a2a-evidence/2026-10-19-batch17/T-104'/label;out.mkdir(exist_ok=False);(out/'tmp').mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','GIT_'))}
env.pop('ELECTRON_RUN_AS_NODE',None);env.pop('NODE_OPTIONS',None)
env.update(ELECTRON_OVERRIDE_DIST_PATH=str(dist),TMPDIR=str(out/'tmp'),TMP=str(out/'tmp'),TEMP=str(out/'tmp'),
           electron_config_cache=str(disk/'a2a-electron-cache'),npm_config_cache=str(disk/'a2a-t075-npm-cache'))
report=dict(status='INCOMPLETE',task='T-104',attempt='a1',part=2,checks=[],archive=str(out),electron=str(binary),
            source=str(source),baseline=str(baseline),revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
def run(name,argv):
    with (out/(name+'.log')).open('x') as log:
        result=subprocess.run(list(map(str,argv)),cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    entry=dict(name=name,argv=list(map(str,argv)),exit=result.returncode)
    report['checks'].append(entry)
    assert result.returncode==0,entry
    return entry
try:
    for name,root,contract in [('baseline',baseline,'picker'),('candidate',source,'shell')]:
        entry=run(name+'-ipc',['node','--experimental-vm-modules','workbench/tests/test_t091_pane_ipc.mjs',
                              out/(name+'-ipc.json'),'--source',root,'--contract',contract])
        result=json.loads((out/(name+'-ipc.json')).read_text())
        assert result['status']=='PASS'
        assert all(result[field]['rejected'] for field in ['known_bad_result','single_pane_counterexample','close_mutant','empty_layout_known_bad','window_key_mutant'])
        entry['status']='PASS'
        entry=run(name+'-window',['python3','-B','workbench/tests/test_electron_e2e.py','--source',root,
                                '--output',out/(name+'-window'),'--stage','window','--ipc-contract',contract,'--runtime-source',runtime_source])
        result=json.loads((out/(name+'-window/verdict.json')).read_text())
        assert result['status']=='PASS' and result['daemon_stopped'] is True
        entry['status']='PASS'
    entry=run('ui',['python3','-B','workbench/tests/run_t104_shell_ui.py','--source',source,'--baseline',baseline,
                    '--electron-dist',dist,'--output',out/'ui'])
    result=json.loads((out/'ui/run.json').read_text())
    assert result['status']=='PASS' and result['cleanup_complete'] is True
    entry['status']='PASS';report['screenshots']=result['screenshots']
    report['status']='PASS'
except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc())
finally:
    text=json.dumps(report,ensure_ascii=False,indent=2)+'\n';(out/'run.json').write_text(text,encoding='utf-8')
    with (folder/(label+'-summary.json')).open('x',encoding='utf-8') as file:file.write(text)
    manifest=dict(original=str(out),archive=str(out),bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
                  replay='bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-06-UI.sh 新编号')
    with (folder/(label+'.archive.json')).open('x',encoding='utf-8') as file:json.dump(manifest,file,ensure_ascii=False,indent=2)
print(text)
raise SystemExit(0 if report['status']=='PASS' else 1)
PY
