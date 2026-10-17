"""Controller-only cleanup of the exact build slot owned by one completed P1 fixture."""
import argparse, json, shutil, subprocess, traceback
from pathlib import Path
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
p=argparse.ArgumentParser();p.add_argument('--materials',type=Path,required=True);a=p.parse_args()
m=a.materials.resolve();m.relative_to(SOURCE/'evidence/2026-10-11-batch13/T-078')
out=m/'slot-cleanup';out.mkdir()
r={'status':'BLOCKED','argv':__import__('sys').argv,'signals_sent':0}
try:
    approval=json.loads((m/'approval.json').read_text(encoding='utf-8'))
    run=json.loads((m/'continue-esc/result.json').read_text(encoding='utf-8'))
    assert json.loads((m/'cleanup/result.json').read_text(encoding='utf-8'))['status']=='PASS','Fixture cleanup must finish first'
    launch=approval['input']['launch'];slot=Path('/Volumes/WD-Elements/a2a-workbench')/('t078-09-'+launch)
    volume=Path('/Volumes/WD-Elements')
    assert volume.resolve(strict=True)==volume and volume.stat().st_dev!=volume.parent.stat().st_dev,'External volume is not mounted'
    assert run['input']['launch']==launch and run['electron_build']==str(slot/'dist')
    assert not slot.is_symlink() and slot.resolve(strict=True)==slot,'Build slot contains a link'
    build=json.loads((slot/'dist/build.json').read_text(encoding='utf-8'))
    assert build['source']==str(SOURCE/'workbench/app') and build['out']==str(slot/'dist')
    log=[json.loads(line) for line in (m/'continue-esc/electron-driver.jsonl').read_text(encoding='utf-8').splitlines()]
    owner=next(e for e in log if 'argv' in e and 'pid' in e)
    assert owner['argv'][owner['argv'].index('--build')+1]==str(slot/'dist')
    stages=[json.loads(line) for line in (m/'continue-esc/electron/stages.jsonl').read_text(encoding='utf-8').splitlines()]
    assert any(e['stage']=='quit' and e['pid']==owner['pid'] for e in stages),'No recorded Electron exit'
    ps=subprocess.run(['/bin/ps','-p',str(owner['pid']),'-o','pid=,lstart=,command='],capture_output=True,text=True)
    r['process_check']={'pid':owner['pid'],'exit':ps.returncode,'stdout':ps.stdout,'stderr':ps.stderr}
    assert ps.returncode==1 and not ps.stdout.strip() and not ps.stderr,'Recorded Electron PID still exists; no deletion'
    files=[]
    for f in slot.rglob('*'):
        assert not f.is_symlink(),'Build slot contains a link; no deletion'
        if f.is_file():files.append({'path':str(f.relative_to(slot)),'bytes':f.stat().st_size})
    r.update(slot=str(slot),owner_launch=launch,build_manifest=build,files=files,
             replay=run.get('input',{}).get('source_snapshot'),ownership='This worker fixture only; controller executes cleanup outside sandbox')
    (out/'before-delete.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.rmtree(slot)
    assert not slot.exists();r['status']='PASS'
except Exception as error:r.update(error=repr(error),traceback=traceback.format_exc())
with (out/'result.json').open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
