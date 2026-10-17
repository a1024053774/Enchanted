"""Replay attempt-1 records at settlement, HTTP handler and permission CLI entries.

These focused cases replay recorded I/O; the separate rehearsal uses real
daemon/relay/HTTP/PTY. Injected clocks here are not real-time evidence.
"""
import argparse
import base64
from contextlib import closing
import copy
import io
import json
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

import t078_09c_driver as c
import t078_09b_i1_driver as b
import t078_09b_fake_api as api
import electron_client
from t078_09b_rehearsal_peer import initial_messages

SOURCE = Path(__file__).resolve().parents[2]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
RECORDS = BASE / '09c-attempt-1-diagnosis-01'
PERMISSION_CODE = None


def permission_entry():
    path = SOURCE/'workbench/tests/t078_09b_i1_permission.py'
    if PERMISSION_CODE is None:
        return runpy.run_path(str(path),run_name='__main__')
    return exec(compile(PERMISSION_CODE,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})


def load(path): return json.loads(Path(path).read_bytes())


class Recorded:
    def __init__(self, root):
        self.root=root; self.saved=load(RECORDS/'stop-relay-and-events.json')
        self.inp=load(BASE/'09c-c1-b1-ideation-p1-01/input.json')
        self.claim=load(BASE/'09c-stage-a-01/readiness.json')['target_binding']
        events={row['seq']:row for row in self.saved['events']}
        for row in load(BASE/'09c-ci1-start-diagnosis-01/relevant-events.json')['dispatch_through_permission']:
            events[row['seq']]=row
        self.events=list(events.values()); (root/'state').mkdir(); self.db=root/'state/state.sqlite3'
        with closing(sqlite3.connect(self.db)) as db,db:
            db.executescript('CREATE TABLE orchestration_events(seq INTEGER,type TEXT,launch TEXT,data TEXT);'
                'CREATE TABLE inbox_records(id TEXT,data TEXT); CREATE TABLE relay_requests(key TEXT,request_id TEXT,launch TEXT,input TEXT);'
                'CREATE TABLE relay_results(key TEXT,data TEXT); CREATE TABLE events(type TEXT,details TEXT,time TEXT);'
                'CREATE TABLE launch_records(id TEXT,data TEXT);')
            db.executemany('INSERT INTO orchestration_events VALUES(?,?,?,?)',[(r['seq'],r['type'],r['launch'],json.dumps(r['data'])) for r in self.events])
            stop=self.saved['stop'];db.execute('INSERT INTO inbox_records VALUES(?,?)',(stop['id'],json.dumps(stop)))
            req=self.saved['relay_request'];db.execute('INSERT INTO relay_requests VALUES(?,?,?,?)',tuple(req[k] for k in ['key','request_id','launch','input']))
            res=self.saved['relay_result'];db.execute('INSERT INTO relay_results VALUES(?,?)',(res['key'],res['data']))
            db.execute('INSERT INTO launch_records VALUES(?,?)',(self.inp['launch'],json.dumps(self.inp)))
        self.plan={'scene':'09C','root':str(root),'source':str(SOURCE),'node':'/opt/homebrew/bin/node',
            'target_binding':self.claim,'roles':{'ideation':self.inp},'source_revision':self.inp['code_revision'],
            'synthetic_input_id':next(x[6:] for x in stop['refs'] if x.startswith('input:')),
            'i1_prompt':(BASE/'09c-materials-01/i1-prompt.txt').read_text(encoding='utf-8'),
            'target_bytes':'received.bin','target_baseline_hex':'','clock_origin_file':str(root/'clock.json'),
            'target_identity':load(BASE/'09c-materials-01/owner.json')['target_binding']}
        self.plan['target_identity'].update(shell_pid=54366,leader_pid=54368,native_session=self.claim['runtime_identity']['native_session'])
        (root/'received.bin').write_bytes(b''); self.role=root/'roles/ideation';self.role.mkdir(parents=True)
        calls=load(RECORDS/'HTTP-metadata-and-tool-results.json')['requests']['ideation']
        self.calls=[row for row in calls if row['phase']=='C-I1' and not row['error']]
        (self.role/'requests.ndjson').write_text(''.join(json.dumps(row)+'\n' for row in self.calls),encoding='utf-8')
        (self.role/'http-exchanges').mkdir()
        for i in [1,2]:(self.role/'http-exchanges'/f'{i:04d}.request.bin').write_bytes(b'fixed recorded POST boundary')

    def gate(self, root, command, *args):
        if command=='status':return {'task':{'current_attempt':self.claim}}
        if command=='pane_process_info':return {'shell_pid':54366,'leader':54368,'native_session':self.claim['runtime_identity']['native_session'],'session_ended':False,'failed':None}
        raise AssertionError('unexpected recorded gate command: '+command)

    def settle(self):
        instant=c.created_ms(self.saved['stop']['created_at'])+1000
        class Clock:
            def wall(self):return instant
            def mono(self):return 1000
        out=self.root/'settle';out.mkdir()
        with patch.object(c,'Clock',Clock),patch.object(b,'gate',self.gate):
            value=c.settle_stage(self.plan,self.inp,'C-I1',out)
        assert value['status']=='PASS' and load(self.root/'clock.json')['stop']['request_id']==self.saved['relay_request']['request_id']

    def handler(self):
        for path in (self.role/'http-exchanges').iterdir():path.unlink()
        (self.root/'plan.json').write_text(json.dumps(self.plan),encoding='utf-8')
        (self.role/'protocol-registry.json').write_text(json.dumps({'phase_plan':str(self.root/'plan.json')}),encoding='utf-8')
        approved=load(BASE/'09c-c1-b1-ideation-p1-01/phases/C-I2/approval.json')
        (self.role/'stage-approvals').mkdir();(self.role/'stage-approvals/C-I2.json').write_text(json.dumps(approved),encoding='utf-8')
        dispatch=next(r['data'] for r in self.events if r['type']=='dispatch_queued' and r['data']['source']=='gate')
        structure=load(BASE/'09c-fix-01/request-structure.json')
        body={**structure['request'],'messages':initial_messages(structure,dispatch['text'])}
        encoded=json.dumps(body).encode();api.configure(self.role,'ideation',True)
        handler=api.Handler.__new__(api.Handler);handler.path='/v1/messages';handler.rfile=io.BytesIO(encoded);handler.wfile=io.BytesIO()
        handler.headers={'Content-Length':str(len(encoded)),'Content-Type':'application/json'}
        seen={};handler.send_response=lambda code:seen.update(status=code)
        handler.send_header=lambda *args:None;handler.end_headers=lambda:None
        handler.do_POST();(self.root/'handler-response.bin').write_bytes(handler.wfile.getvalue())
        assert seen['status']==200,handler.wfile.getvalue().decode()

    def start(self):
        self.plan['prompt_file']=str(self.root/'prompt.txt');Path(self.plan['prompt_file']).write_text(self.plan['i1_prompt'],encoding='utf-8')
        # No POST before the fresh start; dispatch result is the actual recorded message.
        for path in (self.role/'http-exchanges').iterdir():path.unlink()
        dispatch=next(r['data'] for r in self.events if r['launch']==self.inp['launch'] and r['type']=='dispatch_queued' and r['data']['source']=='executor')
        observed=[]
        def gate(root,command,*args):
            observed.append(command)
            if command=='pane_status':return {'state':'idle','active':None,'queued':[]}
            if command=='pane_dispatch':return {'dispatch':dispatch}
            if command=='pane_release':raise RuntimeError('initial_release_only')
            raise AssertionError(command)
        # Add the second original role solely for the start's idle preflight.
        self.plan['roles']['executor']=load(BASE/'09c-c1-b1-executor-p1-01/input.json')
        value=c.start_first_turn(self.plan,{'approval_ref':'recorded-entry fixture only'},gate)
        assert value['dispatch']==dispatch and observed==['pane_status','pane_status','pane_dispatch']


