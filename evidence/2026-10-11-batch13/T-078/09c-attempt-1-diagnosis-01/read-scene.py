"""只读还原失败场次；不调用结算函数、业务命令或写 clock-origin。"""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import signal
import sqlite3
import sys
import traceback

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
SOURCE = BASE.parents[2]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from t078_09b_i1_driver import gate
from t078_09b_phase_registry import feedback_receipts
from t078_09c_driver import phase_for_dispatch


def load(path): return json.loads(Path(path).read_bytes())


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not (OUT / 'result.json').exists()
    def timeout(*_): raise TimeoutError('readonly_diagnosis_timeout_20s')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(20)
    result = {'status':'INCOMPLETE','scope':'只读 SELECT/HTTP-meta/hook/Electron日志/pane_status；不续行、不写业务状态',
              'business_actions':0,'keys_sent':0,'clock_origin_written':False}
    try:
        ready = load(BASE / '09c-stage-a-01/readiness.json'); root = Path(ready['root'])
        plan = load(root / 'protocol-plan.json'); inputs = plan['roles']
        i1 = BASE / '09c-c1-b1-ideation-p1-01/phases/C-I1'
        with closing(sqlite3.connect((root/'state/state.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
            db.row_factory=sqlite3.Row; db.execute('BEGIN')
            data={table:[dict(row) for row in db.execute('SELECT * FROM '+table+' ORDER BY rowid')]
                  for table in ['inbox_records','inbox_deliveries','relay_requests','relay_results','orchestration_events','user_inputs','events']}
        stops=[json.loads(row['data']) for row in data['inbox_records'] if json.loads(row['data']).get('kind')=='stop']
        stops=[item for item in stops if 'input:'+plan['synthetic_input_id'] in item.get('refs',[])]
        assert len(stops)==1; stop=stops[0]
        requests=[row for row in data['relay_requests'] if row['launch']==inputs['ideation']['launch'] and json.loads(row['input'])['command']=='inbox_send']
        assert len(requests)==1; request=requests[0]
        receipts=[row for row in data['relay_results'] if row['key']==request['key']]
        assert len(receipts)==1; receipt=json.loads(receipts[0]['data'])
        assert receipt['entry']['id']==stop['id'] and receipt['delivery']['state']=='delivered'
        events=[{**row,'data':json.loads(row['data'])} for row in data['orchestration_events']]
        inputs_cr=[row for row in events if row['launch']==inputs['ideation']['launch'] and row['type']=='terminal_input_write_intent' and row['data'].get('data')=='\r']
        assert len(inputs_cr)==1; action_id=inputs_cr[0]['data']['request_id']
        written=[row for row in events if row['type']=='terminal_input_written' and row['data'].get('request_id')==action_id]
        assert len(written)==1
        actions=[json.loads(row['data']) for row in data['user_inputs']]
        actions=[row for row in actions if row.get('source_ref',{}).get('command_id')==action_id]
        assert len(actions)==1 and actions[0]['form']=='action' and actions[0]['content']['data']=='\r'
        journal=[json.loads(line) for line in (i1/'execute-02-electron-driver.jsonl').read_bytes().splitlines() if line.strip()]
        keys=[row['request'] for row in journal if row.get('request',{}).get('command')=='terminal-key']
        responses=[json.loads(row['response']) for row in journal if 'response' in row]
        responses=[row for row in responses if row.get('id')==keys[0]['id']]
        assert len(keys)==len(responses)==1 and keys[0]['key']=='Enter'
        assert responses[0]['value']['delivered']=={'ok':True,'written':True,'request_id':action_id}
        save('one-Enter-receipts.json',{'request':keys[0],'response_delivery':responses[0]['value']['delivered'],
            'intent':inputs_cr[0],'written':written[0],'action':actions[0]})
        relevant=[row for row in events if row['type'] in ['turn_submitted','turn_start_signal','turn_end_signal','permission_wait','relay_processed','relay_rejected','dispatch_queued','pane_idle']]
        save('stop-relay-and-events.json',{'stop':stop,'relay_request':request,'relay_result':receipts[0],
            'deliveries':[row for row in data['inbox_deliveries'] if row['entry']==stop['id']],
            'events':relevant,'emergency_interrupts':[row for row in data['events'] if row['type']=='emergency_interrupt_requested']})
        calls={}; meta={}; hook_index=[]
        for role in ['ideation','executor']:
            folder=root/'roles'/role; path=folder/'requests.ndjson'
            records=[json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]
            calls[role]=[{key:item.get(key) for key in ['sequence','at','phase','dispatch_id','message_kind','tool_result_payload','error']} for item in records]
            meta[role]=[load(path) for path in sorted((folder/'http-exchanges').glob('*.meta.json'))]
            for trace in sorted((folder/'hooks').iterdir()):
                if not trace.is_dir(): continue
                native=load(trace/'stdin.bin'); finish=load(trace/'finished.json') if (trace/'finished.json').exists() else None
                dest=OUT/'hooks'/role/trace.name; dest.mkdir(parents=True)
                for name in ['stdin.bin','started.json','finished.json','stdout.bin','stderr.bin']:
                    path=trace/name
                    if path.is_file():
                        with (dest/name).open('xb') as stream:stream.write(path.read_bytes())
                hook_index.append({'role':role,'trace':str(trace),'saved':str(dest),
                    'event':native['hook_event_name'],'prompt_id':native.get('prompt_id'),'finished':finish})
        save('HTTP-metadata-and-tool-results.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'requests':calls,'HTTP_metadata':meta})
        save('hook-index.json',hook_index)
        payload=[row['tool_result_payload'] for row in calls['ideation'] if row['phase']=='C-I1' and row['message_kind']=='tool_result']
        assert len(payload)==1 and payload[0]['request_id']==request['request_id']
        try: receipt['request_id']
        except KeyError as error: keyerror=repr(error)
        else: raise AssertionError('原 relay_result.data 不应伪造 request_id')
        feedback=[row for row in relevant if row['type']=='dispatch_queued' and row['launch']==inputs['ideation']['launch'] and row['data']['source']=='gate']
        assert len(feedback)==1; wrapped=feedback_receipts(feedback[0]['data']['text'])[0]
        assert wrapped['request_id']==request['request_id'] and wrapped['result']==receipt
        try: phase_for_dispatch(plan,'ideation',feedback[0]['data'])
        except ValueError as error: phase_error=repr(error)
        else: raise AssertionError('当前 C-I2 错误解包应拒绝真实反馈')
        save('field-assumption-reds.json',{'original_first_traceback':'已被重跑覆盖；此文件不是原始 traceback',
            'clock_origin_expression':"receipt['request_id']",'observed_error':keyerror,
            'actual_relay_result_keys':list(receipt),'proven_request_id':request['request_id'],
            'queued_tool_result_request_id':payload[0]['request_id'],'feedback_envelope_keys':list(wrapped),
            'actual_C_phase_resolver_error':phase_error,'business_result_is_envelope_result':True,
            'related_missing_fields':['NativePermission.actual send[].request_id','observe send[0].request_id']})
        panes={role:gate(root,'pane_status','--thread',inp['thread']) for role,inp in inputs.items()}
        save('pane-status.json',panes)
        now=datetime.now(timezone.utc); age=(now-datetime.fromisoformat(stop['created_at'].replace('Z','+00:00'))).total_seconds()
        target=(root/plan['target_bytes']).read_bytes(); baseline=bytes.fromhex(plan['target_baseline_hex'])
        assert target==baseline and not Path(plan['clock_origin_file']).exists()
        assert not any(json.loads(row['data']).get('kind')=='ack' for row in data['inbox_records'])
        result.update(status='PASS',scene_status='INCOMPLETE; 不续行',source_revision=ready['source_revision'],root=str(root),
            stop_id=stop['id'],created_at=stop['created_at'],delivery=receipt['delivery'],original_request_id=request['request_id'],
            one_Enter_request_id=action_id,one_Enter_events=[inputs_cr[0]['seq'],written[0]['seq']],
            POST_counts_at_snapshot={role:len(items) for role,items in meta.items()},
            C_I1_successful_POSTs=sum(item['phase']=='C-I1' and not item['error'] for item in calls['ideation']),
            C_I2='实际反馈已提交；API C_actual_delivery_required，无 C-I2 tool_use/许可；会按原生策略重试',
            executor='C-E1 单条保持到150秒后不完整结束；额外原生重试如实计数',
            clock_origin_exists=False,wall_age_seconds_at_snapshot=age,no_ack=True,target_delta_hex='',
            first_result_loss='execute-02/result.json 现为 FileExistsError；不伪造恢复原件，另存可追溯重建',
            snapshot_warning='POST/错误可能继续增长；回收必须稳定采集，tar 再独立重数')
    except Exception as error:
        result.update(error=repr(error),traceback=traceback.format_exc())
    finally:signal.alarm(0)
    save('result.json',result)
    print(json.dumps({k:result[k] for k in ['status','stop_id','created_at','POST_counts_at_snapshot','error'] if k in result},ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
