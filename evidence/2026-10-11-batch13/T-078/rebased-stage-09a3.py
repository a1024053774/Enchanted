"""Controller-run bounded cleanup or zero-model regression stage, no vendor CLI."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078');BASE=ROOT/'evidence/2026-10-11-batch13/T-078'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['cleanup','regression-02'],required=True);args=p.parse_args()
out=BASE/('rebased-outside-'+args.mode+'-09a3');out.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
log={'status':'INCOMPLETE','mode':args.mode,'scope':'沙箱外独立阶段；只操作本轮夹具；无 vendor/model 启动','checks':[],'commands':[],'real_model_turns':0}
def save(): (out/'result.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
def run(argv,*,cwd=ROOT,child_env=env,timeout=30,allowed=(0,)):
    argv=[str(v) for v in argv];n=len(log['commands'])+1
    with (out/f'{n}.stdout.bin').open('xb') as stdout,(out/f'{n}.stderr.bin').open('xb') as stderr:
        r=subprocess.run(argv,cwd=cwd,env=child_env,stdout=stdout,stderr=stderr,timeout=timeout,start_new_session=True)
    stdout=(out/f'{n}.stdout.bin').read_text(encoding='utf-8');stderr=(out/f'{n}.stderr.bin').read_text(encoding='utf-8')
    log['commands'].append({'argv':argv,'cwd':str(cwd),'exit_code':r.returncode,'stdout_file':f'{n}.stdout.bin','stderr_file':f'{n}.stderr.bin'});save()
    assert r.returncode in allowed,(argv,r.returncode,stderr)
    return r.returncode,stdout
save()
try:
    if args.mode=='cleanup':
        original=Path('/private/tmp/s3f-92fdj4n_');assert original.is_dir()
        expected={'t-njhekowz':20686,'t-0v7tn673':20555,'t-58byqww6':20607,'t-9jfqfrc7':20570,
                  't-ihwvaq2a':20628,'t-_cf6ewvd':20590,'t-q0tirof8':20669,'t-1iv466bz':20654}
        observed=json.loads((BASE/'rebased-coop-local-09a3/run.json').read_text(encoding='utf-8'))
        assert observed['artifact_root']==str(original)
        for name,pid in expected.items():
            fixture=original/name;state=fixture/'isolated state';credential=fixture/'operator-01.credential.json'
            ready=json.loads((fixture/'host-01.ready.json').read_bytes())
            assert ready['pid']==pid and ready['root']==str(state)
            assert int((state/'daemon.pid').read_text())==pid
            code,command=run(['/bin/ps','-p',pid,'-o','command='],allowed=(0,1))
            assert code==0 and str(ROOT/'workbench/tests/daemon_acceptance_host.ts') in command and str(state) in command,'PID identity unknown; no signal/stop'
            private={**env,'A2A_OPERATOR_CREDENTIAL':str(credential)}
            cli=['node',ROOT/'workbench/src/gates/cli.ts','--state',state]
            _,value=run([*cli,'daemon_status'],child_env=private);status=json.loads(value)
            assert status['pid']==pid and status['root']==str(state)
            _,value=run([*cli,'daemon_stop'],child_env=private);assert json.loads(value)['ok']
            deadline=time.monotonic()+15
            while True:
                code,_=run(['/bin/ps','-p',pid,'-o','pid='],allowed=(0,1))
                if code==1:break
                assert time.monotonic()<deadline,'Owned process exit unconfirmed; no forced signal/retry'
                time.sleep(.1)
            assert not (state/'daemon.pid').exists() and not (state/'control.sock').exists()
            log['checks'].append({'fixture':str(fixture),'pid':pid,'status':'PASS','action':'Authenticated daemon_stop; root and evidence retained'});save()
    else:
        plan=json.loads((BASE/'regression-02-source-freeze.json').read_bytes())
        _,head=run(['git','rev-parse','HEAD']);head=head.strip();assert head==plan['revision'],'Frozen code revision changed'
        assert json.loads((BASE/'rebased-outside-cleanup-09a3/result.json').read_bytes())['status']=='PASS','Stop old isolated backends first'
        assert os.path.ismount('/Volumes/WD-Elements'),'External cache volume missing; no fallback'
        _,dirty=run(['git','diff','--','workbench']);assert not dirty,'Workbench candidate is not frozen'
        previous=BASE/'rebased-outside-regression-09a3'
        for name,count in [('runtime',12),('input-failures',11)]:
            facts=json.loads((previous/name/'results.json').read_bytes())
            assert facts['status']=='PASS' and facts['cleanup_complete'] and len(facts['checks'])==count
        _,product_change=run(['git','diff','0f754a6dfd555568cb377affbbe52655a13d3d4d',head,'--','workbench/src','workbench/app','workbench/hooks'])
        assert not product_change,'Passed product/UI scenarios changed; do not silently reuse their evidence'
        log['revision']=head;save()
        frontend=Path(json.loads((previous/'runtime/build.json').read_bytes())['out'])
        log['previous_passes']={'source_revision':'0f754a6dfd555568cb377affbbe52655a13d3d4d','runtime':12,'input-failures':11,'not_rerun':True,'product_files_unchanged':True};save()
        target=out/'worker-inbox'
        run(['python3','-B',ROOT/'workbench/tests/test_t078_input_entry.py','--source',ROOT,'--output',target,'--worker-inbox','--reuse-build',frontend],timeout=300)
        facts=json.loads((target/'results.json').read_bytes())
        assert facts['status']=='PASS' and facts['setup_complete'] and facts['cleanup_complete'] and len(facts['checks'])==14
        log['checks'].append({'name':'worker-inbox','status':'PASS','checks':14,'source':'Real daemon/Electron/PTY, deterministic native receiver'});save()
        for suite,count in [('coop',8),('recovery',9),('run',18),('cas',1)]:
            target=out/suite
            run(['python3','-B',ROOT/'workbench/tests/run_s3_rebased_regression.py','--suite',suite,'--revision',head,'--output',target],timeout=720)
            facts=json.loads((target/'run.json').read_bytes());assert facts['status']=='PASS' and facts['tests_run']==count and not facts['failures'] and not facts['errors'] and not facts['skipped']
            log['checks'].append({'name':suite,'status':'PASS','checks':count,'source':'Unchanged business assertions through current controlled actors'});save()
        sys.path.insert(0,str(ROOT/'workbench/tests'))
        from t078_worker_mutants import exercise
        def run_mutant(argv,name,timeout,expected=0):
            run(argv,timeout=timeout,allowed=(expected,))
        log['worker_rule_counterexamples']=exercise(ROOT,out,frontend,run_mutant)
        log['frontend_slot']=str(frontend)
        _,final=run(['git','rev-parse','HEAD']);assert final.strip()==head
    log['status']='PASS'
except Exception as e:
    import traceback
    log.update(error=repr(e),traceback=traceback.format_exc())
finally:save()
print(json.dumps({'status':log['status'],'mode':args.mode,'output':str(out),'error':log.get('error')},ensure_ascii=False))
raise SystemExit(0 if log['status']=='PASS' else 1)
