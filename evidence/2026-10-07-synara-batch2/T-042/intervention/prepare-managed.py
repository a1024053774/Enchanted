import json
from pathlib import Path
from owned_api import request
out=Path(__file__).resolve().parent
f=json.loads((out/'fixture.json').read_text())
Path(f['instructions']).write_text('本次仅验证人工介入。只回复 OK；不要调用工具、修改文件、提交或交付。',encoding='utf-8')
r=request('create',dict(command='create',**{k:f[k] for k in ['task','project','repo','base','oracle','instructions']}));assert r['ok'],r
r=request('dispatch',{'command':'dispatch','task':f['task'],'runtimeMode':'full-access'});assert r['ok'],r
a=r['attempt']
r=request('membership',{'command':'save','task':{'taskId':f['task'],'projectId':f['project'],'title':'人工介入复验','revision':0,'members':[{'threadId':a['thread_id'],'role':'worker'}]}},'/api/a2a/membership');assert r['ok'],r
request('events-before',{'command':'events','task':f['task']})
