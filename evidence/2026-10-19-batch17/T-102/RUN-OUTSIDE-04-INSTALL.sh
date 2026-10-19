#!/bin/bash
# 主控运行：不覆盖任何已有 /Applications/a2a.app；失败留下现场。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
python3 - "$@" <<'PY'
import datetime, json, os, pathlib, shutil, subprocess, sys

assert len(sys.argv) in (2,3), '参数：03 的 *-summary.json [本次明确获准替换的旧安装记录]'
repo=pathlib.Path.cwd(); summary_path=pathlib.Path(sys.argv[1]).resolve()
build=json.loads(summary_path.read_text(encoding='utf-8'))
assert build['task']=='T-102' and build['attempt']=='a2' and build['status']=='PASS'
source=pathlib.Path(build['package']['app'])
assert source.is_dir() and str(source).startswith('/Volumes/WD-Elements/a2a-workbench/')
destination=pathlib.Path('/Applications/a2a.app')
def inventory(root):
    files=[p for p in root.rglob('*') if p.is_file() or p.is_symlink()]
    return {'files':len(files),'bytes':sum(p.lstat().st_size for p in files)}
before=inventory(source)
replacement=None
if os.path.lexists(destination):
    assert len(sys.argv)==3, '/Applications/a2a.app 已存在；没有明确旧安装记录，停止，不覆盖'
    previous_path=pathlib.Path(sys.argv[2]).resolve()
    assert previous_path.name=='install-20261019T085846.823773Z.json', '本轮只获准替换这份坏安装；其他安装须另行核对'
    previous=json.loads(previous_path.read_text(encoding='utf-8'))
    assert previous['task']=='T-102' and previous['attempt']=='a2' and previous['status']=='PASS' and previous['installed']==str(destination)
    assert destination.is_dir() and not destination.is_symlink()
    assert inventory(destination)==previous['installed_inventory'], '旧安装文件数／字节数已变化；停止，不替换'
    active=[line for line in subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True).splitlines() if line.strip().split(maxsplit=1)[-1].startswith(str(destination)+'/')]
    assert not active, f'旧应用仍有进程；保留现场：{active}'
    volume=pathlib.Path('/Volumes/WD-Elements');assert volume.is_mount(), '外置盘未挂载'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('replaced-%Y%m%dT%H%M%S.%fZ')
    archive=volume/'a2a-evidence/2026-10-19-batch17/T-102'/stamp/'a2a.app'
    archive.parent.mkdir(parents=True,exist_ok=False)
    subprocess.run(['/usr/bin/ditto',str(destination),str(archive)],check=True)
    assert inventory(archive)==inventory(destination)==previous['installed_inventory'], '归档文件数／字节数不一致；保留原安装'
    replacement={'original':str(destination),'archive':str(archive),**previous['installed_inventory'],'previous_install':str(previous_path),'replay':f'codesign --verify --deep --strict {archive}'}
    (repo/'evidence/2026-10-19-batch17/T-102'/(stamp+'.archive.json')).write_text(json.dumps(replacement,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # The verified archive preserves the complete old bundle before clearing its path.
    shutil.rmtree(destination)
destination.mkdir() # Exclusive reservation also rejects a competing install.
argv=['/usr/bin/ditto',str(source),str(destination)]
result={'task':'T-102','attempt':'a2','status':'INCOMPLETE','build_summary':str(summary_path),'argv':argv,'source':str(source),'installed':str(destination),'source_inventory':before,'replacement':replacement}
try:
    subprocess.run(argv,check=True)
    result['installed_inventory']=inventory(destination)
    assert result['installed_inventory']==before, '安装的文件数／字节数不符；保留现场'
    subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(destination)],check=True)
    probe_argv=[str(destination/'Contents/MacOS/a2a'),'-p','JSON.stringify(process.versions)']
    probe=subprocess.run(probe_argv,env={**os.environ,'ELECTRON_RUN_AS_NODE':'1'},capture_output=True,text=True,timeout=30,start_new_session=True)
    result['runtime_probe']={'argv':probe_argv,'exit':probe.returncode,'stdout':probe.stdout,'stderr':probe.stderr}
    assert probe.returncode==0, '安装后的实际运行时不能加载；保留现场'
    helper=destination/'Contents/Resources/app/node_modules/node-pty/build/Release/spawn-helper'
    assert os.access(helper,os.X_OK)
    result.update(status='PASS',helper_mode=oct(helper.stat().st_mode & 0o777),sizeKiB=int(subprocess.check_output(['/usr/bin/du','-sk',str(destination)],text=True).split()[0]))
except Exception as error: result['error']=str(error)
label=datetime.datetime.now(datetime.timezone.utc).strftime('install-%Y%m%dT%H%M%S.%fZ.json')
path=repo/'evidence/2026-10-19-batch17/T-102'/label
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(path);print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['status']=='PASS' else 1)
PY
