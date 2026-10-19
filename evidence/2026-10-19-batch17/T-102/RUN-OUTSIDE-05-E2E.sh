#!/bin/bash
# 主控运行：只经 /Applications 的真实入口；截图／夹具／日志直接留在外置盘。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
python3 - "$@" <<'PY'
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

repo=pathlib.Path.cwd(); volume=pathlib.Path('/Volumes/WD-Elements')
assert volume.is_mount(), '外置盘未挂载'
assert len(sys.argv)==2 and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',sys.argv[1]), '参数：新的运行编号，如 a2-e2e-01'
label=sys.argv[1]; run=volume/'a2a-evidence/2026-10-19-batch17/T-102'/label
assert not run.exists(), '保留已有现场，改用新编号'
run.parent.mkdir(parents=True,exist_ok=True)
evidence=repo/'evidence/2026-10-19-batch17/T-102'
script=repo/'workbench/tests/run_t102_packaged.mjs'
argv=['node',str(script),str(run)]
summary={'task':'T-102','attempt':'a2','status':'INCOMPLETE','argv':argv,'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
try:
    packaged=pathlib.Path('/Applications/a2a.app/Contents/Resources/app')
    for local,installed in [('app/desktop.mjs','desktop.mjs'),('src/transport.ts','src/transport.ts')]:
        assert (repo/'workbench'/local).read_bytes()==(packaged/installed).read_bytes(), '安装候选与当前产品源码不符'
    with tempfile.TemporaryDirectory(prefix='a2at102-unmounted-',dir='/private/tmp') as tmp:
        negative_argv=['node',str(repo/'workbench/app/package.mjs'),'--slot','must-not-build']
        negative=subprocess.run(negative_argv,cwd=repo,env={**os.environ,'A2A_BUILD_VOLUME':tmp},text=True,capture_output=True)
        summary['unmounted_counterexample']={'argv':negative_argv,'volume':tmp,'exit':negative.returncode,'stdout':negative.stdout,'stderr':negative.stderr,'created_files':list(pathlib.Path(tmp).iterdir())}
        assert negative.returncode!=0 and '打包要求真实挂载的外置盘' in negative.stderr and not summary['unmounted_counterexample']['created_files']
    driver_before=script.read_bytes()
    p=subprocess.run(argv,cwd=repo,text=True,capture_output=True,start_new_session=True)
    summary['exit']=p.returncode
    if run.is_dir():
        (run/'runner.stdout.log').write_text(p.stdout,encoding='utf-8');(run/'runner.stderr.log').write_text(p.stderr,encoding='utf-8')
        snapshot=run/'source-snapshot'; snapshot.mkdir()
        (snapshot/script.name).write_bytes(driver_before)
        shutil.copyfile(evidence/'RUN-OUTSIDE-05-E2E.sh',snapshot/'RUN-OUTSIDE-05-E2E.sh')
        assert script.read_bytes()==driver_before, '验收期间驱动变化；不报告 PASS'
    if (run/'run.json').exists():
        result=json.loads((run/'run.json').read_text(encoding='utf-8'))
        summary.update(run_json=str(run/'run.json'),checks=result['checks'],screenshots=result['screenshots'],cleanup_complete=result.get('cleanup_complete'),error=result.get('error'))
        if p.returncode==0 and result['status']=='PASS' and result['cleanup_complete']: summary['status']='PASS'
    else: summary.update(error='未生成 run.json',stdout=p.stdout,stderr=p.stderr)
except Exception as error: summary['error']=str(error)
finally:
    path=evidence/(label+'-summary.json')
    with path.open('x',encoding='utf-8') as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
    if run.exists():
        files=[p for p in run.rglob('*') if p.is_file() or p.is_symlink()]
        with (evidence/(label+'.archive.json')).open('x',encoding='utf-8') as f:
            json.dump({'original':str(run),'archive':str(run),'files':len(files),'bytes':sum(p.lstat().st_size for p in files),'replay':f'bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-05-E2E.sh {label}-replay'},f,ensure_ascii=False,indent=2);f.write('\n')
    print(path); print(json.dumps(summary,ensure_ascii=False,indent=2))
sys.exit(0 if summary['status']=='PASS' else 1)
PY
