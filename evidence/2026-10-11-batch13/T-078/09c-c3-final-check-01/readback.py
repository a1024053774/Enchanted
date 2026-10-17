"""Recount actual 09C HTTP/hooks and gate rows; no runner or model invocation."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import sqlite3
import tarfile
import traceback

BASE=Path(__file__).resolve().parents[1]
OWNER=BASE/'09c-attempt-3-materials-01/owner.json'
P1=BASE/'09c-c3-b1-ideation-p1-01'
E1=BASE/'09c-c3-b1-executor-p1-01'
TIMED=BASE/'09c-c3-preparation-01/timed-01/result.json'
CONTROLS=BASE/'09c-c3-closeout-materials-01/original-control-files'
TABLES=['dispatch_records','orchestration_events','events','inbox_records','relay_requests','relay_results','user_inputs']
EXPECTED={'C-I1':('ideation',2,True),'C-I2':('ideation',2,True),'C-I3':('ideation',2,True),
          'C-I4':('ideation',1,False),'C-E1':('executor',1,False)}


def require(value, label):
    if not value:raise AssertionError(label)


def stamp(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()*1000
def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


class Reader:
    def __init__(self,owner,archive=None,task_boundary=None):
        self.owner=owner;self.root=Path(owner['root']);self.tar=None;self.archive=archive
        if archive:
            self.tar=tarfile.open(archive,'r:gz')
            try:
                members=self.tar.getmembers()
                require(len(members)==len({m.name for m in members}) and all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and
                        (m.isfile() or m.isdir()) for m in members),'safe_unique_archive_members')
                snapshot=self.json_member('snapshot.json')
                require(snapshot['root']==owner['root'] and snapshot['source_revision']==owner['source_revision'],'archive_binding')
                self.source_map={row['source']:'files/'+row['logical'] for row in snapshot['records']}
                identity=self.json_member('identity-receipts.json')
                for key in ['root','source_revision','target_binding','processes','roles','process_graph']:
                    require(identity[key]==owner[key],'archive_owner:'+key)
                self.names={name.removeprefix('files/') for name in self.tar.getnames() if name.startswith('files/')}
                self.rows=self.json_member('live-rows.json')
                require(task_boundary is not None,'explicit_task_boundary_required_for_tar')
                self.task_boundary=self.json_source(task_boundary)
            except Exception:
                self.tar.close();raise
        else:
            self.names={str(p.relative_to(self.root)) for role in ['ideation','executor']
                        for tree in ['http-exchanges','hooks'] for p in (self.root/'roles'/role/tree).rglob('*') if p.is_file()}
            with closing(sqlite3.connect((self.root/'state/state.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
                db.row_factory=sqlite3.Row;db.execute('BEGIN')
                self.rows={table:[dict(row) for row in db.execute('SELECT * FROM '+table+' ORDER BY rowid')] for table in TABLES}
                task=json.loads(db.execute('SELECT data FROM tasks WHERE id=?',(owner['target_binding']['task_id'],)).fetchone()[0])
                self.task_boundary={'source':'live read-only transaction: state/state.sqlite3#tasks',
                    'observed_at':datetime.now(timezone.utc).isoformat(),'task_id':task['task_id'],'state':task['state'],
                    'current_attempt':task['current_attempt'],'candidate_commit':task['candidate_commit'],'verification':task['verification'],
                    'integration_intent':task['integration_intent']};db.rollback()

    def close(self):
        if self.tar:self.tar.close()
    def member(self,name):
        with self.tar.extractfile(name) as f:return f.read()
    def json_member(self,name):return json.loads(self.member(name))
    def raw(self,name):
        if self.tar:return self.member('files/'+name)
        path=self.root/({'target/received.bin':self.owner['target_bytes'],'target/baseline.bin':self.owner['target_baseline']}.get(name,name))
        return path.read_bytes()
    def source(self,path):
        path=Path(path)
        if self.tar:return self.member(self.source_map[str(path)])
        return path.read_bytes()
    def json_source(self,path):return json.loads(self.source(path))


def blocks(request,kind):
    return [block for message in request['messages'] if isinstance(message.get('content'),list)
            for block in message['content'] if block.get('type')==kind]


def inspect(reader):
    o=reader.owner;rows=reader.rows
    events=[{**row,'data':json.loads(row['data'])} for row in rows['orchestration_events']]
    dispatches=[{**row,'body':json.loads(row['data'])} for row in rows['dispatch_records']]
    for row in dispatches:
        row['registered_text']=f"⟦{'门禁' if row['body']['source']=='gate' else '主控'} #{row['seq']}⟧\n"+row['body']['text']
    roots={role:sorted([d for d in dispatches if d['launch']==o['roles'][role]['launch']],key=lambda d:d['seq']) for role in ['ideation','executor']}
    require([len(roots[r]) for r in ['ideation','executor']]==[4,1],'actual_registered_roots_4_1')
    phases={d['id']:stage for stage,d in zip(['C-I1','C-I2','C-I3','C-I4'],roots['ideation'])}
    phases[roots['executor'][0]['id']]='C-E1'
    data={stage:{'dispatch':next(k for k,v in phases.items() if v==stage),'POST':[],'tools':[]} for stage in EXPECTED}
    hook_sources={};http=[];hook_counts={};permission_sources=[]
    for role in ['ideation','executor']:
        native=o['roles'][role];current=roots[role];hook_counts[role]={};prompts={}
        submits=[e for e in events if e['launch']==native['launch'] and e['type']=='turn_submitted']
        require({e['data']['dispatch'] for e in submits}=={d['id'] for d in current} and len(submits)==len(current),'one_real_submit_per_root')
        for path in sorted(n for n in reader.names if n.startswith(f'roles/{role}/hooks/') and n.endswith('/stdin.bin')):
            h=json.loads(reader.raw(path));kind=h['hook_event_name'];hook_counts[role][kind]=hook_counts[role].get(kind,0)+1
            require(h['session_id']==native['session'] and h['cwd']==str(reader.root/'repo'),'native_hook_identity')
            finished=json.loads(reader.raw(path.replace('stdin.bin','finished.json')))
            require(finished['exit_code']==0,'hook_nonzero')
            matches=[e for e in events if e['launch']==native['launch'] and e['type']=={'UserPromptSubmit':'turn_start_signal','Stop':'turn_end_signal','PermissionRequest':'permission_wait'}[kind]
                     and e['data'].get('prompt_id')==h['prompt_id']]
            require(len(matches)==1,'one_real_signal_for_hook')
            if kind=='UserPromptSubmit':
                d=[d for d in current if d['registered_text']==h['prompt']];require(len(d)==1,'UPS_exact_registered_text')
                prompts[h['prompt_id']]=phases[d[0]['id']];data[phases[d[0]['id']]]['prompt_id']=h['prompt_id']
            hook_sources.setdefault(role,[]).append({'path':path,'kind':kind,'prompt_id':h['prompt_id'],'event_seq':matches[0]['seq']})
        require(hook_counts[role]==({'UserPromptSubmit':4,'Stop':4,'PermissionRequest':3} if role=='ideation' else {'UserPromptSubmit':1,'Stop':1}),'raw_hook_totals')
        files=sorted(n for n in reader.names if n.startswith(f'roles/{role}/http-exchanges/') and n.endswith('.request.bin'))
        require(len(files)==(7 if role=='ideation' else 1),'actual_POST_budget')
        for path in files:
            raw=reader.raw(path);request=json.loads(raw);response=reader.raw(path.replace('.request.bin','.response.bin'));meta=json.loads(reader.raw(path.replace('.request.bin','.meta.json')))
            require(meta['method']=='POST' and meta['path'].split('?')[0]=='/v1/messages' and meta['status']==200 and meta['complete'] is True,'actual_HTTP_success')
            require(meta['request_bytes']==len(raw) and meta['response_bytes']==meta['wire_bytes_confirmed']==len(response),'HTTP_original_bytes')
            text=[b.get('text') for m in request['messages'] if m['role']=='user' and isinstance(m.get('content'),list) for b in m['content'] if b.get('type')=='text']
            direct=[m['content'] for m in request['messages'] if m.get('role')=='user' and isinstance(m.get('content'),str)]
            located=[(index,d) for index,t in enumerate(text+direct) for d in current if t==d['registered_text']]
            require(bool(located),'request_registered_text_missing');dispatch=located[-1][1];stage=phases[dispatch['id']]
            require(meta['dispatch_id']==dispatch['id'] and meta['phase']==stage,'HTTP_dispatch_phase_binding')
            wire=[json.loads(line[6:]) for line in response.decode('utf-8').splitlines() if line.startswith('data: ')]
            require(wire and wire[0]['type']=='message_start' and wire[-1]['type']=='message_stop','complete_SSE')
            tool=[item['content_block'] for item in wire if item['type']=='content_block_start' and item['content_block']['type']=='tool_use']
            if tool:
                require(len(tool)==1 and tool[0]['name']=='Bash','only_actual_Bash')
                partial=''.join(item['delta']['partial_json'] for item in wire if item['type']=='content_block_delta' and item['delta']['type']=='input_json_delta')
                inp=json.loads(partial);require(set(inp)=={'command'},'real_Bash_command_schema')
                data[stage]['tools'].append({'tool_use_id':tool[0]['id'],'command':inp['command'],'response_file':path.replace('.request.bin','.response.bin')})
            data[stage]['POST'].append(path);http.append({'role':role,'stage':stage,'request':path,'status':meta['status'],'complete':True,'bytes':len(raw),'SSE_events':len(wire)})
        for stage,(expected_role,expected_posts,has_tool) in EXPECTED.items():
            if role!=expected_role:continue
            part=data[stage];require(len(part['POST'])==expected_posts and len(part['tools'])==(1 if has_tool else 0),'per_stage_actual_POST_and_tool_budget:'+stage)
            start=[h for h in hook_sources[role] if h['kind']=='UserPromptSubmit' and h['prompt_id']==part['prompt_id']];require(len(start)==1,'phase_UPS')
            require(len([h for h in hook_sources[role] if h['kind']=='Stop' and h['prompt_id']==part['prompt_id']])==1,'phase_Stop')
            if has_tool:
                tool=part['tools'][0];last=json.loads(reader.raw(part['POST'][-1]));settle=[b for b in blocks(last,'tool_result') if b['tool_use_id']==tool['tool_use_id']]
                require(len(settle)==1 and settle[0].get('is_error') is not True,'one_actual_tool_result')
                queued=json.loads(settle[0]['content']);require(queued['ok'] is True and queued['queued'] is True and queued['delivered'] is False,'tool_result_is_queue_only')
                req=[row for row in rows['relay_requests'] if row['launch']==native['launch'] and row['request_id']==queued['request_id']];require(len(req)==1,'actual_Stop_relay_request')
                require(json.loads(req[0]['input'])['prompt_id']==part['prompt_id'],'relay_actual_native_prompt')
                rr=[json.loads(row['data']) for row in rows['relay_results'] if row['key']==req[0]['key']];require(len(rr)==1,'actual_relay_result')
                permission=[h for h in hook_sources[role] if h['kind']=='PermissionRequest' and h['prompt_id']==part['prompt_id']];require(len(permission)==1,'one_PermissionRequest')
                h=json.loads(reader.raw(permission[0]['path']));require(h['tool_input']=={'command':tool['command']},'tool_permission_command_exact')
                controls=[e for e in events if e['launch']==native['launch'] and e['type']=='permission_control_written' and e['data']['prompt_id']==part['prompt_id']]
                require(len(controls)==1,'one_Enter_per_permission');control=controls[0];cid=control['data']['request_id']
                writes=[e for e in events if e['type']=='terminal_input_written' and e['data'].get('request_id')==cid]
                intents=[e for e in events if e['type']=='terminal_input_write_intent' and e['data'].get('request_id')==cid and e['data'].get('data')=='\r']
                actions=[json.loads(row['data']) for row in rows['user_inputs'] if json.loads(row['data']).get('source_ref',{}).get('command_id')==cid]
                require(len(writes)==len(actions)==len(intents)==1 and actions[0]['form']=='action' and actions[0]['content']=={'action':'terminal-key','data':'\r'},'control_action_not_message')
                require(not any(e['type']=='turn_submit_intent' and e['data'].get('request_id')==cid for e in events),'permission_Enter_must_not_submit_root')
                part.update(queued_request=queued['request_id'],relay=rr[0],permission_event_seq=permission[0]['event_seq'],control_event_seq=control['seq'])
                permission_sources.append({'stage':stage,'hook':permission[0]['path'],'event_seq':permission[0]['event_seq'],'control_seq':control['seq'],'request_id':cid,'action_id':actions[0]['id'],'command':tool['command']})
    stop=data['C-I1']['relay']['entry'];require(stop['kind']=='stop' and stop['from']=='ideation' and stop['to']=='executor','real_sender_stop')
    inbox=[json.loads(row['data']) for row in rows['inbox_records']]
    require(len([x for x in inbox if x['id']==stop['id']])==1 and not any(x['kind']=='ack' and x.get('reply_to')==stop['id'] for x in inbox),'original_stop_no_ack')
    require(data['C-I2']['relay'].get('error')=='stop_too_early' and data['C-I2']['relay']['ok'] is False,'actual_early_rejection')
    require(data['C-I3']['relay']=={'ok':True,'interruptRequested':True},'actual_late_interrupt_only')
    target=o['target_binding'];target_thread=target['thread_id']
    for stage in ['C-I2','C-I3']:
        argv=shlex.split(data[stage]['tools'][0]['command'])
        require(argv==[shlex.split(o['processes']['daemon']['command'])[0],str(Path(o['source'])/'workbench/src/gates/cli.ts'),
                       'stop','--thread',target_thread,'--stop-id',stop['id']],'same_target_original_stop_no_extra_command')
    emergencies=[row for row in rows['events'] if row['type']=='emergency_interrupt_requested']
    require(len(emergencies)==1,'one_actual_emergency');event=emergencies[0];detail=json.loads(event['details'])
    require(detail=={'stop_id':stop['id'],'thread':target_thread,'actor':'ideation'},'actual_ideation_caller')
    age=stamp(event['time'])-stamp(stop['created_at']);require(120000<age<150000,'real_event_age_gt120_lt150')
    baseline=reader.raw('target/baseline.bin');received=reader.raw('target/received.bin');require(received==baseline+b'\x1b','exactly_one_Esc')
    target_writes=[e for e in events if e['type']=='pane_interrupt_written'];require(len(target_writes)==1 and target_writes[0]['data']['leader']==o['processes']['target_leader']['pid'],'one_real_target_write')
    early=[e for e in events if e['type']=='relay_rejected' and e['data'].get('request_id')==data['C-I2']['queued_request']]
    require(len(early)==1 and 0<stamp(early[0]['time'])-stamp(stop['created_at'])<120000,'early_relay_time')
    task=reader.task_boundary;current=task['current_attempt']
    for key in ['task_id','attempt_id','session_id','fence','spec_rev','thread_id','workspace']:require(current[key]==target[key],'original_attempt_unchanged:'+key)
    require(current['reclaimed'] is False and current['state']==task['state']=='claimed' and task['candidate_commit'] is None and task['integration_intent'] is None,'only_interrupt_no_reclaim_or_integrate')
    require(not any(e['type'] in ['pane_exit','pane_stop_intent'] and e['launch']==o['claim_binding']['runtime_identity']['launch'] for e in events),'target_not_stopped_in_scene_events')
    clock_path=P1/'phases/C-I1/execute-02/clock-origin.json';origin=reader.json_source(clock_path)
    require(origin['stop']=={'id':stop['id'],'created_at':stop['created_at'],'request_id':data['C-I1']['queued_request']},'original_clock_binding')
    require(reader.source(clock_path)==reader.source(CONTROLS/'clock-origin.json'),'original_clock_copies_exact')
    plan=reader.json_source(CONTROLS/'protocol-plan.json')
    require(plan['root']==o['root'] and plan['source_revision']==o['source_revision'] and plan['target_binding']==o['claim_binding'],'original_plan_binding')
    demand=reader.json_source(CONTROLS/Path(plan['continued_demand_file']).relative_to(reader.root))
    require(demand['stop_id']==stop['id'] and demand['still_required'] is True and demand['source']=='test-simulated-user' and
        bool(demand['approval_ref']),'continued_original_stop_demand')
    late=reader.json_source(P1/'phases/C-I3/execute-02/result.json');enter=late['enter_at']
    require(enter['wall_age_ms']>120000 and enter['observed_elapsed_ms']>=120100,'late_control_clock_boundaries')
    require(abs(enter['observed_elapsed_ms']-(enter['monotonic_ms']-origin['mono_ms']))<1 and
            abs(enter['wall_age_ms']-(enter['wall_ms']-stamp(stop['created_at'])))<1,'recorded_clock_arithmetic')
    require(abs((enter['wall_ms']-origin['wall_ms'])-(enter['monotonic_ms']-origin['mono_ms']))<=1000,'no_clock_discontinuity')
    timed=reader.json_source(TIMED);require(timed['observed_time']['wall_age_ms']<150000,'completion_before150')
    screens=[]
    for stage in ['C-I1','C-I2','C-I3']:
        folder=P1/'phases'/stage;dispatch=reader.json_source(folder/'dispatch-01/result.json');screen=reader.source(folder/'dispatch-01/permission-screen.bin');capture=dispatch['permission_screen_capture']
        require(capture['complete'] is True and capture['start_offset']==0 and capture['next_offset']==capture['total_bytes']==len(screen),'complete_permission_screen')
        pages=capture['pages'];require(pages[0]['start_offset']==0 and pages[-1]['next_offset']==len(screen) and all(p['total_bytes']==len(screen) for p in pages),'consistent_permission_pages')
        signed_relative='permission-approval-01.json' if stage=='C-I1' else 'permission-signed.json' if stage=='C-I2' else 'execute-02-review/approved.json'
        signed=reader.json_source(folder/signed_relative)
        require(signed.get('approved_by')=='executor' and signed.get('approval_ref'),'signed_permission_template')
        require(dispatch['dispatch']['id']==data[stage]['dispatch'] and dispatch['permission_event']['seq']==data[stage]['permission_event_seq'],'same_permission_reference')
        command=data[stage]['tools'][0]['command']
        binding=signed['binding'] if stage=='C-I3' else signed
        require(binding['dispatch']==data[stage]['dispatch'] and binding['permission_seq']==data[stage]['permission_event_seq'] and
                binding.get('bash_command',binding.get('command'))==command and signed['key']=='Enter' and signed['selected_label']=='Yes' and
                signed['selected_line']=='❯ 1. Yes','approval_exact_command_and_permission')
        require(reader.source(signed['screen_file'])==screen,'approved_full_screen_exact')
        second=P1/(o['roles']['ideation']['session'][:8]+f'-ideation-{stage}-permission-screen-'+('02' if stage=='C-I1' else '01'))
        require(reader.source(second/'screen.bin')==screen,'independent_full_read_exact')
        verified_path=folder/('execute-02/result.json' if stage=='C-I1' else 'permission-check-01/result.json' if stage=='C-I2' else 'execute-02/control/result.json')
        verified=reader.json_source(verified_path)
        cap=verified['screen_capture'] if stage=='C-I3' else verified['permission_screen_verified_capture']
        require(cap['complete'] is True and cap['start_offset']==0 and cap['next_offset']==cap['total_bytes']==len(screen),'pre_Enter_direct_total')
        if stage=='C-I3':require(reader.source(folder/'execute-02/control/current-screen.bin')==screen,'last_C_I3_raw_read_exact')
        screens.append({'stage':stage,'source':str(folder/'dispatch-01/permission-screen.bin'),'bytes':len(screen),'total_bytes':capture['total_bytes'],
            'permission_event':data[stage]['permission_event_seq'],'signed_source':str(folder/signed_relative),
            'independent_read':str(second/'screen.bin'),'pre_Enter_capture_total':cap['total_bytes'],'verified_capture_source':str(verified_path)})
    return {'status':'PASS','root':o['root'],'archive':str(reader.archive) if reader.archive else None,
        'source_revision':o['source_revision'],'runtime_source_revision':'77865b044b5a5fedeeec12e62eae1314b87bf885',
        'POST':{'ideation':7,'executor':1},'roots':{'ideation':4,'executor':1},'permissions':3,'http':http,'hook_counts':hook_counts,'hook_sources':hook_sources,
        'phases':data,'permission_sources':permission_sources,'permission_screens':screens,'stop':{k:stop[k] for k in ['id','created_at','from','to']},
        'early_relay_event':{'seq':early[0]['seq'],'time':early[0]['time'],'age_ms':stamp(early[0]['time'])-stamp(stop['created_at'])},
        'late_emergency_event':event,'independent_emergency_age_ms':age,'late_Enter_clock':enter,'completion_observation':timed['observed_time'],
        'global_dispatch_sequence':[{'seq':d['seq'],'id':d['id'],'source':d['body']['source'],'stage':phases.get(d['id'],'target_initial')} for d in dispatches],
        'target_delta_hex':'1b','target_total_bytes':len(received),'baseline_bytes':len(baseline),'no_ack':True,'current_attempt_unchanged':True,'continued_original_stop_demand':demand,
        'model_turns':0,'model_scope':'actual local fake-API paths and frozen deterministic handler; no supplier response claimed',
        'sources':{'http_hooks':'roles/<role>/http-exchanges and hooks original files','gate_rows':'one live read transaction' if not reader.archive else 'tar live-rows.json captured before stop','clock':str(clock_path)},
        'limitations':'Worker readback is not independent reviewer acceptance. Current OS liveness awaits owner-bound dry-run; original stage drivers saved its checks. Cleanup not run.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--owner',type=Path,default=OWNER);p.add_argument('--archive',type=Path);p.add_argument('--task-boundary',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);reader=None
    try:
        reader=Reader(json.loads(a.owner.read_bytes()),a.archive,a.task_boundary);result=inspect(reader)
        if not a.archive:write(a.output/'task-boundary.json',reader.task_boundary)
    except Exception as error:result={'status':'INCOMPLETE','error':repr(error),'traceback':traceback.format_exc()}
    finally:
        if reader:reader.close()
    write(a.output/'result.json',result)
    print(json.dumps({key:result[key] for key in ['status','POST','roots','permissions','independent_emergency_age_ms','error'] if key in result},ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
