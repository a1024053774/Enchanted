"""Run the actual 09C timed coordinator on the real deterministic-PTY chain.

No vendor CLI/model. Only provider executable identity uses the existing,
PID/argv/lstart-verified peer seam; gate, hooks, relay, HTTP and Electron are real.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time
import traceback

from test_t078_09c_real_chain import CScene, preflight as base_preflight, SOURCE, TESTS, BASE, STRUCTURE
from test_t078_a14_rehearsal import save, require, wait_for
from p1_processes import identity_from_ps


def preflight(signature):
    require('REHEARSAL ONLY' in signature and bool(signature.strip()), 'explicit_rehearsal_signature_required')
    result=base_preflight()
    paths=[Path(__file__),TESTS/'t078_09c_timed_run.py',BASE/'prepare-rev2-owner.py',BASE/'prepare-a14.py']
    for path in paths:
        require(path.is_file(),'existing coordinator path',str(path));ast.parse(path.read_text(encoding='utf-8'))
    require(not subprocess.check_output(['git','diff','7a6edbff8','--','workbench/src','workbench/app','acceptance'],cwd=SOURCE),
            'product app acceptance unchanged')
    return {**result,'coordinator_paths':list(map(str,paths)),'signature_ref':signature,'scope':__doc__,
            'phase_executor':'actual t078_09c_timed_run.py CLI; no replacement of Timed methods',
            'duplicate_probe':'after PASS only; same CLI must reject before binding and preserve all result bytes'}


class CoordinatorScene(CScene):
    def __init__(self,output,signature):
        super().__init__(output);self.signature=signature;self.coordinator=None

    def freeze_sources(self,snapshot):
        # Match the coordinator's strict file-only source closure. No directory
        # entries and no dependency/cache trees may enter this archive.
        tracked=subprocess.check_output(['git','ls-files','-z','--','workbench/src','workbench/app','workbench/bin','workbench/tests'],cwd=SOURCE).decode().split('\0')
        paths=[SOURCE/name for name in tracked if name and (Path(name).suffix in
            ['.py','.ts','.mjs','.js','.c','.html','.css','.json'] or name.startswith(('workbench/bin/','workbench/app/')))]
        paths += [SOURCE/'workbench/package.json',SOURCE/'workbench/package-lock.json',STRUCTURE,
                  BASE/'prepare-a14.py',BASE/'prepare-rev2-owner.py',BASE/'09b-materials-01/protocol.json',
                  BASE/'stage-b-a12-ideation-approval-01.json']
        paths=sorted(set(paths));names=[]
        with tarfile.open(snapshot,'x:gz') as archive:
            for path in paths:
                require(path.is_file() and path.resolve()==path,'regular source path',str(path))
                name=str(path.relative_to(SOURCE));archive.add(path,arcname=name,recursive=False);names.append(name)
        with tarfile.open(snapshot) as archive:
            require(archive.getnames()==names,'unique regular source closure')
            for path,name in zip(paths,names):require(archive.extractfile(name).read()==path.read_bytes(),'source byte readback',name)
        return names

    def approve(self,p1,stage):
        path=p1/'phases'/stage/'approval.json';value=json.loads(path.read_bytes())
        require(value['approved_by'] is None and value['approval_ref'] is None,'unsigned fresh phase approval')
        value.update(approved_by='executor',approval_ref=self.signature+' / '+stage)
        # This is a newly created fixture draft, not a historical signed artifact.
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return path

    def bind_peer_launch(self,role):
        p1=self.p1s[role];inp=self.inputs[role]
        peer=json.loads((self.root/'peer'/role/'ready.json').read_bytes())
        identities=[];commands=[]
        for _ in range(2):
            argv=['/bin/ps','-p',str(peer['pid']),'-o','pid=,lstart=,comm=']
            result=subprocess.run(argv,env={**self.env,'LC_ALL':'C','LANG':'C'},capture_output=True,text=True,timeout=5)
            identities.append(identity_from_ps(peer['pid'],result.returncode,result.stdout,result.stderr))
            commands.append({'argv':argv,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        require(identities[0] is not None and identities[0]==identities[1],'stable actual peer comm identity')
        info=self.gate('pane_process_info','--thread',inp['thread'])
        require(info['leader']==peer['pid'],'actual peer leader')
        launch=p1/'rehearsal-launch';launch.mkdir()
        save(launch/'process-manifest.json',{'launch':inp['launch'],'session':inp['session'],
            'shell_pid':info['shell_pid'],'cli':identities[0],'scope':'actual deterministic PTY peer; not a Claude process'})
        save(p1/'launch-binding.json',{'launch_label':launch.name,'process_manifest':str(launch/'process-manifest.json')})
        save(launch/'identity-probes.json',{'scope':'real ps twice; exact format read by P1 same_cli','commands':commands})

    def prepare_C_I1(self):
        inp=self.inputs['ideation'];p1=self.p1s['ideation'];folder=p1/'phases/C-I1'
        wait_for('C-I1 real PermissionRequest',lambda:any(e['type']=='permission_wait' and e['launch']==inp['launch'] for e in self.events()))
        self.review_permission(inp,'C-I1')
        dispatch=self.phase_c('C-I1','observe','dispatch-01')
        draft=folder/'permission-approval-01.json'
        self.command([sys.executable,'-B',BASE/'prepare-a14.py','--mode','permission','--p1',p1,'--result',dispatch,'--output',draft])
        value=json.loads(draft.read_bytes());require(value['approved_by'] is None and value['approval_ref'] is None,'fresh C-I1 permission')
        value.update(approved_by='executor',approval_ref=self.signature+' / C-I1 permission')
        draft.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def policy(self):
        plan=json.loads((self.root/'protocol-plan.json').read_bytes());inp=self.inputs['ideation']
        value={'approved_by':'executor','approval_ref':self.signature,'scene':'09C','role':'ideation',
            'source':'test-simulated-user','source_revision':plan['source_revision'],'package':plan['package'],
            'target_binding':plan['target_binding'],'launch':inp['launch'],'session':inp['session'],'thread':inp['thread'],
            'stages':['C-I2','C-I3'],'max_Enter_per_stage':1,
            'stop_binding':'actual original C-I1 queued request -> Stop/relay entry only',
            'scope':'Main #359 REHEARSAL ONLY; deterministic native transport; no vendor CLI/model'}
        path=self.output/'timed-preapproval.json';save(path,value);return path

    def duplicate_probe(self,argv,coordinator_output):
        # One completed execution, followed by a deliberate refusal probe. No
        # permission/business failure is retried, and no method is mocked here.
        roots=[coordinator_output,*[p1/'phases' for p1 in self.p1s.values()]]
        def snapshot():return {str(p):p.read_bytes() for root in roots for p in root.rglob('*') if p.is_file()}
        before=snapshot();events_before=self.events();posts_before=self.counts()
        folder=self.output/'coordinator-duplicate-refusal';folder.mkdir()
        with (folder/'original-coordinator-result.json').open('xb') as stream:stream.write((coordinator_output/'result.json').read_bytes())
        save(folder/'before.json',{'events':events_before,'POST':posts_before,'files':len(before)})
        result=subprocess.run(list(map(str,argv)),cwd=SOURCE,env=self.env,capture_output=True,timeout=10)
        for name,raw in [('stdout.bin',result.stdout),('stderr.bin',result.stderr)]:
            with (folder/name).open('xb') as stream:stream.write(raw)
        after=snapshot();events_after=self.events();posts_after=self.counts()
        save(folder/'after.json',{'events':events_after,'POST':posts_after,'files':len(after)})
        require(result.returncode==1 and b'FileExistsError' in result.stderr,'duplicate CLI refused at exclusive mkdir')
        require(after==before,'duplicate preserves every original phase/coordinator byte',
            [p for p in set(before)|set(after) if before.get(p)!=after.get(p)],[])
        require(events_after==events_before and posts_after==posts_before,'duplicate zero gate/window/POST effects')
        save(folder/'result.json',{'status':'PASS','expected_exit':1,'actual_exit':result.returncode,
            'complete_coordinator_executions':1,'refused_duplicate_invocations':1,
            'original_files_byte_compared':len(before),'original_bytes_compared':sum(map(len,before.values())),
            'gate_event_delta':0,'POST_delta':0,'key_delta':0,'result_overwrites':0})

    def flow(self):
        print(json.dumps({'stage':'setup','coordinator':'real CLI','model_turns':0}),flush=True)
        self.setup()
        for role in ['ideation','executor']:self.bind_peer_launch(role)
        self.phase_c('C-I1','initialize','initialized-01');self.phase_c('C-I1','start','start-01')
        self.prepare_C_I1();policy=self.policy()
        out=self.output/'coordinator-01'
        argv=[sys.executable,'-B',TESTS/'t078_09c_timed_run.py','--plan',self.root/'protocol-plan.json',
            '--stage-a',self.stage_a,'--ideation',self.p1s['ideation'],'--executor',self.p1s['executor'],
            '--build',self.build,'--preapproval',policy,'--signature-ref',self.signature,'--output',out]
        save(self.output/'coordinator-command.json',{'argv':list(map(str,argv)),'signature_source':'explicit outer --signature-ref',
            'business_execution_limit':1,'timed_mode':'unchanged actual coordinator, C-I1 check/Enter through final collect'})
        control_start=time.monotonic()
        print(json.dumps({'stage':'coordinator','status':'WAITING_REAL_CLOCK','expected_seconds':'>120 and <150','model_turns':0}),flush=True)
        self.coordinator=self.spawn('coordinator',argv);self.coordinator.wait(timeout=180)
        require(self.coordinator.returncode==0,'actual coordinator exit',self.coordinator.returncode,0)
        result=json.loads((out/'result.json').read_bytes())
        require(result['status']=='PASS' and result['POST']=={'ideation':7,'executor':1} and result['roots']=={'ideation':4,'executor':1},'actual coordinator result',result)
        require(result['signature_ref']==self.signature,'coordinator signature parameter preserved')
        i1=self.p1s['ideation']/'phases'
        sent=json.loads((i1/'C-I1/execute-02/settlement.json').read_bytes())
        early=json.loads((i1/'C-I2/execute-02/result.json').read_bytes())
        late=json.loads((i1/'C-I3/execute-02/result.json').read_bytes())
        require(early['relay_receipt']['error']=='stop_too_early','actual early denial')
        require(late['status']=='PASS' and 120000<late['enter_at']['wall_age_ms']<130000 and
            late['enter_at']['observed_elapsed_ms']>=120100,'actual conditional Enter time',late)
        # Independent readback uses the existing HTTP/SQLite/target oracle, not
        # the coordinator's PASS string or its own expected counts.
        checked=self.readback(sent['stop'],early,late,control_start)
        self.duplicate_probe(argv,out)
        import t078_09c_driver as clocks
        finish=clocks.timing(json.loads((self.root/'clock-origin.json').read_bytes()),clocks.Clock())
        require(120000<finish['wall_age_ms']<150000,'full observation including duplicate probe within 150 seconds')
        return {**checked,'coordinator_execution_count':1,'duplicate_refusal':'PASS',
            'coordinator_output':str(out),'signature_ref':self.signature,'completion_age_ms':finish['wall_age_ms']}

    def cleanup(self):
        if self.coordinator is not None and self.coordinator.poll() is None:
            self.coordinator.send_signal(signal.SIGINT);self.coordinator.wait(timeout=15)
        result=self.output/'coordinator-01/result.json'
        if result.is_file():require('close_error' not in json.loads(result.read_bytes()),'conditional harness cleanup unconfirmed; retain root')
        return super().cleanup()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--signature-ref',required=True);parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    try:checked=preflight(args.signature_ref);save(output/'preflight.json',checked)
    except Exception as error:
        save(output/'result.json',{'status':'INCOMPLETE','stage':'preflight','error':repr(error),
            'traceback':traceback.format_exc(),'scene_process_starts':0});return 1
    if args.check_only:print(json.dumps(checked,ensure_ascii=False));return 0
    dirty=subprocess.check_output(['git','status','--porcelain','--','workbench','acceptance','scripts'],cwd=SOURCE,text=True)
    if dirty.strip():
        save(output/'result.json',{'status':'INCOMPLETE','stage':'source-preflight','dirty':dirty.splitlines(),'scene_process_starts':0});return 1
    result={'status':'INCOMPLETE','scope':__doc__,'real_model_turns':0,'vendor_CLIs':0,
            'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()}
    def hard(*_):raise TimeoutError('coordinator_rehearsal_hard_timeout_420s')
    previous=signal.signal(signal.SIGALRM,hard);signal.alarm(420);scene=None
    try:
        scene=CoordinatorScene(output/'flow',args.signature_ref);result.update(scene.flow())
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        if scene is not None:
            try:result['cleanup']=scene.cleanup()
            except Exception as error:result.update(status='INCOMPLETE',cleanup_error=repr(error),cleanup_traceback=traceback.format_exc())
        save(output/'result.json',result)
    print(json.dumps({k:result[k] for k in ['status','POST','scene_age_ms','coordinator_execution_count','error','cleanup_error'] if k in result}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
