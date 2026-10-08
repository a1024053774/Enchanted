import json,subprocess,re,urllib.request,urllib.error,urllib.parse
from pathlib import Path
out=Path(__file__).resolve().parent

def connection():
 start=json.loads((out/'electron-start.json').read_text())
 ps=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True)
 matches=[]
 for line in ps.splitlines()[1:]:
  row=line.split(None,3)
  if len(row)==4 and int(row[2])==start['pgid'] and row[3].endswith('/Users/luckye/Documents/Code/synara/apps/server/dist/index.mjs'):matches.append(int(row[0]))
 assert len(matches)==1,matches
 env=subprocess.check_output(['ps','eww','-p',str(matches[0]),'-o','command='],text=True)
 token=re.search(r'(?:^| )SYNARA_AUTH_TOKEN=([0-9a-f]+)(?: |$)',env)
 port=re.search(r'(?:^| )SYNARA_PORT=(\d+)(?: |$)',env)
 assert token and port
 return 'http://127.0.0.1:'+port.group(1),token.group(1),matches[0]

def request(label,body=None,path='/api/a2a'):
 endpoint,token,pid=connection()
 url=endpoint+path+('&' if '?' in path else '?')+'token='+urllib.parse.quote(token)
 req=urllib.request.Request(url,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60) as r:status,raw=r.status,r.read().decode()
 except urllib.error.HTTPError as e:status,raw=e.code,e.read().decode()
 record={'endpoint':endpoint,'backend_pid':pid,'path':path,'input':body,'status':status,'body':json.loads(raw)}
 with (out/(label+'.json')).open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
 return record['body']
