"""09C real daemon/relay/inbox/Stop/HTTP/Electron rehearsal; deterministic PTY roles.

No Claude/Codex/vendor model. Provider identity is the existing PID-verified
PTY seam; business requests and all relay results remain production paths.
"""
import argparse
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback
import uuid

from test_t078_a14_rehearsal import Scene, save, require, wait_for, process_exists, NODE, CLI
from p1_reuse import process_command
from t078_raw_retention import NativeRuntime, check_identities
from p1_output import read_complete_output, validate_capture
from t078_09c_driver import visible_command

SOURCE=Path(__file__).resolve().parents[2]
TESTS=SOURCE/'workbench/tests'
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
STRUCTURE=BASE/'09c-fix-01/request-structure.json'


def preflight():
    import ast
    paths=[NODE,CLI,STRUCTURE,TESTS/'t078_09c_driver.py',TESTS/'t078_09b_i1_permission.py',
           TESTS/'t078_09b_rehearsal_host.ts',TESTS/'t078_09b_rehearsal_peer.py',TESTS/'t078_09b_fake_api.py',
           TESTS/'t078_native_receiver.c',Path('/usr/bin/clang'),SOURCE/'workbench/node_modules/electron/path.txt',
           BASE/'prepare-a14.py',Path(__file__)]
    require(Path('/Volumes/WD-Elements').is_mount(),'external build volume mounted')
    for path in paths:
        require(path.is_file(),'existing path',str(path))
        if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8'))
    value=json.loads(STRUCTURE.read_bytes())
    require(value['request']['tools'][0]['input_schema']['required']==['command'],'first-scene Bash schema')
    require(not value['redaction']['credentials_copied'],'no credential copied')
    return {'status':'PASS','paths':list(map(str,paths)),'request_sources':[value['source_initial'],value['source_tool_result']],
            'models':0,'vendor_CLIs':0,'expected_wall_wait_seconds':120.1,'hard_timeout_seconds':420}


