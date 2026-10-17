"""Stop C3 generators at their command boundary; no launch/build/gate calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch
import t078_09c_timed_run as timed

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
class Captured(Exception):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','scene_starts':0,'subprocess_starts':0}
    try:
        spec=importlib.util.spec_from_file_location('C_materials',BASE/'prepare-c2-runtime.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='t078-C3-paths-',dir='/private/tmp') as tmp:
            root=Path(tmp);seen=[]
            args=SimpleNamespace(output=root/'new-role',instance='c3',preparation=root/'c3-preparation',prompt_file=root/'prompt',
                role='ideation',stage_a=root/'stage-a',packet=root/'packet')
            def command(argv,**kwargs):seen.append(list(map(str,argv)));raise Captured()
            try:
                with patch.object(module.subprocess,'run',command):module.role(args)
            except Captured:pass
            assert len(seen)==1 and seen[0][seen[0].index('--instance')+1]=='c3','C3 role must not use C2 instance'
            p1=root/'actual-I';p1.mkdir();(p1/'input.json').write_text(json.dumps({'root':str(root),'session':'actual-session'}))
            actual_E=root/'actual-E'
            (root/'protocol-plan.json').write_text(json.dumps({'roles':{'executor':{'readiness_file':str(actual_E/'readiness.json')}}}))
            args=SimpleNamespace(output=root/'observe',p1=p1,approval=root/'policy',stage_a=root/'stage-a');captured=[]
            def constructor(namespace,out):captured.append(namespace);raise Captured()
            try:
                with patch.object(timed,'Timed',constructor):module.observe_C1(args)
            except Captured:pass
            assert len(captured)==1 and captured[0].executor==actual_E,'executor P1 must come from actual plan readiness binding'
            result.update(status='PASS',role_command=seen[0],executor=str(captured[0].executor),scope='actual producer functions at pre-spawn boundary')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    with (a.output/'result.json').open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'error':result.get('error'),'scene_starts':0}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
