"""Runner pre-spawn spies: approval, source and attempt gates; no process/root spawn."""
import argparse, importlib.util, json, os, subprocess, tempfile, uuid
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';RUNNER=BASE/'run-09b.py'
def module(source=None):
    text=source.read_text(encoding='utf-8') if isinstance(source,Path) else (source or RUNNER.read_text(encoding='utf-8'));scope={'__name__':'runner_spy_module','__file__':str(RUNNER)};exec(compile(text,str(RUNNER),'exec'),scope);return scope
def run_root_set():return {p for p in Path('/private/tmp').glob('t078-2-09b-run-*') if p.exists()}
def fixture(suffix):
    materials=BASE/('09b-run-spy-materials-'+suffix);materials.mkdir(exist_ok=False)
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    (materials/'static-check.json').write_text(json.dumps({'status':'PASS','launch_status':'NO_GO','revision':rev,'root':'/private/tmp/nonexistent'})+'\n')
    return materials,rev
def call_runner(materials,approval,out):
    return subprocess.run(['python3','-B',str(RUNNER),'--materials',str(materials),'--stage','A','--approval',str(approval),'--output',str(out)],cwd=SOURCE,capture_output=True,text=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=BASE/'09b-run-spies-02');args=parser.parse_args();out=args.output;out.mkdir(exist_ok=False);materials,rev=fixture(uuid.uuid4().hex[:8]);before=run_root_set();checks=[]
    def check(name,passed,observed):checks.append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','observed':observed})
    valid={'approved_by':'executor','stage':'A','approval_ref':'主控 #190','source_revision':rev,'allow_role_cli_spawn':False}
    bad_approval={**valid,'approved_by':'operator','stage':'B','approval_ref':'','allow_role_cli_spawn':True}
    bad_approval_mutant={**valid,'approved_by':'operator','stage':'B','approval_ref':''}
    bad_source={**valid,'source_revision':'0'*40}
    for name,payload in [('bad-approval',bad_approval),('bad-source',bad_source)]:
        ap=out/(name+'.json');ap.write_text(json.dumps(payload));target=out/(name+'-run');p=call_runner(materials,ap,target);after=run_root_set();result=json.loads((target/'result.json').read_bytes())
        check(name+'-real-entry-rejects-before-spawn',p.returncode!=0 and result.get('spawned') is False and 'root' not in result and before==after,{'exit':p.returncode,'result':result,'roots_added':sorted(map(str,after-before))})
    s=RUNNER.read_text(encoding='utf-8')
    bad_attempt={'attempt_id':'a','session_id':'s','fence':1,'thread_id':'t','workspace':''}
    mutant_attempt=s.replace("assert isinstance(attempt,dict) and all(attempt.get(k) not in [None,''] for k in required)","pass",1)
    good_attempt=module().get('validate_attempt');bad_validate=module(mutant_attempt).get('validate_attempt')
    try:bad_validate(bad_attempt);mutant_accepts=True
    except AssertionError:mutant_accepts=False
    try:good_attempt(bad_attempt);real_rejects=False
    except (AssertionError,KeyError):real_rejects=True
    check('attempt-receipt-mutant-red-and-fixed-green',mutant_accepts and real_rejects,{'mutant_accepts_empty_workspace':mutant_accepts,'real_rejects':real_rejects})
    mutant_approval=s.replace("assert approval.get('approved_by')=='executor' and approval.get('stage')=='A' and approval.get('approval_ref')","pass",1)
    mutant_source=s.replace("assert approval.get('source_revision')==static['revision'] and approval.get('allow_role_cli_spawn') is False","pass",1)
    valid_input={'approved_by':'executor','stage':'A','approval_ref':'x','source_revision':rev,'allow_role_cli_spawn':False}
    try:module(mutant_approval)['validate_stage_a_inputs'](materials,bad_approval_mutant);approval_mutant_accepts=True
    except AssertionError:approval_mutant_accepts=False
    try:module()['validate_stage_a_inputs'](materials,bad_approval);approval_real_rejects=False
    except AssertionError:approval_real_rejects=True
    try:module(mutant_source)['validate_stage_a_inputs'](materials,bad_source);source_mutant_accepts=True
    except AssertionError:source_mutant_accepts=False
    try:module()['validate_stage_a_inputs'](materials,bad_source);source_real_rejects=False
    except AssertionError:source_real_rejects=True
    check('approval-check-mutant-red-and-fixed-green',approval_mutant_accepts and approval_real_rejects,{'mutant_accepts':approval_mutant_accepts,'real_rejects':approval_real_rejects})
    check('source-check-mutant-red-and-fixed-green',source_mutant_accepts and source_real_rejects,{'mutant_accepts':source_mutant_accepts,'real_rejects':source_real_rejects})
    for check_result in checks:(out/(check_result['name']+'.json')).write_text(json.dumps(check_result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    record={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'Actual run-09b entry rejection plus source mutations; no daemon/API/target/role spawn','roots_before':sorted(map(str,before)),'roots_after':sorted(map(str,run_root_set())),'real_process_starts':0,'materials_fixture':str(materials)}
    (out/'results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':record['status'],'checks':len(checks)}));raise SystemExit(0 if record['status']=='PASS' else 1)
if __name__=='__main__':main()
