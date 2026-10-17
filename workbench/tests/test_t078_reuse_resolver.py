"""Red/green resolver checks for the bound 09B fake API."""
import argparse, json, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p1_reuse import resolve_reused_api
BASE=Path(__file__).resolve().parents[2]/'evidence/2026-10-11-batch13/T-078'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False)
 source=json.loads((BASE/'09b-stage-a-05/readiness.json').read_bytes()); entry=source['api_processes'][0]
 with tempfile.TemporaryDirectory(dir='/private/tmp') as td:
  root=Path(td);api=root/'roles/ideation';api.mkdir(parents=True);ready=dict(entry['ready']);(api/'api-ready.json').write_text(json.dumps(ready));readiness=root/'readiness.json';readiness.write_text(json.dumps({'api_processes':[entry]}))
  identity={'pid':entry['pid'],'started':'Wed Oct 14 21:05:48 2026','command':' '.join(entry['argv'])}
  template={'preset':'ideation','launch':'launch','session':'session','api_url':'http://127.0.0.1:0'}
  def probe(_): return identity
  checks=[]
  try: resolve_reused_api(template,api,readiness,probe);checks.append({'name':'valid-green','status':'PASS'})
  except Exception as e: checks.append({'name':'valid-green','status':'INCOMPLETE','error':repr(e)})
  mutants=[('pid-mismatch',lambda r:r.update(pid=r['pid']+1)),('role-mismatch',lambda r:r.update(role='executor')),('stage-mismatch',lambda r:r.update(stage='B')),('invalid-port',lambda r:r.update(port=0)),('readiness-mismatch',lambda r:r.update(api_url='http://127.0.0.1:1'))]
  for name,mutate in mutants:
   bad=dict(ready);mutate(bad);(api/'api-ready.json').write_text(json.dumps(bad))
   try: resolve_reused_api(template,api,readiness,probe);checks.append({'name':name,'status':'INCOMPLETE'})
   except Exception as e: checks.append({'name':name,'status':'PASS','error':repr(e)})
   (api/'api-ready.json').write_text(json.dumps(ready))
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'resolver only; no ps/network/API/CLI/daemon/pane mutation','spawned':False}
 (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
