"""Exercise only the receipt consumer with persisted real rows or owner sentinels.

Contract: use the queued request ID for the selected launch; the journal key is
opaque. An identical request ID on another launch cannot select that outcome.
"""
import argparse,ast,json,sqlite3
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--failed-fixture',type=Path,required=True);args=p.parse_args()
args.output.mkdir()
source=Path(__file__).with_name('t078_worker_inbox_scenario.py').read_text(encoding='utf-8')
tree=ast.parse(source);top=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_worker_inbox')
receipt=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='receipts_for_launch'),None)
if receipt:
    namespace={'json':json};exec(compile(ast.Module(body=[receipt],type_ignores=[]),'<actual receipt consumer>','exec'),namespace)
    collect=namespace['receipts_for_launch']
else:
    # Freeze the current broken expression rather than fabricating a bad model.
    assignment=next(n for n in top.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='receipts' for t in n.targets))
    reply=next(n for n in top.body if isinstance(n,ast.FunctionDef) and n.name=='reply')
    def collect(query,launch):
        scope={'json':json,'query':query};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'<current consumer>','exec'),scope)
        # Return a request-id map using the actual current get expression.
        values={}
        for row in query('relay_requests'):
            if row['launch']!=launch:continue
            scope.update(queued={'case':row['request_id']});exec(compile(ast.Module(body=[reply],type_ignores=[]),'<current reply>','exec'),scope)
            values[row['request_id']]=scope['reply']('case')
        return values
facts=json.loads((args.failed_fixture/'results.json').read_bytes());root=Path(facts['fixture'])
dbfile=root/'state/state.sqlite3';assert facts['cleanup_complete'] and not Path(str(dbfile)+'-wal').exists()
db=sqlite3.connect(dbfile.as_uri()+'?mode=ro&immutable=1',uri=True);db.row_factory=sqlite3.Row
tables={name:[dict(r) for r in db.execute('SELECT * FROM '+name+' ORDER BY rowid')] for name in ['relay_requests','relay_results']};db.close()
launch=facts['worker_client']['identity']['launch'];ids={x['name']:x['response']['request_id'] for x in facts['worker_client']['commands']}
checks=[]
actual=collect(lambda table:tables[table],launch)
expected_errors={'assign':'invalid_direction','ready':'controller_required','ack-foreign':'recipient_required'}
for name,error in expected_errors.items():
    passed=actual.get(ids[name],{}).get('error')==error;checks.append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','expected_error':error,'observed':actual.get(ids[name],{})})
checks.append({'name':'issue_real_sender','status':'PASS' if actual.get(ids['issue'],{}).get('entry',{}).get('from')=='worker:'+facts['attempt']['thread_id'] else 'INCOMPLETE'})
address='worker:'+facts['attempt']['thread_id']
listed=actual.get(ids['list'],{}).get('entries',[])
checks.append({'name':'list_real_scope','status':'PASS' if any(v['entry']['id']=='visible-message' for v in listed) and all(v['entry']['to']==address for v in listed) else 'INCOMPLETE'})
ack1=actual.get(ids['ack-one'],{}).get('entry',{});ack2=actual.get(ids['ack-two'],{}).get('entry',{})
checks.append({'name':'owned_ack_idempotent','status':'PASS' if ack1.get('id') and ack1.get('id')==ack2.get('id') and ack1.get('from')==address else 'INCOMPLETE'})
stale=facts['revoked_worker_client']['commands'][0]['response']['request_id']
checks.append({'name':'revoked_attempt_error','status':'PASS' if actual.get(stale,{}).get('error')=='stale_attempt' else 'INCOMPLETE'})
sentinel={'relay_requests':[{'launch':'chosen','request_id':'shared','key':'opaque-selected'}, {'launch':'other','request_id':'shared','key':'opaque-foreign'}],
          'relay_results':[{'key':'opaque-selected','data':json.dumps({'ok':True,'sentinel':'selected'})},{'key':'opaque-foreign','data':json.dumps({'ok':True,'sentinel':'foreign'})}]}
value=collect(lambda table:sentinel[table],'chosen')
checks.append({'name':'opaque_key_and_foreign_owner','status':'PASS' if value=={'shared':{'ok':True,'sentinel':'selected'}} else 'INCOMPLETE','expected':{'shared':{'ok':True,'sentinel':'selected'}},'observed':value})
r={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'Actual receipt consumer and read-only real failed fixture; no server/CLI/UI/model starts','argv':__import__('sys').argv,'real_model_turns':0}
(args.output/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');(args.output/'consumer.py').write_text(source,encoding='utf-8')
print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
