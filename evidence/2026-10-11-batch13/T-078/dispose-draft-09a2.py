"""Controller-only archival and removal of the failed fixture and its exact owned slot.

Keep the product verdict INCOMPLETE. No process signals, CLI starts or retries.
Archive symlinks as links; do not follow their targets or copy the global CLI.
"""
import argparse, datetime, json, os, shutil, sqlite3, stat, subprocess, tarfile, traceback
from pathlib import Path
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078');BASE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/t078-2-p1-09a2-sm_du7jo');M=BASE/'p1-materials-09a2'
LAUNCH='d2d9c666-5621-4467-bbe4-d99450bd5503';VOLUME=Path('/Volumes/WD-Elements')
SLOT=VOLUME/'a2a-workbench'/('t078-09-'+LAUNCH)
p=argparse.ArgumentParser();p.add_argument('--approval-ref',required=True);args=p.parse_args()
assert args.approval_ref.strip()
label='draft-disposal-09a2-01';out=BASE/label;out.mkdir()
report={'status':'BLOCKED','scope':'Archival/removal only','product_status':'INCOMPLETE','approval_ref':args.approval_ref,
        'argv':__import__('sys').argv,'signals_sent':0,'process_starts':0,'archives':[],'removed':[]}
def save():
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def inventory(directory):
    # lstat first: do not read through the fixture's CLI executable symlink.
    items={}
    for path in [directory,*sorted(directory.rglob('*'))]:
        info=path.lstat();relative=path.relative_to(directory)
        if stat.S_ISLNK(info.st_mode):kind='link'
        elif stat.S_ISDIR(info.st_mode):kind='directory'
        elif stat.S_ISREG(info.st_mode):kind='file'
        else:raise RuntimeError('Unexpected file type; retain source: '+str(path))
        items[str(relative)]={'kind':kind,'bytes':info.st_size,'link':os.readlink(path) if kind=='link' else None}
    return items
def archive_and_verify(directory,destination):
    items=inventory(directory)
    with tarfile.open(destination,'x:gz',dereference=False) as arc:arc.add(directory,arcname=directory.name)
    with destination.open('rb') as f:os.fsync(f.fileno())
    with tarfile.open(destination) as arc:
        expected={directory.name if n=='.' else directory.name+'/'+n for n in items}
        assert set(arc.getnames())==expected,'Archive member set differs'
        for n,item in items.items():
            name=directory.name if n=='.' else directory.name+'/'+n;member=arc.getmember(name)
            if item['kind']=='link':assert member.issym() and member.linkname==item['link'];continue
            if item['kind']=='directory':assert member.isdir();continue
            assert member.isfile() or member.islnk()
            with (directory/n).open('rb') as src:
                dst=arc.extractfile(member)
                while True:
                    a,b=src.read(1024*1024),dst.read(1024*1024)
                    assert a==b,'Archive byte readback differs: '+n
                    if not a:break
    assert inventory(directory)==items,'Source changed during archival'
    return {'source':str(directory),'archive':str(destination),'bytes':destination.stat().st_size,
            'byte_readback':'PASS','items':items,'symlinks':'Stored as links; targets not opened'}
save()
try:
    approval=json.loads((M/'approval.json').read_text(encoding='utf-8'))
    assert approval['input']['root']==str(ROOT) and approval['input']['launch']==LAUNCH
    assert ROOT.resolve(strict=True)==ROOT and not ROOT.is_symlink()
    assert (ROOT/'approval.json').read_bytes()==(M/'approval.json').read_bytes()
    assert os.path.ismount(VOLUME) and VOLUME.resolve()==VOLUME
    assert SLOT.resolve(strict=True)==SLOT and not SLOT.is_symlink()
    build=json.loads((SLOT/'dist/build.json').read_text(encoding='utf-8'))
    assert build['source']==str(SOURCE/'workbench/app') and build['out']==str(SLOT/'dist')
    continuation=json.loads((M/'continue-esc/result.json').read_text(encoding='utf-8'))
    assert continuation['electron_build']==str(SLOT/'dist') and continuation['input']['launch']==LAUNCH
    cleanup=json.loads((M/'cleanup/result.json').read_text(encoding='utf-8'))
    assert cleanup['status']=='INCOMPLETE' and cleanup['cli_exit_verdict']['status']=='PASS'
    assert (ROOT/'api-error.json').exists() and not (ROOT/'state/daemon.pid').exists()
    owner=json.loads((M/'launch/process-manifest.json').read_text(encoding='utf-8'))
    api_owner=json.loads((ROOT/'api-owner.json').read_text(encoding='utf-8'))
    assert api_owner['argv'][-1]==str(ROOT)
    driver=[json.loads(x) for x in (M/'continue-esc/electron-driver.jsonl').read_text(encoding='utf-8').splitlines()]
    electron=next(v for v in driver if 'pid' in v and 'argv' in v)
    assert electron['argv'][electron['argv'].index('--build')+1]==str(SLOT/'dist')
    stages=[json.loads(x) for x in (M/'continue-esc/electron/stages.jsonl').read_text(encoding='utf-8').splitlines()]
    assert any(v['stage']=='quit' and v['pid']==electron['pid'] for v in stages)
    with sqlite3.connect((ROOT/'state/state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
        daemon=json.loads(db.execute("SELECT data FROM orchestration_events WHERE type='daemon_started' ORDER BY seq DESC LIMIT 1").fetchone()[0])['pid']
        assert db.execute("SELECT 1 FROM orchestration_events WHERE type='daemon_stopped'").fetchone()
    pids=sorted({owner['cli']['pid'],owner['shell_pid'],api_owner['pid'],electron['pid'],daemon})
    assert all(isinstance(v,int) and v>1 for v in pids)
    ps=subprocess.run(['/bin/ps','-p',','.join(map(str,pids)),'-o','pid=,lstart=,comm='],capture_output=True,text=True)
    report['process_check']={'pids':pids,'exit':ps.returncode,'stdout':ps.stdout,'stderr':ps.stderr};save()
    assert ps.returncode==1 and not ps.stdout.strip() and not ps.stderr,'Recorded PID exists or exit unconfirmed; no signal or deletion'
    external=VOLUME/'a2a-evidence/2026-10-11-batch13/T-078'/label
    assert external.parent.resolve(strict=True)==external.parent
    external.mkdir()
    shutil.copyfile(Path(__file__).resolve(),out/'dispose-script.py')
    report['candidate_commit']=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    report['original_cleanup_status']=cleanup['status'];report['build_manifest']=build
    for directory,name in [(ROOT,'root.tar.gz'),(SLOT,'slot.tar.gz')]:
        report['archives'].append(archive_and_verify(directory,external/name));save()
    # Both complete readbacks precede either deletion. Original run verdicts stay unchanged.
    for directory in [ROOT,SLOT]:
        shutil.rmtree(directory);assert not directory.exists()
        report['removed'].append(str(directory));save()
    report.update(status='PASS',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
except Exception as error:
    report.update(error=repr(error),traceback=traceback.format_exc());save()
print(json.dumps({'status':report['status'],'product_status':report['product_status'],'archives':[{'archive':v['archive'],'bytes':v['bytes'],'byte_readback':v['byte_readback']} for v in report['archives']],
                  'removed':report['removed'],'result':str(out/'result.json'),'error':report.get('error')},ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
