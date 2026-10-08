import json,sys,subprocess,datetime
from pathlib import Path
from owned_api import connection,request
out=Path(__file__).resolve().parent;f=json.loads((out/'fixture.json').read_text());a=json.loads((out/'dispatch.json').read_text())['body']['attempt']
def rpc(label,tag,body):
 path=out/(label+'-input.json');path.write_text(json.dumps(body,ensure_ascii=False))
 endpoint,token,pid=connection();env=json.loads((out/'isolation.json').read_text())['env'];env.update(A2A_GATE_BEARER=token,A2A_RPC_TAG=tag)
 r=subprocess.run(['./a2a/scripts/bun','run','node',str(out/'native-rpc.mjs'),label,endpoint,str(path)],cwd='/Users/luckye/Documents/Code/synara',env=env,capture_output=True,text=True)
 (out/(label+'-command.json')).write_text(json.dumps({'argv':r.args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2));assert r.returncode==0,r.stderr
if __name__=='__main__':
 label=sys.argv[1]
 request('events-'+label,{'command':'events','task':f['task']});request('status-'+label,{'command':'status','task':f['task']})
 rpc('native-'+label,'orchestration.getThreadDetailSnapshot',{'threadId':a['thread_id']})
