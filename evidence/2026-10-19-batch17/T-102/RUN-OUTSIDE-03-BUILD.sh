#!/bin/bash
# 主控运行：依赖、头文件、临时文件、中间产物均在外置盘；不运行外置盘 .app。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
python3 - "$@" <<'PY'
import datetime, json, os, pathlib, re, shutil, subprocess, sys

repo = pathlib.Path.cwd()
volume = pathlib.Path('/Volumes/WD-Elements')
assert volume.is_mount() and volume.resolve() == volume, '外置盘未挂载；不回退内置盘'
label = sys.argv[1] if len(sys.argv)>1 else 'a2-build-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',label)
run = volume/'a2a-evidence/2026-10-19-batch17/T-102'/label
run.mkdir(parents=True,exist_ok=False)
evidence = repo/'evidence/2026-10-19-batch17/T-102'
summary = {'task':'T-102','attempt':'a2','head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(), 'status':'INCOMPLETE','run':str(run),'commands':[]}
source = repo/'workbench'
stage = run/'workbench'
env = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_CONFIG_')) and k not in ('NODE_OPTIONS','NODE_PATH','ELECTRON_RUN_AS_NODE')}
(run/'tmp').mkdir()
env.update(TMPDIR=str(run/'tmp'),TMP=str(run/'tmp'),TEMP=str(run/'tmp'),npm_config_cache=str(volume/'a2a-t075-npm-cache'),electron_config_cache=str(volume/'a2a-electron-cache'))
def command(argv, cwd):
    index=len(summary['commands'])
    record={'argv':argv,'cwd':str(cwd)}
    summary['commands'].append(record)
    with (run/f'{index:02d}.stdout.log').open('w') as stdout, (run/f'{index:02d}.stderr.log').open('w') as stderr:
        p=subprocess.run(argv,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    record['exit']=p.returncode
    assert p.returncode==0, f'命令失败；保留现场：{argv}，查看 {run}/{index:02d}.stderr.log'
    return (run/f'{index:02d}.stdout.log').read_text(encoding='utf-8')
try:
    # The source snapshot is retained for independent review and byte comparison.
    shutil.copytree(source,stage,ignore=shutil.ignore_patterns('node_modules','__pycache__'))
    package_before=(source/'package.json').read_bytes()
    lock_before=(source/'package-lock.json').read_bytes()
    command(['node','check-cache.mjs'],stage)
    command(['npm','install','--package-lock-only','--ignore-scripts','--cache',env['npm_config_cache']],stage)
    assert (source/'package.json').read_bytes()==package_before and (source/'package-lock.json').read_bytes()==lock_before, '源码在准备期间变化；保留锁文件，不覆盖'
    (source/'package-lock.json').write_bytes((stage/'package-lock.json').read_bytes())
    command(['npm','ci','--ignore-scripts','--cache',env['npm_config_cache']],stage)
    command(['npm','ls','--depth=0'],stage)
    output=command(['npm','run','package:mac','--','--slot',label],stage)
    package=json.loads(output.strip().splitlines()[-1])
    assert pathlib.Path(package['app']).is_dir()
    summary.update(status='PASS',package=package)
except Exception as error:
    summary['error']=str(error)
finally:
    path=evidence/(label+'-summary.json')
    with path.open('x',encoding='utf-8') as f: json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
    with (evidence/(label+'.archive.json')).open('x',encoding='utf-8') as f:
        files=[p for p in run.rglob('*') if p.is_file()]
        json.dump({'original':str(run),'archive':str(run),'files':len(files),'bytes':sum(p.stat().st_size for p in files),'replay':f'bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-03-BUILD.sh {label}-replay'},f,ensure_ascii=False,indent=2);f.write('\n')
    print(path)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
sys.exit(0 if summary['status']=='PASS' else 1)
PY
