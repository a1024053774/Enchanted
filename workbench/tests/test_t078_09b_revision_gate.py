"""Revision lineage spy for the stage-A runner; no spawn."""
import argparse, importlib.util, json
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';RUNNER=BASE/'run-09b.py'
def load():
 s={'__name__':'revision_gate_spy','__file__':str(RUNNER)};exec(compile(RUNNER.read_text(encoding='utf-8'),str(RUNNER),'exec'),s);return s
def main():
 p=argparse.ArgumentParser();p.add_argument('--materials',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);static=json.loads((a.materials/'static-check.json').read_bytes());scope=load();checks=[]
 try:scope['validate_material_lineage'](a.materials,static);checks.append({'name':'ancestor-and-ticket-only-current-lineage','status':'PASS'})
 except Exception as e:checks.append({'name':'ancestor-and-ticket-only-current-lineage','status':'INCOMPLETE','error':repr(e)})
 try:scope['validate_material_lineage'](a.materials,static,['workbench/src/claudeLaunch.ts']);checks.append({'name':'workbench-change-is-rejected','status':'INCOMPLETE'})
 except Exception as e:checks.append({'name':'workbench-change-is-rejected','status':'PASS','error':repr(e)})
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'Revision gate only; no runner stage, daemon, API, target or role process','spawned':False,'roots_created':0,'real_process_starts':0}
 (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
