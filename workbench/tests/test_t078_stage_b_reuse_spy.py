"""Green stage-B reuse spy: approval plans existing API, never starts one."""
import argparse, importlib.util, json
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';RUNNER=BASE/'run-09b-stage-b.py'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False)
 scope={'__name__':'reuse_spy','__file__':str(RUNNER)};exec(compile(RUNNER.read_text(),str(RUNNER),'exec'),scope)
 binding={'root':'/private/tmp/t078-2-09b-run-94_wksxv','task':'t078-09b-runtime-2aab20d5','source_revision':json.loads((BASE/'09b-executable-materials-05/static-check.json').read_bytes())['revision'],'attempt':{'attempt_id':'766c797e-8d21-4941-8925-eb8d6462a7c0','session_id':'3d1411f5-0395-44e7-9691-c894556882e4','fence':1,'spec_rev':1,'thread_id':'c6961479-5c3a-4d29-862c-c49f41bfd083','workspace':'/private/tmp/t078-2-09b-run-94_wksxv/state/worktrees/t078-09b-runtime-project/t078-09b-runtime-2aab20d5-a1'},'pids':{},'identities':{}}
 pm=a.output/'p1';pm.mkdir();(pm/'input.json').write_text(json.dumps({'root':binding['root'],'preset':'ideation','task':binding['task']}))
 approval={'approved_by':'executor','stage':'B','approval_ref':'reuse-spy','allow_role_cli_spawn':True,'source_revision':binding['source_revision'],'role':'ideation','phase':'B1','binding':binding['attempt'],'screen_approvals':scope['expected_screen_plan'](),'tool_approval':{'key':'Enter','purpose':'one-time-tool-approval','selected_label':'1. Yes','one_time':True},'stop_after':'first-screen','p1_materials':str(pm),'p1_phase':'launch','p1_args':['--reuse-stage-a','--reuse-api-root',binding['root']+'/roles/ideation']}
 scope['validate_role_approval'](approval,binding,BASE/'09b-executable-materials-05','ideation','B1')
 result={'status':'PASS','checks':[{'name':'existing-api-bound-by-root-and-role','status':'PASS'},{'name':'no-api-or-cli-spawn','status':'PASS','spawned':False,'api_starts':0,'cli_starts':0}],'scope':'Pure reuse approval preflight; no API/CLI/daemon/pane action','spawned':False,'api_starts':0,'cli_starts':0}
 (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