def duplicate_output(root):
    out=root/'existing';out.mkdir();original=(BASE/'09c-c1-b1-ideation-p1-01/phases/C-I1/execute-02/result.json').read_bytes()
    (out/'result.json').write_bytes(original);calls=[]
    argv=['permission','--materials',str(root),'--p1',str(root),'--stage','C-I1','--stage-a',str(root),
          '--dispatch-result',str(root/'unused'),'--process-manifest',str(root/'unused'),'--approval',str(root/'unused'),'--output',str(out)]
    def forbidden(*args,**kwargs):calls.append('spawn-or-window');raise AssertionError('duplicate output must stop before spawn')
    try:
        with patch.object(sys,'argv',argv),patch('subprocess.run',forbidden),patch.object(electron_client,'ElectronClient',forbidden):
            permission_entry()
    except FileExistsError:pass
    assert (out/'result.json').read_bytes()==original,'duplicate output overwrote original result'
    assert not calls,'duplicate output spawned process/window'
    return {'original_result_bytes_unchanged':True,'process_or_window_starts':len(calls),'key_writes':0}


def binding_counterexamples(output):
    cases=[]
    for kind in ['original-send','wrong-launch','wrong-key','wrong-native-session','duplicate-request','pending-not-delivered']:
        with tempfile.TemporaryDirectory(prefix='t078-recorded-negative-',dir='/private/tmp') as path:
            record=Recorded(Path(path))
            with closing(sqlite3.connect(record.db)) as db,db:
                if kind=='wrong-launch':db.execute("UPDATE relay_requests SET launch='different-controller'")
                if kind=='wrong-key':db.execute("UPDATE relay_results SET key='different-request'")
                if kind=='wrong-native-session':
                    value=json.loads(record.saved['relay_request']['input']);value['native_session']='other-native-session'
                    db.execute('UPDATE relay_requests SET input=?',(json.dumps(value),))
                if kind=='duplicate-request':db.execute('INSERT INTO relay_requests SELECT * FROM relay_requests')
            try:
                if kind=='pending-not-delivered':
                    event=copy.deepcopy(next(r['data'] for r in record.events if r['type']=='dispatch_queued' and r['data']['source']=='gate'))
                    from t078_09b_phase_registry import feedback_receipts
                    envelope=feedback_receipts(event['text']);envelope[0]['result']['delivery']['state']='pending'
                    event['text']=event['text'].partition('\n')[0]+'\nactual feedback\n'+json.dumps(envelope)
                    c.phase_for_dispatch(record.plan,'ideation',event)
                else:
                    _,request,_=c.original_send(record.plan)
                    assert request['request_id']==record.saved['relay_request']['request_id']
                accepted=True;error=None
            except ValueError as exc:accepted=False;error=repr(exc)
            assert accepted==(kind=='original-send'),(kind,accepted,error)
            cases.append({'name':kind,'status':'PASS','accepted':accepted,'error':error,'key_writes':0})
    return cases


