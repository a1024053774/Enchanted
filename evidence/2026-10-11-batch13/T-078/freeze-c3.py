"""Freeze attempt 3 only after new kernel and full nine-process rehearsal PASS; no launch."""
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
MATERIAL=BASE/'09c-attempt-3-materials-01';PACKET=BASE/'09c-executable-materials-05';STAGE=BASE/'09c-stage-a-03'


def load(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def save(path,value):
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def command(path,argv):
    with path.open('x',encoding='utf-8') as f:f.write(shlex.join(list(map(str,argv)))+'\n')


def main():
    gate=load('c3-revalidation');receipt=gate.receipts()  # Refuse before material mutation or root creation.
    assert not PACKET.exists() and not STAGE.exists() and not (MATERIAL/'stage-a-approval.json').exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    argv=[sys.executable,'-B',BASE/'prepare-09b-executable.py','--scene','09C','--label',PACKET.name,'--protocol','--prompt-file',MATERIAL/'i1-prompt.txt']
    result=subprocess.run(list(map(str,argv)),cwd=SOURCE,capture_output=True,text=True,timeout=300)
    save(MATERIAL/'prepare.json',{'argv':list(map(str,argv)),'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    assert result.returncode==0,'prepare_failed_no_retry'
    runner=load('run-09b');readbacks=[str(BASE/name/'result.json') for name in runner.REGRESSION_REPORTS]
    static=json.loads((PACKET/'static-check.json').read_bytes());delta=['workbench/tests/'+name for name in gate.REPAIRS]+gate.META
    binding={'regression_readbacks':readbacks,'harness_profile':'c3-caffeinate-v1','harness_rehearsal':str(gate.REHEARSAL/'result.json'),
             'runtime_source_revision':receipt['source_revision'],'harness_delta_paths':delta}
    static.update(binding);(PACKET/'static-check.json').write_text(json.dumps(static,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    approval={'approved_by':None,'approval_ref':None,'stage':'A','scene':'09C','source_revision':revision,'launch_status':'NO_GO',
        'allow_role_cli_spawn':False,'protocol':True,'materials':PACKET.name,'final_protocol_api':True,'protocol_tag':'rev2-raw-c-profile-v1',
        'fixture_profile':'rev2-registered-raw-v1','real_vendor_model_turns':0,**binding}
    verification=runner.validate_regression_readbacks(static,approval);runner.validate_material_lineage(PACKET,static)
    save(MATERIAL/'stage-a-approval.json',approval)
    command(MATERIAL/'STAGE-A-COMMAND.txt',[sys.executable,'-B',BASE/'run-09b.py','--materials',PACKET,'--stage','A','--protocol',
        '--approval',MATERIAL/'stage-a-approval.json','--output',STAGE])
    roles=[];preparation=BASE/'09c-c3-preparation-01'
    for role in ['ideation','executor']:
        roles.append(shlex.join(list(map(str,[sys.executable,'-B',BASE/'prepare-c2-runtime.py','--mode','role','--instance','c3','--preparation',preparation,
            '--role',role,'--prompt-file',MATERIAL/'i1-prompt.txt','--stage-a',STAGE,'--packet',PACKET,'--output',BASE/('09c-c3-b1-'+role+'-p1-01')]))))
    with (MATERIAL/'ROLE-MATERIAL-COMMANDS.txt').open('x',encoding='utf-8') as f:f.write('\n\n'.join(roles)+'\n')
    ideation=BASE/'09c-c3-b1-ideation-p1-01';executor=BASE/'09c-c3-b1-executor-p1-01'
    command(MATERIAL/'OWNER-BIND-COMMAND.txt',[sys.executable,'-B',BASE/'prepare-rev2-owner.py','--mode','owner','--stage-a',STAGE,
        '--packet',PACKET,'--ideation',ideation,'--executor',executor,'--output',MATERIAL/'owner.json'])
    command(MATERIAL/'RUNTIME-COMMAND-MATERIALS.txt',[sys.executable,'-B',BASE/'prepare-c2-runtime.py','--mode','bind',
        '--stage-a',STAGE,'--packet',PACKET,'--ideation',ideation,'--executor',executor,'--output',preparation])
    save(MATERIAL/'SOURCE.json',{'status':'PASS','revision':revision,'runtime_source_revision':receipt['source_revision'],
        'regression_validation':verification,'snapshot':str(PACKET/'sources.tar.gz'),'scene_starts':0,'launch_status':'NO_GO'})
    print(json.dumps({'status':'PASS','source_revision':revision,'materials':str(MATERIAL),'scene_starts':0}))


if __name__=='__main__':main()
