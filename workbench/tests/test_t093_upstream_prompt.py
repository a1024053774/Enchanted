"""Actual upstream do_POST with byte streams; no socket, CLI, auth read or process."""
import ast
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import uuid

source=Path(__file__).with_name('t093_parallel_chain_peer.py').resolve()
spec=importlib.util.spec_from_file_location('upstream',source);mod=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else source.read_text();exec(compile(text,str(source),'exec'),vars(mod))
tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');handler=next(n for n in main.body if isinstance(n,ast.ClassDef) and n.name=='Handler')
output=Path(sys.argv[1]);assert not output.exists();checks=[]
nonce=uuid.uuid4().hex;prompt='独立 '+nonce+'\n中间  空白 “精确”';managed='⟦主控 #1⟧\n'+prompt
expected={'messages':[{'role':'user','content':managed}]}
driver=ast.parse(source.with_name('run_t093_login_chain.py').read_text())
assignments=[node for node in ast.walk(driver) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='fixture' and isinstance(target.slice,ast.Constant) and target.slice.value=='expected_request_body' for target in node.targets)]
assert len(assignments)==1,'setup_must_supply_independent_managed_body'
namespace={'fixture':{'prompt':prompt}}
exec(compile(ast.fix_missing_locations(ast.Module(body=assignments,type_ignores=[])),'fixture_expected_body','exec'),namespace)
assert namespace['fixture']['expected_request_body']==expected,'setup_expected_body_must_match_external_contract'
checks.append({'case':'independent_setup_expectation','status':'PASS'})
for kind in ('managed_exact','json_encoding_only','raw_only','wrong_sequence','middle_space','CRLF','trailing_newline','extra_system','wrong_role','extra_message','extra_message_key','empty_messages'):
 payload=copy.deepcopy(expected)
 if kind=='raw_only':payload['messages'][0]['content']=prompt
 if kind=='wrong_sequence':payload['messages'][0]['content']=managed.replace('#1','#2')
 if kind=='middle_space':payload['messages'][0]['content']=managed.replace('  ',' ')
 if kind=='CRLF':payload['messages'][0]['content']=managed.replace('\n','\r\n')
 if kind=='trailing_newline':payload['messages'][0]['content']+='\n'
 if kind=='extra_system':payload['system']='unexpected system'
 if kind=='wrong_role':payload['messages'][0]['role']='assistant'
 if kind=='extra_message':payload['messages'].insert(0,{'role':'assistant','content':'prefix'})
 if kind=='extra_message_key':payload['messages'][0]['extra']=True
 if kind=='empty_messages':payload['messages']=[]
 body=json.dumps(payload,ensure_ascii=kind!='json_encoding_only',indent=2 if kind=='json_encoding_only' else None).encode('utf-8')
 try:
  with tempfile.TemporaryDirectory(prefix='t093-upstream-body-unit-',dir='/private/tmp') as temporary:
   root=Path(temporary);(root/'U').mkdir();ledger=root/'ledger.jsonl';ledger.write_text('{"kind":"request","sequence":1}\n')
   token='synthetic-only-'+uuid.uuid4().hex;received=[]
   namespace={**vars(mod),'root':root,'fixture':{'prompt':prompt,'expected_request_body':expected},'token':token,'received':received,'ledger':ledger}
   exec(compile(ast.fix_missing_locations(ast.Module(body=[handler],type_ignores=[])),str(source),'exec'),namespace)
   value=namespace['Handler'].__new__(namespace['Handler']);value.rfile=io.BytesIO(body);value.wfile=io.BytesIO();value.headers={'content-length':str(len(body)),'authorization':'Bearer '+token};value.command='POST';value.path='/v1/messages'
   value.send_response=lambda *args:None;value.send_header=lambda *args:None;value.end_headers=lambda:None
   value.do_POST();receipt=received[0]
   assert receipt['prompt_matches_fixture']==(kind in ('managed_exact','json_encoding_only')),'managed_prompt_body_must_match_exactly: '+kind
   assert token not in json.dumps(receipt) and prompt not in json.dumps(receipt),'upstream_receipt_must_not_publish_auth_or_prompt'
   checks.append({'case':kind,'status':'PASS','exact_match':receipt['prompt_matches_fixture']})
 except Exception as error:checks.append({'case':kind,'status':'FAIL','business_failure':str(error) if isinstance(error,AssertionError) else type(error).__name__})
status='PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL'
with output.open('x',encoding='utf-8') as f:json.dump({'status':status,'scope':'actual U handler over supplied byte streams; exact external managed envelope; no network/profile/CLI','checks':checks},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
