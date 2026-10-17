"""Controller #153: stop only the recorded block fake API, archive, finish root cleanup."""
import argparse,importlib.util,json,os,shlex,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path

BASE=Path(__file__).resolve().parent
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
M=BASE/'p1-materials-09a3r2-block'
ROOT=Path('/private/tmp/t078-2-p1-09a3r2-block-093154n0')
LAUNCH='c55cbe18-b823-42a6-a707-51fe992f077b'
SESSION='ba9bc02d-7a4e-49f1-8109-85de8625449f'
API_PID=48954
EXPECTED_ARGV=['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_messages.py'),str(ROOT)]

def owns_api(command):
    parts=shlex.split(command)
    # ps can print the resolved interpreter path. The approved -B/script/root
    # arguments must still match exactly, with no additional command or args.
    return len(parts)==4 and parts[1:]==EXPECTED_ARGV[1:]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--approval-ref',required=True);args=p.parse_args()
    assert args.approval_ref.strip()
    out=M/'cleanup-recovery-154';out.mkdir()
    sys.path.insert(0,str(SOURCE/'workbench/tests'))
    from command_evidence import CommandLog
    from p1_processes import identity_from_ps
    log=CommandLog(out)
    r={'status':'BLOCKED','scope':'只停 block 假 API；确认原进程退出、外置归档后只删除该根，不删除 slot','approval_ref':args.approval_ref,
       'root':str(ROOT),'launch':LAUNCH,'api_pid':API_PID,'signals_sent':[],'real_model_turns':0,'slots_removed':[]}
    def save():(out/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def probe(pid,command=False):
        result=log.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,'+('command=' if command else 'comm=')],cwd=SOURCE,env={'LC_ALL':'C','LANG':'C'},timeout=10)
        return identity_from_ps(pid,result.returncode,result.stdout,result.stderr)
    def absent(pid):
        deadline=time.monotonic()+15
        while probe(pid) is not None:
            if time.monotonic()>=deadline:raise RuntimeError('Owned process exit not confirmed: '+str(pid))
            time.sleep(.1)
    save()
    try:
        assert ROOT.is_dir() and ROOT.resolve()==ROOT and not ROOT.is_symlink()
        approved=json.loads((M/'input.json').read_bytes());actual=json.loads((ROOT/'input.json').read_bytes())
        assert approved==actual and actual['launch']==LAUNCH and actual['session']==SESSION and actual['root']==str(ROOT)
        assert json.loads((M/'cleanup/result.json').read_bytes())['status']=='BLOCKED'
        assert json.loads((ROOT/'api-owner.json').read_bytes())=={'pid':API_PID,'argv':EXPECTED_ARGV}
        ready=json.loads((ROOT/'api-ready.json').read_bytes())
        assert ready['pid']==API_PID and ready['launch']==LAUNCH and ready['session']==SESSION
        current=probe(API_PID,True);r['api_before']=current;save()
        if current is not None:
            assert owns_api(current['command']),'PID command/root mismatch; no signal'
            assert probe(API_PID,True)==current,'PID lifetime changed before signal; no signal'
            r['signal_intent']={'pid':API_PID,'signal':'SIGTERM','identity':current};save()
            os.kill(API_PID,signal.SIGTERM)
            r['signals_sent'].append({'pid':API_PID,'signal':'SIGTERM'});save()
            absent(API_PID)
        r['api_exit_confirmed']=True;save()
        manifest=json.loads((M/'launch/process-manifest.json').read_bytes())
        assert manifest['launch']==LAUNCH and manifest['session']==SESSION and manifest['cli']['pid']==48987 and manifest['shell_pid']==48986
        # Do not signal the CLI, its shell, daemon, Electron, or any PID group.
        for pid in [48987,48986,48977]:absent(pid)
        assert not (ROOT/'state/daemon.pid').exists() and not (ROOT/'state/control.sock').exists()
        r['other_owned_exits_confirmed']=[48987,48986,48977]
        volume=Path('/Volumes/WD-Elements');assert os.path.ismount(volume) and volume.resolve()==volume
        external=volume/'a2a-evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/cleanup-recovery-153'
        external.parent.mkdir(parents=True,exist_ok=True);assert external.parent.resolve()==external.parent;external.mkdir()
        # Same cleanup rule as the runner: discard only this dead fixture's
        # private operator credential before archiving it; no user auth exists.
        if (ROOT/'operator.json').exists():(ROOT/'operator.json').unlink()
        spec=importlib.util.spec_from_file_location('verified_root_archive',BASE/'cleanup-slot-after-reboot-09a2.py')
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        archive=external/'fixture.tar.gz';inventory=helper.archive_and_verify(ROOT,archive)
        r.update(archive=str(archive),archive_bytes=archive.stat().st_size,byte_readback='PASS',inventory=inventory,
                 source_revision=actual['code_revision'],source_snapshot=actual['source_snapshot']);save()
        # A second read before deleting guards the archive/delete boundary.
        assert probe(API_PID) is None
        for pid in [48987,48986,48977]:assert probe(pid) is None
        assert ROOT.resolve()==ROOT and helper.inventory(ROOT)==inventory
        assert not (ROOT/'api-error.json').exists(),'Protocol failure retained; root not removed'
        shutil.rmtree(ROOT);assert not ROOT.exists()
        r.update(status='PASS',removed=[str(ROOT)],root_removed=True)
        shutil.copyfile(Path(__file__).resolve(),out/'executed-script.py')
    except Exception as error:r.update(error=repr(error),traceback=traceback.format_exc(),root_retained=ROOT.exists())
    save();print(json.dumps({k:r.get(k) for k in ['status','signals_sent','archive','byte_readback','root_removed','root_retained','error']},ensure_ascii=False))
    return 0 if r['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
