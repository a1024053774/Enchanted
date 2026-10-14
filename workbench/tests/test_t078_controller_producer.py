"""Actual inbox client producer: controller identity, no daemon or vendor CLI."""
import argparse,json,os,subprocess,tempfile,uuid
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
source=Path(__file__).resolve().parents[2];root=Path(tempfile.mkdtemp(prefix='t78-producer-',dir='/tmp')).resolve();requests=root/'requests';requests.mkdir()
context={'schema':2,'launch':str(uuid.uuid4()),'preset':'ideation','project':'controller-project','task':'controller-task',
         'session':str(uuid.uuid4()),'native_session':None,'spec_rev':1,'prompt_id':str(uuid.uuid4())}
context['native_session']=context['session'];(requests/'controller-context').write_text(json.dumps(context),encoding='utf-8')
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','CLAUDE_','ANTHROPIC_'))}
env.update(A2A_ROLE='controller',A2A_LAUNCH=context['launch'],A2A_PRESET=context['preset'],A2A_PROJECT=context['project'],
 A2A_TASK=context['task'],A2A_SESSION=context['session'],A2A_NATIVE_SESSION=context['native_session'],A2A_SPEC_REV='1',
 A2A_CAPABILITY='fixture-only',A2A_REQUEST_DIR=str(requests),A2A_STATE=str(root/'absent-daemon'))
argv=['node',str(source/'workbench/bin/inbox'),'list','--role','executor'];r=subprocess.run(argv,cwd=source,env=env,capture_output=True,timeout=20)
(args.output/'stdout.bin').write_bytes(r.stdout);(args.output/'stderr.bin').write_bytes(r.stderr)
error=None;packet=None
try:
 assert r.returncode==0,'Valid controller producer must not require a daemon socket or a worker attempt'
 reply=json.loads(r.stdout);assert reply['queued'] and reply['delivered'] is False
 packet=json.loads(Path(reply['path']).read_bytes())
 assert all(packet[k]==v for k,v in context.items())
 assert 'attempt' not in packet and 'fence' not in packet and packet['command']=='inbox_list'
except Exception as e:error=str(e)
result={'status':'PASS' if error is None else 'INCOMPLETE','argv':argv,'exit_code':r.returncode,'error':error,'packet':packet,
 'context_input':context,'fixture':str(root),'scope':'Real library client to native request file; context is controlled input, no Stop/native authenticity claim','real_model_turns':0}
(args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'error':error}));raise SystemExit(0 if error is None else 1)
