"""Reclaim only T-044-owned sessions through the public gate HTTP route."""
import json, sys, urllib.request, urllib.error
from pathlib import Path
here = Path(__file__).resolve().parent
label, fixture_path = sys.argv[1:]
fixture = json.loads(Path(fixture_path).read_text(encoding='utf-8'))
path = here / (label + '.jsonl')
assert not path.exists()
def request(route, body=None):
    req = urllib.request.Request('http://127.0.0.1:5817' + route,
        data=None if body is None else json.dumps(body).encode(), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=60) as response: status, raw = response.status,response.read().decode()
    except urllib.error.HTTPError as error: status,raw=error.code,error.read().decode()
    output=json.loads(raw)
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'path':route,'input':body,'status':status,'output':output},ensure_ascii=False)+'\n')
    return output
def gate(command,**args): return request('/api/a2a',{'command':command,'task':fixture['task'],**args})
before=gate('status')['task']
member=lambda: next(t for t in request('/api/a2a/membership')['tasks'] if t['taskId']==fixture['task'])
group=member()
assert {m['role'] for m in group['members']}=={'worker','reviewer'},group
reviewer=fixture['attached']['attachment']['thread_id']
reclaimed=gate('reclaim',thread=reviewer)
assert reclaimed['ok'],reclaimed
assert gate('status')['task']==before,'Ordinary reclaim changed delivery state'
assert next(m for m in member()['members'] if m['threadId']==reviewer)['endedAt']==reclaimed['attachment']['ended_at']
worker=before['current_attempt']
assert gate('reclaim',attempt=worker['attempt_id'])['ok']
after=member()
assert len(after['members'])==2 and all(m.get('endedAt') for m in after['members']),after
events=gate('events')['events']
attached=[e for e in events if e['type']=='attached']
assert len(attached)==1 and attached[0]['details']['attachment']['thread_id']==reviewer
assert any(e['type']=='attachment_reclaimed' and e['details']['attachment']['thread_id']==reviewer for e in events)
assert any(e['type']=='reclaimed' and e['details']['attempt']['attempt_id']==worker['attempt_id'] for e in events)
assert not any(e['type'] in ['submitted','verification_started','integrated'] for e in events)
print('PASS: two ended members, durable events, ordinary reclaim preserves business state')
