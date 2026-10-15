"""A06 executable-packet root gate: bad mutant rejected before runtime root."""
import argparse,json,tempfile,subprocess,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';RUNNER=BASE/'run-09b.py'
def load():
 s={'__name__':'a06_gate','__file__':str(RUNNER)};exec(compile(RUNNER.read_text(),str(RUNNER),'exec'),s);return s
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);scope=load();checks=[]
 with tempfile.TemporaryDirectory(dir='/private/tmp') as td:
  mat=Path(td);(mat/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':'0'*40,'root':'/private/tmp/missing-a06-root'}))
  try:scope['validate_stage_a_inputs'](mat,{'approved_by':'executor','stage':'A','approval_ref':'x','source_revision':'0'*40,'allow_role_cli_spawn':False});checks.append({'name':'missing-static-root-rejected-before-spawn','status':'INCOMPLETE'})
  except Exception as e:checks.append({'name':'missing-static-root-rejected-before-spawn','status':'PASS','error':repr(e)})
 with tempfile.TemporaryDirectory(dir='/tmp') as td:
  entry_out=Path(td)/'entry';bad_materials=BASE/'09b-a06-materials-02';approval=BASE/'a06-stage-a-approval-01.json'
  q=subprocess.run([sys.executable,'-B',str(RUNNER),'--materials',str(bad_materials),'--stage','A','--approval',str(approval),'--output',str(entry_out)],cwd=SOURCE,capture_output=True,text=True)
  entry=json.loads((entry_out/'result.json').read_bytes());entry_ok=q.returncode==1 and 'executable_material_static_root_required' in entry.get('traceback','') and 'root' not in entry
  checks.append({'name':'real-entry-missing-static-root-rejected-before-runtime-root','status':'PASS' if entry_ok else 'INCOMPLETE','exit_code':q.returncode,'root_field_present':'root' in entry,'error':entry.get('error')})
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'spawned':False,'roots_created':0,'scope':'A06 material gate via validator and real run-09b entry; no daemon/API/target/CLI'}
 (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
