"""Reject an attempted key or an uncorrelated/incomplete PTY receipt as delivery."""
import argparse, copy, json
from pathlib import Path
from p1_window_receipts import confirmed_escape
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant-no-write',action='store_true');a=p.parse_args()
binding=dict(launch='launch',thread='thread',dispatch='dispatch',window='window',after_seq=10)
source=dict(command_id='request',source_sequence=2,window_id='window')
action=dict(form='action',channel='terminal-window',content={'action':'terminal-key','data':'\x1b'},target={'thread':'thread'},source_ref=source)
receipt=dict(request_id='request',sequence=2,window_id='window',encoding='utf8',byte_length=1)
events=[dict(seq=11,launch='launch',type='window_request_admitted',data={**receipt,'command':'window_input'}),
        dict(seq=12,launch='launch',type='terminal_input_write_intent',data={**receipt,'data':'\x1b'}),
        dict(seq=13,launch='launch',type='terminal_input_written',data=receipt),
        dict(seq=14,launch='launch',type='claude_submission_retired',data={'dispatch':'dispatch','reason':'user-esc'})]
if a.mutant_no_write:
    # Execute a known-bad verifier that invents the missing write receipt.
    code=Path(__file__).with_name('p1_window_receipts.py').read_text(encoding='utf-8')
    marker="        retired = [e for e in events"
    code=code.replace(marker,"        if not written and intent: written = [{**intent[0], 'seq': intent[0]['seq'] + 0.5}]\n"+marker)
    scope={};exec(compile(code,'mutant-no-write','exec'),scope);confirmed_escape=scope['confirmed_escape']
checks=[]
def check(name,es,ins,expected):
    v=confirmed_escape(es,ins,**binding);checks.append({'name':name,'status':'PASS' if bool(v)==expected else 'INCOMPLETE','delivery_observed':bool(v)})
check('attempt_without_backend_facts_is_not_delivery',[],[],False)
check('complete_matching_receipt_is_delivery',events,[action],True)
for kind in ['window_request_admitted','terminal_input_write_intent','terminal_input_written','claude_submission_retired']:
    check('missing_'+kind,[e for e in events if e['type']!=kind],[action],False)
for field,value in [('request_id','other'),('window_id','other'),('sequence',3)]:
    altered=copy.deepcopy(events);altered[2]['data'][field]=value;check('wrong_'+field,altered,[action],False)
check('missing_user_action',events,[],False)
altered=copy.deepcopy(action);altered['target']['thread']='other';check('wrong_action_thread',events,[altered],False)
altered=copy.deepcopy(events);altered[3]['data']['dispatch']='other';check('wrong_retired_dispatch',altered,[action],False)
r={'status':'PASS' if all(v['status']=='PASS' for v in checks) else 'INCOMPLETE','checks':checks,'argv':__import__('sys').argv,'scope':'Synthetic persisted facts only; no daemon, PTY or UI starts','mutant_no_write':a.mutant_no_write}
with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
print(json.dumps(r));raise SystemExit(0 if r['status']=='PASS' else 1)