def late_early_permission(root, age=100000):
    """Counterexample: a delayed early-stage check must stop before any key."""
    record=Recorded(root);p1=root/'p1';p1.mkdir();stage=root/'stage';stage.mkdir()
    dispatch=load(BASE/'09c-c1-b1-ideation-p1-01/phases/C-I1/dispatch-01/result.json')
    dispatch['stage']='C-I2'
    plan=record.plan;plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan),encoding='utf-8')
    dispatch['phase_plan']=str(plan_path)
    approval=load(BASE/'09c-c1-b1-ideation-p1-01/phases/C-I1/permission-approval-01.json')
    for path,value in [(p1/'input.json',record.inp),(p1/'dispatch.json',dispatch),(p1/'permission.json',approval),
                       (p1/'manifest.json',{'launch':record.inp['launch'],'session':record.inp['session']}),
                       (stage/'readiness.json',{'root':str(root)})]:path.write_text(json.dumps(value),encoding='utf-8')
    old=c.created_ms(record.saved['stop']['created_at'])
    origin={'stop':{'id':record.saved['stop']['id'],'created_at':record.saved['stop']['created_at'],
                    'request_id':record.saved['relay_request']['request_id']},'wall_ms':old,'mono_ms':10000}
    class RecordedClock:
        def wall(self):return old+age
        def mono(self):return 10000+age
    Path(plan['clock_origin_file']).write_text(json.dumps(origin),encoding='utf-8')
    raw=Path(dispatch['permission_screen']).read_bytes();calls=[]
    def gate(root,command,*args):
        if command=='pane_status':return {'state':'busy','active':{'dispatch':dispatch['dispatch']['id']}}
        if command=='pane_output':
            offset=int(args[args.index('--offset')+1]);data=raw[offset:]
            return {'launch':record.inp['launch'],'start_offset':offset,'next_offset':len(raw),'total_bytes':len(raw),
                    'data_base64':base64.b64encode(data).decode()}
        raise AssertionError(command)
    def forbidden(*args,**kwargs):calls.append('spawn/window/key');raise AssertionError('late check spawned')
    argv=['permission','--materials',str(p1),'--p1',str(p1),'--stage','C-I2','--stage-a',str(stage),
          '--dispatch-result',str(p1/'dispatch.json'),'--process-manifest',str(p1/'manifest.json'),
          '--approval',str(p1/'permission.json'),'--output',str(root/'late-check'),'--check-only']
    rejected=False
    try:
        with patch.object(c,'Clock',RecordedClock),patch.object(sys,'argv',argv),patch.object(b,'gate',gate),patch('subprocess.run',forbidden),patch.object(electron_client,'ElectronClient',forbidden):
            permission_entry()
    except ValueError as error:rejected='C_early_permission_deadline' in str(error)
    except SystemExit as error:assert error.code==0
    assert rejected==(age>=90000),'late early-permission check accepted' if age>=90000 else 'fresh early-permission check rejected'
    assert not calls
    return {'observed_age_ms':age,'process_window_key_calls':len(calls),'rejected':rejected}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--expect',choices=['red','green'],required=True)
    parser.add_argument('--case',choices=['late-early-permission'])
    parser.add_argument('--known-bad-revision',choices=['f1518b627b85edb0d170fee779cb8202ffae38b3'])
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);rows=[]
    if args.known_bad_revision:
        global PERMISSION_CODE
        assert args.expect=='red'
        snapshots=args.output/'source';snapshots.mkdir()
        texts={}
        for name in ['t078_09c_driver.py','t078_09b_i1_permission.py']:
            raw=subprocess.check_output(['git','show',args.known_bad_revision+':workbench/tests/'+name],cwd=SOURCE)
            (snapshots/name).write_bytes(raw);texts[name]=raw.decode('utf-8')
        metadata={k:c.__dict__[k] for k in ['__name__','__file__','__package__','__loader__','__spec__']}
        c.__dict__.clear();c.__dict__.update(metadata)
        exec(compile(texts['t078_09c_driver.py'],c.__file__,'exec'),c.__dict__)
        PERMISSION_CODE=texts['t078_09b_i1_permission.py']
    names=[args.case] if args.case else ['settlement-request-id','HTTP-envelope','start-after-initialize','duplicate-output','late-early-permission']
    if args.expect=='green' and not args.case:names.append('fresh-early-permission')
    for name in names:
        with tempfile.TemporaryDirectory(prefix='t078-recorded-entry-',dir='/private/tmp') as folder:
            root=Path(folder)
            try:
                observed=None
                if name=='late-early-permission':observed=late_early_permission(root)
                elif name=='fresh-early-permission':observed=late_early_permission(root,1000)
                elif name=='duplicate-output':observed=duplicate_output(root)
                else:
                    record=Recorded(root)
                    {'settlement-request-id':record.settle,'HTTP-envelope':record.handler,'start-after-initialize':record.start}[name]()
                passed,error=True,None
            except Exception as exc:
                passed,error=False,repr(exc)
                (args.output/(name+'.traceback.txt')).write_text(traceback.format_exc(),encoding='utf-8')
            specific=({'settlement-request-id':"KeyError('request_id')",'HTTP-envelope':'C_actual_delivery_required',
                       'start-after-initialize':'initial_release_only','duplicate-output':'overwrote original result',
                       'late-early-permission':'late early-permission check accepted','fresh-early-permission':'fresh early-permission check rejected'}[name])
            rows.append({'name':name,'desired_contract_passed':passed,'error':error,
                         'expected_red_observed':not passed and specific in error if error else False,'observed':observed})
    negatives=binding_counterexamples(args.output) if args.expect=='green' else []
    ok=all(row['desired_contract_passed'] if args.expect=='green' else row['expected_red_observed'] for row in rows)
    result={'status':'PASS' if ok else 'INCOMPLETE','expected':args.expect,'checks':rows,
            'counterexamples':negatives,'scope':__doc__,'recorded_source':str(RECORDS),'known_bad_revision':args.known_bad_revision,
            'model_turns':0,'role_CLIs':0,'live_scene_touched':False}
    (args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
