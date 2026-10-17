"""Read-only check of the frozen attempt-2 packet and deferred command paths."""
import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
MATERIAL=BASE/'09c-attempt-2-materials-02';PACKET=BASE/'09c-executable-materials-04'


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    static=json.loads((PACKET/'static-check.json').read_bytes());approval=json.loads((MATERIAL/'stage-a-approval.json').read_bytes())
    assert static['runtime_source_revision']==approval['runtime_source_revision']=='dc15dc3f0169f8689c5cded440676031cfa48bf5'
    assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['allow_role_cli_spawn'] is False
    runner=module(BASE/'run-09b.py','check_C2_stageA')
    report=runner.validate_regression_readbacks(static,approval);assert report['status']=='PASS'
    runner.validate_material_lineage(PACKET,static)
    try:runner.validate_stage_a_inputs(PACKET,approval,protocol=True)
    except AssertionError:pass
    else:raise AssertionError('unsigned Stage A accepted')
    revalidation=module(BASE/'c2-revalidation.py','check_C2_delta');negative=[]
    bad=copy.deepcopy(approval);bad['harness_rehearsal']='unrelated.json'
    try:revalidation.validate(static,bad)
    except AssertionError as error:negative.append({'case':'wrong-rehearsal','status':'PASS','error':str(error)})
    else:raise AssertionError('wrong rehearsal accepted')
    bad=copy.deepcopy(approval);bad['runtime_source_revision']='unrehearsed-runtime'
    try:revalidation.validate(static,bad)
    except AssertionError as error:negative.append({'case':'wrong-runtime-revision','status':'PASS','error':str(error)})
    else:raise AssertionError('unrehearsed runtime accepted')
    real=subprocess.check_output
    def altered(argv,*a,**kw):
        if argv[:3]==['git','diff','--name-only']:
            value=real(argv,*a,**kw)
            return value+'workbench/src/panes.ts\n'
        return real(argv,*a,**kw)
    with patch.object(revalidation.subprocess,'check_output',altered):
        try:revalidation.validate(static,approval)
        except AssertionError as error:negative.append({'case':'additional-product-delta','status':'PASS','error':str(error)})
        else:raise AssertionError('product delta accepted')
    with tarfile.open(PACKET/'sources.tar.gz') as arc:
        assert len(arc.getnames())==len(set(arc.getnames())) and set(arc.getnames())==set(static['source_paths'])
        for relative in arc.getnames():assert arc.extractfile(relative).read()==(SOURCE/relative).read_bytes()
    checks=[]
    deferred={'--stage-a','--ideation','--executor'}
    for name in ['STAGE-A-COMMAND.txt','ROLE-MATERIAL-COMMANDS.txt','OWNER-BIND-COMMAND.txt','RUNTIME-COMMAND-MATERIALS.txt']:
        for line in (MATERIAL/name).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):continue
            argv=shlex.split(line);assert Path(argv[0]).is_file() and argv[1]=='-B' and Path(argv[2]).is_file()
            for flag in ['--materials','--packet','--prompt-file','--approval']:
                if flag in argv:assert Path(argv[argv.index(flag)+1]).exists(),(name,flag)
            out=Path(argv[argv.index('--output')+1]);assert not out.exists(),out
            wait={flag:argv[argv.index(flag)+1] for flag in deferred if flag in argv}
            checks.append({'file':name,'argv':argv,'program_exists':True,'existing_inputs_checked':True,
                'future_inputs':wait,'output_absent':str(out)})
    heredoc=(MATERIAL/'CLOCK-ORIGIN-SAVE-COMMAND.txt').read_text(encoding='utf-8')
    body=heredoc.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    ast.parse(body);compile(body,'CLOCK-ORIGIN-SAVE-COMMAND.txt','exec')
    subprocess.run(['zsh','-n',str(MATERIAL/'CLOCK-ORIGIN-SAVE-COMMAND.txt')],check=True)
    result={'status':'PASS','source_revision':static['revision'],'runtime_source_revision':static['runtime_source_revision'],'source_files_bytes_compared':len(static['source_paths']),
        'regression_validation':report,'unsigned_Stage_A':'REJECTED','negative_cases':negative,'commands':checks,
        'runtime_bindings':'NOT_CREATED; deferred inputs require actual new Stage A and B1',
        'clock_save_heredoc':'AST/shell PASS; input/output deferred to actual C-I1',
        'scene_process_starts':0,'models':0,'key_writes':0}
    with (args.output/'result.json').open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','source_files':len(static['source_paths']),'command_count':len(checks),
        'unsigned_Stage_A':'REJECTED','scene_process_starts':0}))


if __name__=='__main__':main()