class CScene(Scene):
    def __init__(self,out):
        super().__init__(out,'09C');self.p1s={};self.inputs={};self.signature='REHEARSAL ONLY main #365 deterministic native chain'

    def approve(self,p1,stage):
        path=p1/'phases'/stage/'approval.json';value=json.loads(path.read_bytes())
        value.update(approved_by='executor',approval_ref=self.signature+' / '+stage)
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return path

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

    def setup(self):
        (self.root/'repo/value.txt').write_text('09C deterministic baseline\n',encoding='utf-8')
        (self.root/'repo/oracle/contract.json').write_text('{"model":0}\n',encoding='utf-8')
        for argv in [['git','-C',self.root/'repo','init','-b','main'],['git','-C',self.root/'repo','add','value.txt','oracle/contract.json'],
                     ['git','-C',self.root/'repo','commit','-m','09C scratch only']]:self.command(argv)
        receiver=self.root/'target/bin/codex-receiver'
        self.command(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',TESTS/'t078_native_receiver.c','-o',receiver])
        (self.root/'target/role.md').write_text('Deterministic target; no model.\n',encoding='utf-8')
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
        snapshot=self.root/'sources.tar.gz';source_paths=self.freeze_sources(snapshot)
        config={'codex_bin':str(receiver),'codex_home':str(self.root/'target/home'),'role_card':str(self.root/'target/role.md'),
                'role_card_revision':'09C-rehearsal','code_revision':revision,'source_snapshot':str(snapshot),
                'hook_authorization':'Main #355 deterministic rehearsal; no vendor executable','turn_limit':10}
        save(self.root/'launch-config.json',config);apis=[]
        for role in ['ideation','executor']:
            folder=self.root/'roles'/role;folder.mkdir(parents=True)
            argv=[sys.executable,'-B',TESTS/'t078_09b_fake_api.py','--root',folder,'--role',role,'--protocol']
            child=self.spawn(role+'-api',argv);wait_for('api-ready',lambda:(folder/'api-ready.json').is_file())
            ready=json.loads((folder/'api-ready.json').read_bytes())
            require(ready['pid']==child.pid and ready['role']==role and ready['stage']=='A' and ready['model_turns']==0 and
                    ready['protocol']=='rev2-raw-c-profile-v1' and ready['fixture_profile']=='rev2-registered-raw-v1','actual API profile',ready)
            apis.append({'role':role,'pid':child.pid,'argv':list(map(str,argv)),'ready':ready})
        self.host=self.spawn('daemon',[NODE,TESTS/'t078_09b_rehearsal_host.ts',self.root,self.root/'launch-config.json',STRUCTURE])
        wait_for('daemon-ready',lambda:(self.root/'host-ready.json').is_file())
        task='t078-c-rehearsal-'+uuid.uuid4().hex[:8]
        card={'id':task,'source':None,'goal':'09C real relay rehearsal','non_goals':['vendor model','candidate submission'],
              'paths':{'allow':['value.txt'],'deny':[]},'oracle_paths':['oracle/contract.json'],
              'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c',"raise SystemExit('no candidate')"]}],
              'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L',
              'executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        save(self.root/'card.json',card)
        self.gate('card_save','--task',task,'--card',self.root/'card.json','--expected-version','0')
        self.gate('create','--task',task,'--repo',self.root/'repo','--branch','refs/heads/main','--card-version','1','--project','t078-c-rehearsal')
        claim=self.gate('dispatch','--task',task,'--runtime-mode','workspace-write')['attempt']
        require(all(claim.get(k) for k in ['task_id','attempt_id','session_id','fence','thread_id','workspace']),'actual claimed target',claim)
        wait_for('target-received',lambda:(self.root/'target/home/received.bin').is_file())
        target=wait_for('target-leader',lambda:self.target_info(claim['thread_id']))
        self.request_dir=Path(next(json.loads(r['data'])['request_dir'] for r in self.rows('launch_records') if json.loads(r['data']).get('role')=='worker'))
        original_processes={}
        for label,pid in [('daemon',self.host.pid),('target_shell',target['shell_pid']),('target_leader',target['leader'])]+[(a['role']+'_api',a['pid']) for a in apis]:
            first=process_command(pid);require(first is not None and process_command(pid)==first,'original Stage A process identity',label)
            original_processes[label]=first
        for api in apis:api['lstart']=original_processes[api['role']+'_api']['started']
        self.ready={'status':'READY_FOR_APPROVAL','stage':'A','root':str(self.root),'task':task,'scene':'09C','source_revision':revision,'original_processes':original_processes,
                    'target_binding':claim,'target_process':target,'api_processes':apis,'daemon':{'pid':self.host.pid,'root':str(self.state)}}
        self.stage_a=self.output/'stage-a';self.stage_a.mkdir();save(self.stage_a/'readiness.json',self.ready)
        save(self.stage_a/'result.json',{'status':'READY_FOR_APPROVAL','stage':'A','root':str(self.root),'attempt':claim})
        self.packet=self.output/'packet';self.packet.mkdir()
        static={'scene':'09C','revision':revision,'protocol':True}
        if source_paths is not None:static['source_paths']=source_paths
        save(self.packet/'static-check.json',static)
        save(self.packet/'plan.json',{'roles':{'ideation':{'root_budget':4},'executor':{'root_budget':1}}})
        shutil.copyfile(snapshot,self.packet/'sources.tar.gz')
        for role in ['ideation','executor']:
            p1=self.output/(role+'-p1')
            self.command([sys.executable,'-B',BASE/'prepare-a14.py','--mode','role','--instance','c355','--role',role,
                '--prompt-file',BASE/'09c-materials-01/i1-prompt.txt','--stage-a',self.stage_a,'--packet',self.packet,'--output',p1])
            inp=json.loads((p1/'input.json').read_bytes());api=next(a for a in apis if a['role']==role)
            save(p1/'runtime-input.json',{**inp,'api_url':api['ready']['api_url']})
            # Same B1 receipt/approval and P1 launch-prefix checks. The only
            # replaced boundary below is the vendor executable in node-pty.
            import importlib.util
            spec=importlib.util.spec_from_file_location('rehearsal_stage_b',BASE/'run-09b-stage-b.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            binding=module.read_stage_a_binding(self.stage_a)
            approval=json.loads((p1/'stage-b-approval.json').read_bytes())
            approval.update(approved_by='executor',approval_ref=self.signature)
            module.validate_role_approval(approval,binding,self.packet,role,'B1')
            save(p1/'rehearsal-B1-approval.json',approval)
            self.command([sys.executable,'-B',TESTS/'run_t078_p1.py','--materials',p1,'--phase','launch',
                '--label','rehearsal-launch-prefix','--reuse-stage-a','--reuse-api-root',self.root/'roles'/role,
                '--reuse-readiness-file',self.stage_a/'readiness.json','--stop-before-cli'])
            require(json.loads((p1/'rehearsal-launch-prefix/result.json').read_bytes())['stop_before_cli'] is True,'real P1 prefix gate')
            self.gate('controller_start','--task',task,'--manifest',p1/'runtime-input.json')
            wait_for('actual peer ready',lambda:(self.root/'peer'/role/'ready.json').is_file())
            save(p1/'readiness.json',{'launch':inp['launch'],'session':inp['session'],'confirmed_by':'executor','readiness':'confirmed',
                 'basis':'Deterministic empty PTY peer; not Claude onboarding evidence'})
            self.p1s[role]=p1;self.inputs[role]=inp
        self.bind_owner()
        slot='t078-C355-'+uuid.uuid4().hex
        self.build=Path(json.loads(self.command(['node',SOURCE/'workbench/app/build.mjs','--slot',slot],timeout=120).strip().splitlines()[-1])['out'])
        for stage in ['C-I1','C-E1','C-I2','C-I3','C-I4']:
            self.approve(self.p1s['executor' if stage=='C-E1' else 'ideation'],stage)
            self.phase_c(stage,'arm','armed-01')

    def bind_owner(self):
        # Same owner producer and validator as live scenes; nine real lifetimes.
        # The manifest explicitly names Python, never a fictional Claude PID.
        from p1_processes import identity_from_ps
        for role,inp in self.inputs.items():
            p1=self.p1s[role];peer=json.loads((self.root/'peer'/role/'ready.json').read_bytes())
            info=self.gate('pane_process_info','--thread',inp['thread'])
            identities=[]
            for _ in range(2):
                result=subprocess.run(['/bin/ps','-p',str(peer['pid']),'-o','pid=,lstart=,comm='],
                    env={**self.env,'LC_ALL':'C','LANG':'C'},capture_output=True,text=True,timeout=5)
                identities.append(identity_from_ps(peer['pid'],result.returncode,result.stdout,result.stderr))
            require(identities[0] is not None and identities[0]==identities[1],'stable real peer lifetime')
            require(info['leader']==peer['pid'] and info['shell_pid']!=peer['pid'] and peer['ppid']==info['shell_pid'],'real shell parent distinct from peer')
            launch=p1/'rehearsal-launch';launch.mkdir()
            save(launch/'process-manifest.json',{'launch':inp['launch'],'session':inp['session'],
                'shell_pid':info['shell_pid'],'cli':identities[0],'provider_kind':'deterministic Python PTY peer'})
            save(p1/'launch-binding.json',{'launch_label':launch.name,'process_manifest':str(launch/'process-manifest.json')})
        owner_file=self.root/'raw-owner.json'
        self.command([sys.executable,'-B',BASE/'prepare-rev2-owner.py','--mode','owner','--stage-a',self.stage_a,
            '--packet',self.packet,'--ideation',self.p1s['ideation'],'--executor',self.p1s['executor'],'--output',owner_file])
        owner=json.loads(owner_file.read_bytes())
        check_identities(owner,NativeRuntime(owner))
        plan=json.loads((self.root/'protocol-plan.json').read_bytes());self.target_identity=plan['target_identity']
        save(self.output/'identity-seam.json',{'scope':'nine real processes; common original receipts and topology gate; Python provider, not Claude',
            'owner_file':str(owner_file),'processes':owner['processes'],'process_graph':owner['process_graph']})

    def phase_c(self,stage,mode,label,spawn=False):
        p1=self.p1s['executor' if stage=='C-E1' else 'ideation'];folder=p1/'phases'/stage
        argv=[sys.executable,'-B',TESTS/'t078_09c_driver.py','--plan',self.root/'protocol-plan.json','--stage',stage,
              '--approval',folder/'approval.json','--mode',mode,'--output',folder/label]
        if mode=='permission':argv+=['--build',self.build]
        if spawn:return self.spawn('conditional-driver',argv)
        self.command(argv,timeout=45)
        result=folder/label/'result.json';value=json.loads(result.read_bytes())
        expected={'arm':'ARMED','initialize':'INITIALIZED','start':'DISPATCHED','observe':'READY_FOR_PERMISSION','collect':'PASS'}[mode]
        require(value['status']==expected,'exact stage result: '+stage+'/'+mode,value['status'],expected)
        return result

    def review_permission(self,inp,stage):
        number=0
        def observe():
            nonlocal number
            events=[e for e in self.events() if e['launch']==inp['launch'] and e['type']=='permission_wait'
                    and e['seq']>getattr(self,'last_permission',0)]
            if not events:return None
            event=events[-1];command=event['data']['tool_input']['command']
            observed=read_complete_output(lambda offset:self.gate('pane_output','--launch',inp['launch'],'--offset',str(offset)),inp['launch'])
            raw=observed['raw'];number+=1
            path=self.output/f'{stage}-review-screen-{number:02d}.bin'
            with path.open('xb') as stream:stream.write(raw)
            save(path.with_suffix('.json'),{'permission_event':event,'command':command,'screen_capture':observed['capture']})
            terminal=raw.decode('utf-8');box=terminal.rsplit('Run shell command',1)
            if len(box)!=2 or 'This command requires approval' not in box[1] or '❯ 1. Yes' not in box[1]:return None
            if visible_command(terminal)!=command:raise ValueError('rehearsal_permission_command_mismatch')
            return str(path)
        return wait_for(stage+'_actual_permission_display',observe,seconds=15)

    def permission(self,stage):
        inp=self.inputs['ideation'];p1=self.p1s['ideation'];folder=p1/'phases'/stage
        wait_for(stage+' real PermissionRequest',lambda:any(e['type']=='permission_wait' and e['data'].get('tool_input',{}).get('command') for e in self.events() if e['launch']==inp['launch'] and e['seq']>getattr(self,'last_permission',0)))
        self.review_permission(inp,stage)
        path=self.phase_c(stage,'observe','dispatch-01');dispatch=json.loads(path.read_bytes())
        self.last_permission=dispatch['permission_event']['seq']
        permitted=folder/'permission.json'
        self.command([sys.executable,'-B',BASE/'prepare-a14.py','--mode','permission','--p1',p1,'--result',path,'--output',permitted])
        approval=json.loads(permitted.read_bytes());approval.update(approved_by='executor',approval_ref='Main #355 deterministic scratch '+stage)
        permitted.write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if stage=='C-I2':
            stop=self.original_stop();age=time.time()*1000-__import__('t078_09c_driver').created_ms(stop['created_at'])
            require(age<90000,'early stage must have >=30s headroom before any Enter',age)
        manifest=p1/'actual-peer-manifest.json'
        if not manifest.exists():
            peer=json.loads((self.root/'peer/ideation/ready.json').read_bytes())
            identity=process_command(peer['pid']);require(identity is not None,'actual peer lifetime')
            save(manifest,{'launch':inp['launch'],'session':inp['session'],'cli':identity,
                          'scope':'deterministic real PTY replacement; no separate Claude shell'})
        self.command([sys.executable,'-B',TESTS/'t078_09b_i1_permission.py','--materials',p1,'--p1',p1,'--stage',stage,
             '--stage-a',self.stage_a,'--dispatch-result',path,'--process-manifest',manifest,'--approval',permitted,'--output',folder/'execute-02'],timeout=90)
        result=json.loads((folder/'execute-02/result.json').read_bytes());require(result['status']=='PASS',stage+' actual settlement',result)
        return result

    def original_stop(self):
        entries=[json.loads(r['data']) for r in self.rows('inbox_records') if json.loads(r['data']).get('kind')=='stop']
        require(len(entries)==1,'one original stop',entries);return entries[0]

    def flow(self):
        print(json.dumps({'stage':'setup','status':'RUNNING','model_turns':0}),flush=True)
        self.setup();self.phase_c('C-I1','initialize','initialized-01')
        first=self.phase_c('C-I1','start','start-01');require(json.loads(first.read_bytes())['status']=='DISPATCHED','start succeeds after initialize')
        control_segment_mono=time.monotonic()
        sent=self.permission('C-I1');stop=sent['stop']
        self.command([sys.executable,'-B',BASE/'prepare-rev2-owner.py','--mode','demand','--result',self.p1s['ideation']/'phases/C-I1/execute-02/settlement.json',
              '--approval',self.p1s['ideation']/'phases/C-I1/approval.json','--output',self.root/'continued-demand.json'])
        early=self.permission('C-I2');require(early['relay_receipt']['error']=='stop_too_early','actual early gate denial')
        inp=self.inputs['ideation'];folder=self.p1s['ideation']/'phases/C-I3'
        wait_for('C-I3 PermissionRequest',lambda:any(e['type']=='permission_wait' and e['seq']>self.last_permission for e in self.events() if e['launch']==inp['launch']))
        self.review_permission(inp,'C-I3');observed_path=self.phase_c('C-I3','observe','dispatch-01')
        observed=json.loads(observed_path.read_bytes())
        child=self.phase_c('C-I3','permission','execute-02',spawn=True)
        review=folder/'execute-02-review'
        wait_for('actual window template',lambda:(review/'template.json').is_file(),seconds=30)
        template=json.loads((review/'template.json').read_bytes())
        require(template['binding']['stop']['id']==stop['id'] and template['binding']['stop']['created_at']==stop['created_at'],'actual template stop')
        require(template['binding']['stop']['request_id']==json.loads((self.root/'clock-origin.json').read_bytes())['stop']['request_id'],'actual template original request/key')
        require(template['binding']['target']==self.target_identity,'all actual target fields bound')
        expected_argv=[str(NODE),str(CLI),'stop','--thread',self.ready['target_binding']['thread_id'],'--stop-id',stop['id']]
        require(template['binding']['argv']==expected_argv and template['binding']['command']==shlex.join(expected_argv),'independent full command oracle')
        require(all(template['binding'][k]==v for k,v in [('source_revision',self.ready['source_revision']),('package',str(self.packet)),
                ('launch',inp['launch']),('session',inp['session']),('thread',inp['thread']),('dispatch',observed['dispatch']['id']),
                ('global_seq',observed['dispatch']['seq']),('tool_use_id',observed['dispatch']['tool_use']['id']),
                ('prompt_id',observed['permission_event']['data']['prompt_id']),('permission_seq',observed['permission_event']['seq'])]),'actual source/native/permission tuple')
        require(template['key']=='Enter' and template['selected_line']=='❯ 1. Yes' and template['max_writes']==1,'one-time template')
        original=(review/'screen.bin').read_bytes();validate_capture(original,template['screen_capture'])
        current=read_complete_output(lambda offset:self.gate('pane_output','--launch',inp['launch'],'--offset',str(offset)),inp['launch'])
        require(current['raw']==original==Path(observed['permission_screen']).read_bytes(),'independent complete screen equality')
        template.update(approved_by='executor',approval_ref='Main #355 approved deterministic scratch actual template')
        pending=review/'signed.tmp';save(pending,template);os.link(pending,review/'approved.json')
        print(json.dumps({'stage':'C-I3','status':'WAITING_REAL_CLOCK','stop_created_at':stop['created_at'],
                          'expected_wall_age_ms':'>120000 and <150000','model_turns':0}),flush=True)
        remaining=150-(time.time()*1000-__import__('t078_09c_driver').created_ms(stop['created_at']))/1000
        child.wait(timeout=max(1,remaining));require(child.returncode==0,'conditional driver exit',child.returncode)
        late=json.loads((folder/'execute-02/result.json').read_bytes())
        require(late['status']=='PASS' and late['enter_at']['wall_age_ms']>120000 and late['enter_at']['wall_age_ms']<130000 and
                late['enter_at']['observed_elapsed_ms']>=120100,'actual late Enter threshold',late)
        self.phase_c('C-I4','collect','collect-01');self.phase_c('C-E1','collect','collect-01')
        return self.readback(stop,early,late,control_segment_mono)

    def readback(self,stop,early,late,control_segment_mono):
        posts=self.counts();require(posts=={'ideation':7,'executor':1},'actual HTTP POST budget',posts)
        per_stage={}
        for role in ['ideation','executor']:
            for path in (self.root/'roles'/role/'http-exchanges').glob('*.meta.json'):
                meta=json.loads(path.read_bytes());prefix=path.name.removesuffix('.meta.json')
                request=path.with_name(prefix+'.request.bin').read_bytes();response=path.with_name(prefix+'.response.bin').read_bytes()
                require(meta['status']==200 and meta['complete'] and len(request)==meta['request_bytes'] and
                        len(response)==meta['response_bytes']==meta['wire_bytes_confirmed'],'complete original HTTP bytes',meta)
            for line in (self.root/'roles'/role/'requests.ndjson').read_bytes().splitlines():
                row=json.loads(line);require(not row.get('error'),'no HTTP errors',row.get('error'))
                per_stage[row['phase']]=per_stage.get(row['phase'],0)+1
        require(per_stage=={'C-I1':2,'C-I2':2,'C-I3':2,'C-I4':1,'C-E1':1},'phase POST counts',per_stage)
        roots={r:sum(e['type']=='turn_submitted' and e['launch']==i['launch'] for e in self.events()) for r,i in self.inputs.items()}
        require(roots=={'ideation':4,'executor':1},'actual roots',roots)
        require(self.original_stop()['created_at']==stop['created_at'],'created_at unchanged')
        require((self.root/'target/home/received.bin').read_bytes()==(self.root/'target-baseline.bin').read_bytes()+b'\x1b','one target Esc')
        require(not any(json.loads(row['data']).get('kind')=='ack' for row in self.rows('inbox_records')),'no ack')
        current=self.gate('status','--task',self.ready['task'])['task']['current_attempt']
        require(isinstance(current,dict) and all(current.get(k)==self.ready['target_binding'][k] for k in
                ['attempt_id','session_id','fence','spec_rev','thread_id','workspace']),'original attempt remains claimed',current)
        target=self.gate('pane_process_info','--thread',self.ready['target_binding']['thread_id'])
        require(target['shell_pid']==self.ready['target_process']['shell_pid'] and target['leader']==self.ready['target_process']['leader'] and
                not target.get('session_ended') and not target.get('failed'),'target alive; no reclaim or kill',target)
        with closing(sqlite3.connect((self.state/'state.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
            db.row_factory=sqlite3.Row
            actual=[dict(row) for row in db.execute("SELECT * FROM events WHERE type='emergency_interrupt_requested'")]
        require(len(actual)==1,'one real emergency event',actual)
        details=json.loads(actual[0]['details'])
        require(details['actor']=='ideation' and details['thread']==self.ready['target_binding']['thread_id'] and details['stop_id']==stop['id'],
                'independent caller/target/stop oracle',details)
        actual_age=(datetime.fromisoformat(actual[0]['time'].replace('Z','+00:00'))-datetime.fromisoformat(stop['created_at'].replace('Z','+00:00'))).total_seconds()*1000
        require(120000<actual_age<150000,'independent daemon event age',actual_age)
        control_events=[event for event in self.events() if event['type']=='terminal_input_write_intent' and event['data'].get('data')=='\r']
        permissions=[event for event in self.events() if event['type']=='permission_wait']
        require(len(control_events)==len(permissions)==3,'three native one-time approvals',{'keys':len(control_events),'permissions':len(permissions)})
        control_elapsed=time.monotonic()-control_segment_mono
        require(control_elapsed>120,'independent real control-segment monotonic elapsed')
        elapsed=time.time()*1000-__import__('t078_09c_driver').created_ms(stop['created_at'])
        require(120000<elapsed<150000,'real scene time boundary',elapsed)
        save(self.output/'flow-readback.json',{'status':'PASS','stop':stop,'POST':posts,'per_stage':per_stage,'roots':roots,
             'early':early,'late':late,'scene_age_ms':elapsed,'independent_emergency_age_ms':actual_age,
             'independent_control_segment_seconds':control_elapsed,'actual_emergency':actual,
             'control_events':control_events,'permissions':permissions,'model_turns':0,'target_delta_hex':'1b','no_ack':True})
        return {'status':'PASS','POST':posts,'roots':roots,'scene_age_ms':elapsed,'model_turns':0}

    def cleanup(self):
        import t078_raw_retention as raw
        owner_file=self.root/'raw-owner.json'
        require(owner_file.is_file(),'owner must bind before standard cleanup; retain incomplete setup')
        owner=raw.read_json(owner_file)
        coordinator=self.output/'coordinator-01'
        if coordinator.is_dir():owner={**owner,'evidence_trees':owner['evidence_trees']+[str(coordinator)]}
        # Save committed WAL consistently while the daemon is still alive.
        database=self.output/'sqlite';database.mkdir()
        with closing(sqlite3.connect((self.state/'state.sqlite3').as_uri()+'?mode=ro',uri=True)) as src:
            with closing(sqlite3.connect(database/'state.sqlite3')) as dst:src.backup(dst)
        with closing(sqlite3.connect(database/'state.sqlite3')) as db:require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite backup integrity')
        clock=self.root/'clock-origin.json'
        if clock.exists():
            with (self.output/'clock-origin.json').open('xb') as stream:stream.write(clock.read_bytes())
        raw.check_identities(owner,raw.NativeRuntime(owner))
        staging=self.output/'retention-staging';raw.capture(owner,staging)
        archive=self.output/'retention-archive/scene.tar.gz'
        captured=raw.archive_capture(owner,staging,archive);counts=raw.readback(archive)
        raw.save(self.output/'retention-readback.json',{'archive':str(archive),'counts':counts,'scope':'deterministic rehearsal independent tar recount'})
        approval={k:owner[k] for k in ['root','scene','source_revision','target_binding','processes']}
        approval.update(approved_by='executor',approval_ref='REHEARSAL ONLY owner-bound capture/readback before stop',
            archive=str(archive),retain_failed_scene=True)
        raw.save(self.output/'cleanup-approval.json',approval)
        independent={'approved_by':'executor','approval_ref':'REHEARSAL ONLY independent tar recount',
            'archive':str(archive),'counts':counts}
        result=raw.finish(owner,approval,captured,independent,self.output/'cleanup-standard',raw.NativeRuntime(owner))
        require(result['status']=='PASS' and result['root_removed'],'standard archive/readback/finish',result)
        for child in self.children:
            child['child'].wait(timeout=5)
        details={**result,'scratch_removed':True,'SQLite_backup':'live consistent backup includes WAL; integrity ok',
            'scope':'same raw owner/identity/topology/capture/readback/finish gates as live scenes'}
        save(self.output/'cleanup.json',details);return details


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    try:checked=preflight();save(out/'preflight.json',checked)
    except Exception as error:
        save(out/'result.json',{'status':'INCOMPLETE','stage':'preflight','error':repr(error),'traceback':traceback.format_exc(),'scene_process_starts':0})
        return 1
    if args.check_only:print(json.dumps(checked));return 0
    dirty=subprocess.check_output(['git','status','--porcelain=v1','--','workbench','acceptance','scripts'],cwd=SOURCE,text=True)
    if dirty.strip():
        save(out/'result.json',{'status':'INCOMPLETE','stage':'source-preflight','error':'Commit the harness before the real rehearsal',
                               'dirty_paths':dirty.splitlines(),'scene_process_starts':0})
        return 1
    result={'status':'INCOMPLETE','scope':__doc__,'real_model_turns':0,'vendor_CLIs':0,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()}
    def hard(*_):raise TimeoutError('09C_rehearsal_hard_timeout_420s')
    previous=signal.signal(signal.SIGALRM,hard);signal.alarm(420);scene=CScene(out/'flow')
    try:result.update(scene.flow())
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        try:result['cleanup']=scene.cleanup()
        except Exception as error:result.update(status='INCOMPLETE',cleanup_error=repr(error),cleanup_traceback=traceback.format_exc())
        save(out/'result.json',result)
    print(json.dumps({k:result[k] for k in ['status','POST','scene_age_ms','error','cleanup_error'] if k in result}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
