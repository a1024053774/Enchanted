"""Stage-B pre-spawn spies: binding/approval/concurrency gates only."""
import argparse
import importlib.util
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
RUNNER = BASE / 'run-09b-stage-b.py'


def load():
    scope = {'__name__': 'stage_b_spies', '__file__': str(RUNNER)}
    exec(compile(RUNNER.read_text(encoding='utf-8'), str(RUNNER), 'exec'), scope)
    return scope


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    args.output.mkdir(parents=False, exist_ok=False); scope = load(); checks=[]
    static = json.loads((BASE / '09b-executable-materials-05/static-check.json').read_bytes())
    binding = {'root':'/private/tmp/t078-2-09b-run-94_wksxv','task':'t078-09b-runtime-2aab20d5','source_revision':static['revision'],
               'attempt':{'attempt_id':'766c797e-8d21-4941-8925-eb8d6462a7c0','session_id':'3d1411f5-0395-44e7-9691-c894556882e4','fence':1,'spec_rev':1,'thread_id':'c6961479-5c3a-4d29-862c-c49f41bfd083','workspace':'/private/tmp/t078-2-09b-run-94_wksxv/state/worktrees/t078-09b-runtime-project/t078-09b-runtime-2aab20d5-a1'},
               'pids':{'shell':70837,'leader':70839,'ideation_api':70730,'executor_api':70731,'daemon':70733},
               'identities':{}}
    p1_materials=args.output/'p1-materials'; p1_materials.mkdir(); (p1_materials/'input.json').write_text(json.dumps({'root':binding['root'],'preset':'ideation','task':binding['task']})+'\n')
    approval={'approved_by':'executor','stage':'B','approval_ref':'主控 #203 B1','allow_role_cli_spawn':True,'source_revision':static['revision'],
              'role':'ideation','phase':'B1','binding':binding,'screen_approvals':scope['expected_screen_plan'](),
              'tool_approval':{'key':'Enter','purpose':'one-time-tool-approval','selected_label':'1. Yes','one_time':True},'stop_after':'first-screen','p1_materials':str(p1_materials),'p1_phase':'launch','p1_args':[]}
    def check(name, fn):
        try: fn(); checks.append({'name':name,'status':'INCOMPLETE'})
        except Exception as error: checks.append({'name':name,'status':'PASS','error':repr(error)})
    check('missing-B-approval-rejected-before-spawn', lambda: scope['validate_role_approval']({},binding,BASE/'09b-executable-materials-05','ideation','B1'))
    bad={**approval,'binding':{**binding,'attempt':{**binding['attempt'],'fence':2}}}
    check('readiness-binding-mismatch-rejected-before-spawn', lambda: scope['validate_role_approval'](bad,binding,BASE/'09b-executable-materials-05','ideation','B1'))
    gate=scope['RoleGate'](); gate.admit('ideation'); check('second-role-while-first-active-rejected', lambda: gate.admit('ideation'))
    checks.append({'name':'valid-ideation-B1-approval-accepted-no-spawn','status':'PASS' if scope['validate_role_approval'](approval,binding,BASE/'09b-executable-materials-05','ideation','B1') else 'INCOMPLETE','spawned':False})
    source=RUNNER.read_text(encoding='utf-8')
    bad_approval={**approval,'approved_by':'operator'}
    mutant_approval=source.replace("assert approval.get('approved_by') == 'executor' and approval.get('stage') == 'B'", "assert approval.get('stage') == 'B'", 1)
    mutated=load(); mutated_scope={'__name__':'mutated','__file__':str(RUNNER)}; exec(compile(mutant_approval,str(RUNNER),'exec'),mutated_scope)
    try: mutated_scope['validate_role_approval'](bad_approval,binding,BASE/'09b-executable-materials-05','ideation','B1'); mutant_accepts=True
    except Exception: mutant_accepts=False
    checks.append({'name':'approval-mutant-accepts-bad-approver','status':'PASS' if mutant_accepts else 'INCOMPLETE','mutant_accepts':mutant_accepts})
    bad_binding={**approval,'binding':{**binding,'attempt':{**binding['attempt'],'fence':2}}}
    mutant_binding=source.replace("assert approval.get('binding') == binding", "assert True", 1); mutated_scope={'__name__':'mutated_binding','__file__':str(RUNNER)}; exec(compile(mutant_binding,str(RUNNER),'exec'),mutated_scope)
    try: mutated_scope['validate_role_approval'](bad_binding,binding,BASE/'09b-executable-materials-05','ideation','B1'); mutant_accepts_binding=True
    except Exception: mutant_accepts_binding=False
    checks.append({'name':'binding-mutant-accepts-stale-readiness','status':'PASS' if mutant_accepts_binding else 'INCOMPLETE','mutant_accepts':mutant_accepts_binding})
    mutant_concurrency=source.replace("assert self.active is None, 'second role cannot start while another role is active'", "assert True", 1); mutated_scope={'__name__':'mutated_concurrency','__file__':str(RUNNER)}; exec(compile(mutant_concurrency,str(RUNNER),'exec'),mutated_scope)
    mutant_gate=mutated_scope['RoleGate'](); mutant_gate.admit('ideation')
    try: mutant_gate.admit('ideation'); mutant_accepts_concurrency=True
    except Exception: mutant_accepts_concurrency=False
    checks.append({'name':'concurrency-mutant-accepts-second-active-role','status':'PASS' if mutant_accepts_concurrency else 'INCOMPLETE','mutant_accepts':mutant_accepts_concurrency})
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'Pure Stage-B entry gate; no Claude CLI, pane input, API, daemon, target or model spawn','spawned':False,'real_process_starts':0}
    (args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__': main()
