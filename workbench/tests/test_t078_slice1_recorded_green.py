"""Replay #184 native Messages unchanged against independent registration bytes."""
import argparse
import copy
import json
import tempfile
import tarfile
from pathlib import Path
import t078_slice1_protocol as protocol
from t078_fake_inbox_tool import load_registered_feedback

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--registered-feedback',action='store_true')
args=p.parse_args();args.output.mkdir()
base=Path(__file__).resolve().parents[2]/'evidence/2026-10-11-batch13/T-078/slice1-green-3-readback'
scenario=json.loads((base/'scenario.json').read_bytes());reference=json.loads((base/'registered-feedback.json').read_bytes())
messages=[json.loads(s)['body'] for s in (base/'api.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(s)['path']=='/v1/messages']
checks=[]
def check(name,body,number,expected,feedback=None):
 try:
  if args.registered_feedback:observed=protocol.validate_request(body,number,scenario,reference['text'] if feedback is None else feedback)
  else:observed=protocol.validate_request(body,number,scenario)
  accepted=True
 except ValueError as error:observed=str(error);accepted=False
 checks.append({'name':name,'status':'PASS' if accepted==expected else 'INCOMPLETE','expected_accepted':expected,'observed':observed})
for n,body in enumerate(messages,1):check('original-API'+str(n),body,n,n<=3)
third=messages[2];last_user=next(i for i in reversed(range(len(third['messages']))) if third['messages'][i]['role']=='user')
bad=copy.deepcopy(third);bad['messages'][last_user]['content']=[{'type':'text','text':reference['text']}]
check('same-registered-text-as-block-array',bad,3,True)
bad=copy.deepcopy(third);bad['messages'][last_user]['content']+=' extra'
check('changed-registered-body-is-rejected',bad,3,False)
bad=copy.deepcopy(third);bad['model']='foreign-model';check('changed-model-is-rejected',bad,3,False)
bad=copy.deepcopy(third);bad['stream']=False;check('nonstream-is-rejected',bad,3,False)
bad=copy.deepcopy(third)
tool=next(p for m in bad['messages'] if m['role']=='assistant' for p in m['content'] if p['type']=='tool_use')
tool['input']['command']+=' --extra';check('changed-command-is-rejected',bad,3,False)
bad=copy.deepcopy(third)
result=next(p for m in bad['messages'] if m['role']=='user' and isinstance(m['content'],list) for p in m['content'] if p['type']=='tool_result')
result['tool_use_id']='foreign-tool';check('foreign-tool-ID-is-rejected',bad,3,False)
bad=copy.deepcopy(third)
result=next(p for m in bad['messages'] if m['role']=='user' and isinstance(m['content'],list) for p in m['content'] if p['type']=='tool_result')
queued=json.loads(protocol.text_content(result['content']));queued['request_id']='foreign-request';result['content']=json.dumps(queued)
check('foreign-request-ID-is-rejected',bad,3,False)
foreign=next(e['id'] for e in scenario['inbox_fixture'] if e['to']=='executor');own=next(e['id'] for e in scenario['inbox_fixture'] if e['to']=='ideation')
bad=copy.deepcopy(third);foreign_text=reference['text'].replace(own,foreign);bad['messages'][last_user]['content']=foreign_text
check('registered-but-foreign-role-result-is-rejected',bad,3,False,foreign_text)
if args.registered_feedback:
 state=Path(tempfile.mkdtemp(prefix='t78-feedback-reference-',dir='/tmp')).resolve()
 with tarfile.open(base/'raw-database.tar.gz') as archive:
  for member in archive.getmembers():
   assert member.name in ['state.sqlite3','state.sqlite3-wal','state.sqlite3-shm','membership.sqlite3','membership.sqlite3-wal','membership.sqlite3-shm'] and member.isfile()
   (state/member.name).write_bytes(archive.extractfile(member).read())
 launch=reference['dispatch_row']['launch']
 checks.append({'name':'reference-read-uses-actual-registered-launch','status':'PASS' if load_registered_feedback(state,launch)==reference['text'] else 'INCOMPLETE'})
 try:load_registered_feedback(state,'foreign-launch');denied=False
 except ValueError:denied=True
 checks.append({'name':'foreign-launch-has-no-feedback-reference','status':'PASS' if denied else 'INCOMPLETE'})
record={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'registered_feedback_argument':args.registered_feedback,
        'scope':'Original native request replay plus independent database registration; no re-send, socket, CLI or API start','source_api':str(base/'api.jsonl'),'reference':str(base/'registered-feedback.json'),'real_model_turns':0}
(args.output/'results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':record['status'],'checks':len(checks),'failures':[c['name'] for c in checks if c['status']!='PASS']}));raise SystemExit(0 if record['status']=='PASS' else 1)
