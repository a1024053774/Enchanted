"""Prepare or observe one isolated real-Claude topology probe; never press permission Enter."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback
import uuid

from test_t078_a14_rehearsal import Scene, save, require, wait_for, NODE, CLI
from test_t078_09c_coordinator_chain import CoordinatorScene
from p1_reuse import process_command
from p1_output import read_complete_output
from t078_process_tree import snapshot

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
TESTS=SOURCE/'workbench/tests'


class Probe(Scene):
    freeze_sources=CoordinatorScene.freeze_sources

    def setup(self,approval):
        revision=approval['source_revision']
        require(not subprocess.check_output(['git','status','--porcelain','--','workbench','acceptance','scripts'],cwd=SOURCE),
                'probe runtime must be committed before setup')
        (self.root/'repo/value.txt').write_text('T078 topology observation only\n',encoding='utf-8')
        (self.root/'repo/oracle/contract.json').write_text('{"models":0}\n',encoding='utf-8')
        for args in [['init','-b','main'],['add','value.txt','oracle/contract.json'],['commit','-m','isolated topology fixture']]:
            self.command(['git','-C',self.root/'repo',*args])
        receiver=self.root/'target/bin/codex-receiver'
        self.command(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',TESTS/'t078_native_receiver.c','-o',receiver])
        (self.root/'target/role.md').write_text('Deterministic topology target; no model.\n',encoding='utf-8')
        packet=self.output/'packet';packet.mkdir();names=self.freeze_sources(packet/'sources.tar.gz')
        save(packet/'static-check.json',{'scene':'09B','revision':revision,'protocol':True,'source_paths':names,
            'scope':'topology experiment only, not an acceptance Stage A regression waiver'})
        save(packet/'plan.json',{'roles':{'ideation':{'root_budget':1},'executor':{'root_budget':1}}})
        config={'codex_bin':str(receiver),'codex_home':str(self.root/'target/home'),'role_card':str(self.root/'target/role.md'),
            'role_card_revision':'T078-topology-probe','code_revision':revision,'source_snapshot':str(packet/'sources.tar.gz'),
            'hook_authorization':'main #365 isolated topology observation; no real model','turn_limit':10}
        save(self.root/'launch-config.json',config)
        apis=[]
        for role in ['ideation','executor']:
            folder=self.root/'roles'/role;folder.mkdir(parents=True)
            argv=[sys.executable,'-B',TESTS/'t078_09b_fake_api.py','--root',folder,'--role',role,'--protocol']
            child=self.spawn(role+'-api',argv);wait_for('API ready '+role,lambda:(folder/'api-ready.json').is_file())
            ready=json.loads((folder/'api-ready.json').read_bytes());require(ready['pid']==child.pid,'actual API PID')
            apis.append({'role':role,'pid':child.pid,'argv':list(map(str,argv)),'ready':ready})
        daemon=self.gate('daemon_start','--launch-config',self.root/'launch-config.json')
        task='t078-topology-'+uuid.uuid4().hex[:8]
        card={'id':task,'source':None,'goal':'Observe real Claude child processes','non_goals':['model call','execute inbox tool'],
            'paths':{'allow':['value.txt'],'deny':[]},'oracle_paths':['oracle/contract.json'],
            'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c',"raise SystemExit('no candidate')"]}],
            'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L',
            'executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        save(self.root/'card.json',card);self.gate('card_save','--task',task,'--card',self.root/'card.json','--expected-version','0')
        self.gate('create','--task',task,'--repo',self.root/'repo','--branch','refs/heads/main','--card-version','1','--project','t078-topology')
        claim=self.gate('dispatch','--task',task,'--runtime-mode','workspace-write')['attempt']
        target=wait_for('actual native target',lambda:self.target_info(claim['thread_id']))
        original={}
        for label,pid in [('daemon',daemon['pid']),('target_shell',target['shell_pid']),('target_leader',target['leader'])]+[(a['role']+'_api',a['pid']) for a in apis]:
            first=process_command(pid);require(first is not None and process_command(pid)==first,'actual original process',label);original[label]=first
        for api in apis:api['lstart']=original[api['role']+'_api']['started']
        stage=self.output/'stage-a';stage.mkdir()
        ready={'status':'READY_FOR_APPROVAL','stage':'A','root':str(self.root),'scene':'09B','task':task,
            'source_revision':revision,'target_binding':claim,'target_process':target,'api_processes':apis,
            'daemon':daemon,'original_processes':original}
        save(stage/'readiness.json',ready);save(stage/'result.json',{'status':'READY_FOR_APPROVAL','stage':'A','root':str(self.root),'attempt':claim})
        prompt=self.output/'prompt.txt';prompt.write_text('Approved test-simulated-user topology probe: request the isolated target to stop. Wait for a separately approved Bash permission.\n',encoding='utf-8')
        p1=self.output/'ideation-p1'
        self.command([sys.executable,'-B',BASE/'prepare-a14.py','--mode','role','--instance','a365','--role','ideation',
            '--stage-a',stage,'--packet',packet,'--prompt-file',prompt,'--output',p1])
        registry=self.root/'roles/ideation/protocol-registry.json'
        registered=json.loads(registry.read_bytes());registered['message_budget']=1
        registry.write_text(json.dumps(registered,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        save(self.output/'probe.json',{'status':'PREPARED','root':str(self.root),'stage_a':str(stage),'packet':str(packet),'p1':str(p1),
            'source_revision':revision,'original_processes':original,'root_budget':1,'POST_budget':1,'model_turns':0,
            'scope':'one real Claude role; target is deterministic; do not press permission Enter; retain root for reviewed cleanup'})
        save(self.output/'turn-approval-template.json',{'approved_by':None,'approval_ref':None,'root':str(self.root),
            'source_revision':revision,'max_roots':1,'max_POST':1,'permission_Enter_allowed':False,
            'scope':'main #365 topology experiment only; not 09C acceptance or permission execution'})
        return {'status':'PREPARED','root':str(self.root),'p1':str(p1),'role_CLIs_started':0}


def gate(root,command,*args):
    from t078_09b_i1_driver import gate as call
    return call(root,command,*args)


def load_probe(directory):
    data=json.loads((directory/'probe.json').read_bytes());root=Path(data['root'])
    require(root.parent==Path('/private/tmp') and root.name.startswith('t078-2-a14-rehearsal-'),'probe-owned root')
    require(root!=Path('/private/tmp/t078-2-09c-run-iznfrv18'),'never touch attempt 2')
    for label,expected in data['original_processes'].items():
        require(process_command(expected['pid'])==expected and process_command(expected['pid'])==expected,'probe original process changed',label)
    p1=Path(data['p1']);inp=json.loads((p1/'input.json').read_bytes())
    binding=json.loads((p1/'launch-binding.json').read_bytes());manifest=json.loads(Path(binding['process_manifest']).read_bytes())
    processes={**data['original_processes']}
    for label,pid in [('ideation_shell',manifest['shell_pid']),('ideation_cli',manifest['cli']['pid'])]:
        first=process_command(pid);require(first is not None and process_command(pid)==first,'probe role lifetime');processes[label]=first
    require(manifest['launch']==inp['launch'] and manifest['session']==inp['session'],'probe launch/session')
    return data,root,p1,inp,{'root':str(root),'processes':processes}


def sample_for(owner,output,seconds):
    start=time.monotonic();index=0;history={};count=0;previous=set();partial=[]
    while time.monotonic()-start<seconds:
        index+=1;item=snapshot(owner,output/f'sample-{index:04d}')
        require('error' not in item and item['missing']==[],'process sampling transport/core failed',item)
        for expected in owner['processes'].values():
            row=item['processes'].get(str(expected['pid']),{})
            require(row.get('lstart')==expected['started'] and row.get('command')==expected['command'],
                'original probe process identity changed',expected['pid'])
        if item['status']!='PASS':partial.append(index)
        for pid,row in item['processes'].items():
            if 'command' not in row:continue  # Raw graph/vanish receipt kept; no identity is inferred.
            entry=history.setdefault(pid,{'first_observed_at':row['observed_at'],'last_observed_at':row['observed_at'],
                'name':row['name'],'command':row['command'],'lstart':row['lstart'],'parent_chain':row['parent_chain'],
                'creator_evidence':row['creator_evidence'],'appearance_observations':[], 'absence_observations':[],
                'role_cli_descendant':owner['processes']['ideation_cli']['pid'] in row['parent_chain'][1:]})
            require(entry['command']==row['command'] and entry['lstart']==row['lstart'],'PID changed during probe',pid)
            entry['last_observed_at']=row['observed_at']
            if pid not in previous:entry['appearance_observations'].append(row['observed_at'])
        identified={pid for pid,row in item['processes'].items() if 'command' in row}
        for pid in previous-identified:history[pid]['absence_observations'].append(item['observed_at'])
        previous=identified
        count=index;time.sleep(.1)
    save(output/'summary.json',{'status':'PASS','samples':count,'observed_duration_seconds':time.monotonic()-start,
        'process_lifetimes_observed':history,'scope':'sampling first/last observations bound lifetimes; not exact fork/exit timestamps',
        'partial_identity_samples':partial,'classification':'UNKNOWN until main reviews original graph/argv/logs','key_writes':0,
        'capture_complete':not partial})


def observe(args):
    data,root,p1,inp,owner=load_probe(args.probe)
    out=args.output
    if args.mode=='idle':
        screen=read_complete_output(lambda offset:gate(root,'pane_output','--launch',inp['launch'],'--offset',offset),inp['launch'])
        text=screen['raw'].decode('utf-8')
        require('manual mode on' in text and '❯' in text,'complete manual empty-prompt screen required')
        require(not list((root/'roles/ideation/http-exchanges').glob('*.request.bin')),'idle zero POST')
        (out/'screen.bin').write_bytes(screen['raw']);save(out/'screen-capture.json',screen['capture'])
        save(args.probe/'probe-original-role.json',owner)
        sample_for(owner,out,10)
        save(args.probe/'idle-observation.json',{'output':str(out)})
        return {'status':'PASS','stage':'idle','Messages_POST':0}
    require(args.mode=='turn' and args.approval,'signed turn approval required')
    consent=json.loads(args.approval.read_bytes())
    for key in ['root','source_revision']:require(consent.get(key)==data[key],'probe approval changed:'+key)
    require(consent.get('approved_by')=='executor' and consent.get('approval_ref') and consent.get('max_roots')==1 and
        consent.get('max_POST')==1 and consent.get('permission_Enter_allowed') is False,'explicit probe limits')
    require(owner==json.loads((args.probe/'probe-original-role.json').read_bytes()),'original role binding changed')
    # Exclusive journal is durable before release/dispatch; no retry under a new output.
    save(args.probe/'turn-intent.json',{'approval_ref':consent['approval_ref'],'launch':inp['launch'],'root':str(root)})
    plan=json.loads((root/'protocol-plan.json').read_bytes())
    save(root/'roles/ideation/stop-body.txt',{'source':'test-simulated-user','action_id':plan['synthetic_input_id'],
        'approval_ref':consent['approval_ref'],'scope':'isolated topology observation; tool must not execute'})
    gate(root,'pane_release','--thread',inp['thread'],'--reason',consent['approval_ref'])
    dispatch=gate(root,'pane_dispatch','--thread',inp['thread'],'--body-file',args.probe/'prompt.txt')
    save(out/'dispatch.json',dispatch)
    waiting=root/'roles/ideation/waiting-phase.json'
    wait_for('actual held POST',lambda:waiting.is_file(),seconds=15)
    wait=json.loads(waiting.read_bytes());require(wait['stage']=='I1' and wait['dispatch']['id']==dispatch['dispatch']['id'],'held actual registered dispatch')
    busy=out/'in-flight';busy.mkdir();sample_for(owner,busy,15)
    # Release one existing HTTP response using the same stage-approval barrier
    # as 09C. No alternate API/response generator and no second request.
    draft=json.loads((p1/'phases/I1/approval.json').read_bytes());draft.update(approved_by='executor',approval_ref=consent['approval_ref'])
    from t078_09b_phase_registry import validate_phase_approval
    validate_phase_approval(draft,json.loads((root/'protocol-plan.json').read_bytes()),'ideation','I1')
    target=Path(wait['approval_file']);target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix('.pending');save(temporary,draft)
    import os
    os.link(temporary,target);temporary.unlink()
    def permission():
        from t078_09b_phase_registry import rows
        events=[r for r in rows(root,'orchestration_events') if r['launch']==inp['launch'] and r['type']=='permission_wait']
        return events[-1] if events else None
    event=wait_for('actual PermissionRequest',permission,seconds=20);save(out/'permission-event.json',event)
    screen=read_complete_output(lambda offset:gate(root,'pane_output','--launch',inp['launch'],'--offset',offset),inp['launch'])
    expected=json.loads(event['data'])['tool_input']['command']
    require(bool(expected),'actual Bash PermissionRequest command')
    (out/'permission-screen.bin').write_bytes(screen['raw']);save(out/'permission-capture.json',screen['capture'])
    pending=out/'permission-wait';pending.mkdir();sample_for(owner,pending,15)
    after=read_complete_output(lambda offset:gate(root,'pane_output','--launch',inp['launch'],'--offset',offset),inp['launch'])
    (out/'permission-screen-after-sampling.bin').write_bytes(after['raw']);save(out/'permission-capture-after-sampling.json',after['capture'])
    status=gate(root,'pane_status','--thread',inp['thread'])
    require(status['active'] and status['active']['id']==dispatch['dispatch']['id'] and status['state']=='busy',
        'same actual dispatch remains active at PermissionRequest')
    save(out/'permission-pane-status.json',status)
    idle=Path(json.loads((args.probe/'idle-observation.json').read_bytes())['output'])
    save(out/'three-state-index.json',{'status':'PASS','states':{'idle':str(idle),'in-flight':str(busy),'permission-wait':str(pending)},
        'classification':'UNKNOWN; assess all raw snapshots before proposing a rule','exact_birth_exit_times':'not recorded; bounded by observations and lstart',
        'Claude_launch_argv_source':str(p1/'approval.json')})
    posts=list((root/'roles/ideation/http-exchanges').glob('*.request.bin'));require(len(posts)==1,'one actual POST only',len(posts))
    require(not list((root/'roles/ideation/requests').glob('*.json')),'no tool executed')
    return {'status':'PASS','stage':'permission-wait','Messages_POST':1,'roots':1,'permission_Enter_count':0,
        'root_retained':str(root),'permission_display_review':'main must inspect saved complete raw screen against permission-event command; no key authorization inferred',
        'classification':'UNKNOWN; review sampled raw identities before any allow rule'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['setup','idle','turn'],required=True)
    p.add_argument('--probe',type=Path);p.add_argument('--approval',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.mode=='setup':
        require(a.approval is not None,'signed setup approval required')
        approval=json.loads(a.approval.read_bytes())
        require(approval.get('approved_by')=='executor' and approval.get('approval_ref') and
            approval.get('allow_role_cli_spawn') is False and approval.get('real_model_turns')==0 and
            approval.get('max_role_sessions')==1,'setup approval limits')
        revision=approval['source_revision']
        subprocess.run(['git','merge-base','--is-ancestor',revision,'HEAD'],cwd=SOURCE,check=True)
        require(not subprocess.check_output(['git','diff',revision,'--','workbench','acceptance','scripts',
            str(BASE/'prepare-a14.py'),str(BASE/'run-09b-stage-b.py')],cwd=SOURCE),'approved probe source changed')
        scene=Probe(a.output,'TOPOLOGY_PROBE',vendor_processes_allowed=True)
        def setup_deadline(*_):raise TimeoutError('topology_probe_setup_hard_timeout_180s')
        previous=signal.signal(signal.SIGALRM,setup_deadline);signal.alarm(180)
        try:result=scene.setup(approval)
        except Exception as error:
            result={'status':'INCOMPLETE','root':str(scene.root),'error':repr(error),'traceback':traceback.format_exc(),
                'signals_sent':[],'role_CLIs_started':0,'root_retained':True}
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        save(a.output/'result.json',result)
    else:
        a.output.mkdir(parents=True,exist_ok=False)
        def deadline(*_):raise TimeoutError('topology_probe_observation_hard_timeout_120s')
        previous=signal.signal(signal.SIGALRM,deadline);signal.alarm(120)
        try:result=observe(a)
        except Exception as error:
            result={'status':'INCOMPLETE','error':repr(error),'traceback':traceback.format_exc(),'permission_Enter_count':0}
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        if a.output.is_dir():save(a.output/'result.json',result)
    print(json.dumps(result,ensure_ascii=False));return 0 if result['status'] in ['PREPARED','PASS'] else 1


if __name__=='__main__':raise SystemExit(main())
