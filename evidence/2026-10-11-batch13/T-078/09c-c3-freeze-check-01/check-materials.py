"""Read the complete C3 freeze and its future command bindings; no launch."""
import argparse
import ast
import copy
import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
MATERIAL=BASE/'09c-attempt-3-materials-01';PACKET=BASE/'09c-executable-materials-05'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    static=json.loads((PACKET/'static-check.json').read_bytes());approval=json.loads((MATERIAL/'stage-a-approval.json').read_bytes())
    provenance=json.loads((MATERIAL/'SOURCE.json').read_bytes())
    assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['allow_role_cli_spawn'] is False
    assert static['revision']==approval['source_revision']==provenance['revision']=='8f359d3640702b6e36bac282237250f19128495d'
    assert static['runtime_source_revision']==approval['runtime_source_revision']==provenance['runtime_source_revision']=='77865b044b5a5fedeeec12e62eae1314b87bf885'
    assert static['real_cli_starts']==static['api_starts']==static['target_starts']==0
    assert static['scene']=='09C' and static['protocol'] is True and static['approval_fields_empty'] is True
    runner=module('C3_Stage_A',BASE/'run-09b.py')
    validation=runner.validate_regression_readbacks(static,approval);runner.validate_material_lineage(PACKET,static)
    try:runner.validate_stage_a_inputs(PACKET,approval,protocol=True)
    except AssertionError:pass
    else:raise AssertionError('unsigned Stage A accepted')
    signed={**approval,'approved_by':'executor','approval_ref':'UNIT ONLY static validator; never launch'}
    accepted=runner.validate_stage_a_inputs(PACKET,signed,protocol=True)
    assert accepted['regression_validation']==validation
    # One Git archive replaces hundreds of Git subprocesses. Compare bytes,
    # including all seven receipt originals, without computing fingerprints.
    receipts=[*approval['regression_readbacks'],approval['harness_rehearsal'],approval['harness_kernel_check'],approval['coordinator_rehearsal']]
    receipt_paths=[str(Path(p).relative_to(SOURCE)) for p in receipts]
    archived=subprocess.check_output(['git','archive','--format=tar',static['revision'],'--',*static['source_paths'],*receipt_paths],cwd=SOURCE)
    with tarfile.open(fileobj=io.BytesIO(archived)) as git, tarfile.open(PACKET/'sources.tar.gz') as frozen:
        names=frozen.getnames();assert len(names)==len(set(names)) and set(names)==set(static['source_paths'])
        for name in names:assert frozen.extractfile(name).read()==git.extractfile(name).read()==(SOURCE/name).read_bytes(),name
        for name in receipt_paths:assert git.extractfile(name).read()==(SOURCE/name).read_bytes(),name
    assert json.loads((PACKET/'source-files.json').read_bytes())==static['source_paths']
    assert all('workbench/tests/'+name in names for name in ['p1_output.py','p1_reuse.py','p1_endpoint.py','p1_processes.py',
        'command_evidence.py','electron_client.py','t078_raw_retention.py','test_t078_child_reaping.py'])
    assert (MATERIAL/'i1-prompt.txt').read_bytes()==(BASE/'09c-attempt-2-materials-02/i1-prompt.txt').read_bytes()
    budget=json.loads((MATERIAL/'BUDGET.json').read_bytes());assert budget['ideation']=={'roots':4,'POST':7} and budget['executor']=={'roots':1,'POST':1}
    assert budget['real_model_turns']==0 and budget['tool_permissions']==3
    commands=[];future_flags={'--stage-a','--ideation','--executor'}
    for name in ['STAGE-A-COMMAND.txt','ROLE-MATERIAL-COMMANDS.txt','OWNER-BIND-COMMAND.txt','RUNTIME-COMMAND-MATERIALS.txt']:
        for line in (MATERIAL/name).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):continue
            argv=shlex.split(line);assert Path(argv[0]).is_file() and argv[1]=='-B' and Path(argv[2]).is_file()
            for flag in ['--materials','--packet','--prompt-file','--approval']:
                if flag in argv:assert Path(argv[argv.index(flag)+1]).exists(),(name,flag)
            output=Path(argv[argv.index('--output')+1]);assert not output.exists(),output
            future={flag:argv[argv.index(flag)+1] for flag in future_flags if flag in argv}
            assert all('09c-c3-' in path or '09c-stage-a-03' in path for path in future.values()),future
            commands.append({'file':name,'argv':argv,'entry_and_existing_inputs':'PASS','future_inputs':future,'new_output':str(output)})
    assert len(commands)==5
    body=(MATERIAL/'CLOCK-ORIGIN-SAVE-COMMAND.txt').read_text(encoding='utf-8')
    ast.parse(body.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0])
    subprocess.run(['zsh','-n',str(MATERIAL/'CLOCK-ORIGIN-SAVE-COMMAND.txt')],check=True)
    assert '09c-stage-a-03/readiness.json' in body and '09c-c3-b1-ideation-p1-01/phases/C-I1/execute-02/clock-origin.json' in body
    assert all(not (BASE/name).exists() for name in ['09c-stage-a-03','09c-c3-preparation-01','09c-c3-b1-ideation-p1-01','09c-c3-b1-executor-p1-01'])
    # Recount the actual rehearsal tar independently of its top-level PASS.
    sys.path.insert(0,str(SOURCE/'workbench/tests'));from t078_raw_retention import readback
    counts=readback(BASE/'09c-caffeinate-parity-rehearsal-02/flow/retention-archive/scene.tar.gz')
    assert counts['Messages_POST']=={'ideation':7,'executor':1} and counts['roots']=={'ideation':4,'executor':1}
    assert len(counts['permission_requests']['ideation'])==3 and not counts['permission_requests']['executor']
    assert not counts['unfinished_http'] and not counts['unfinished_hooks']
    result={'status':'PASS','source_revision':static['revision'],'runtime_source_revision':static['runtime_source_revision'],
        'source_file_bytes_compared':len(names),'bound_receipt_bytes_compared':receipt_paths,'regression_validation':validation,
        'unsigned_Stage_A':'REJECTED','signed_fixture_stage_A_validator':'PASS; no runner main invocation',
        'commands':commands,'clock_save_heredoc':'AST/shell PASS; actual future inputs not opened',
        'runtime_bindings':'NOT_CREATED; require actual new Stage A and B1','rehearsal_raw_recount':counts,
        'scene_process_starts':0,'models':0,'key_writes':0,'signature_writes':0}
    with (args.output/'result.json').open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','source_files':len(names),'bound_receipts':7,'commands':len(commands),'unsigned_Stage_A':'REJECTED','scene_starts':0}))


if __name__=='__main__':main()
