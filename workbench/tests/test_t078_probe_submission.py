"""Recorded submission identifiers at the failed final TURN assertion; no live control."""
import argparse
import ast
import copy
import json
from pathlib import Path
import traceback
import t078_topology_probe as probe

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--old-source',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    rows=json.loads((BASE/'09c-caffeinate-fix-01/submission-events.json').read_bytes())
    queued=json.loads((BASE/'09c-topology-probe-run-01/turn-01/dispatch.json').read_bytes())['dispatch']
    submitted=next(r for r in rows if r['type']=='turn_submitted')
    status={'state':'busy','active':submitted['data'],'failed':None,'scope':'reconstructed from actual turn_submitted, not a lost historical pane_status original'}
    result={'status':'INCOMPLETE','scene_actions':0,'status_scope':status['scope']}
    try:
        if a.old_source:
            tree=ast.parse(a.old_source.read_text(encoding='utf-8'))
            call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require'
                and any(isinstance(arg,ast.Constant) and arg.value=='same actual dispatch remains active at PermissionRequest' for arg in n.args))
            expression=ast.Expression(call);ast.fix_missing_locations(expression)
            eval(compile(expression,str(a.old_source),'eval'),{'require':probe.require,'status':status,'dispatch':{'dispatch':queued}})
            raise AssertionError('old incorrect comparison unexpectedly accepted the real distinct identifiers')
        checks=[]
        for case in ['green','wrong-dispatch','wrong-submission','missing-active','idle','failed','duplicate-receipt']:
            current=copy.deepcopy(status);events=copy.deepcopy(rows)
            if case=='wrong-dispatch':current['active']['dispatch']='foreign'
            if case=='wrong-submission':current['active']['id']='foreign'
            if case=='missing-active':current['active']=None
            if case=='idle':current['state']='idle'
            if case=='failed':current['failed']='native failure'
            if case=='duplicate-receipt':events.append(copy.deepcopy(submitted))
            error=None
            try:probe.verify_active_submission(current,queued,events)
            except AssertionError as ex:error=repr(ex)
            assert (error is None)==(case=='green'),(case,error)
            checks.append({'case':case,'status':'PASS','error':error})
        result.update(status='PASS',checks=checks)
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    with (a.output/'result.json').open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'error':result.get('error'),'checks':len(result.get('checks',[]))}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
