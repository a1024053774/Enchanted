"""Freeze attempt-2 source and unsigned Stage A material; do not launch a scene."""
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
MATERIAL=BASE/'09c-attempt-2-materials-02';PACKET=BASE/'09c-executable-materials-04'
STAGE_A=BASE/'09c-stage-a-02'


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def text(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(value)


def cmd(argv):return shlex.join(list(map(str,argv)))+'\n'


def main():
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    assert not subprocess.check_output(['git','diff','HEAD','--','workbench','acceptance','scripts',str(BASE/'run-09b.py'),str(BASE/'prepare-09b-executable.py')],cwd=SOURCE)
    assert not PACKET.exists() and not STAGE_A.exists()
    assert not subprocess.check_output(['git','diff','7a6edbff8','--','workbench/src','workbench/app','acceptance'],cwd=SOURCE)
    revalidation=load_module(BASE/'c2-revalidation.py','C2_revalidation')
    rehearsal=str(revalidation.REHEARSAL/'result.json')
    raw=json.loads(Path(rehearsal).read_bytes());assert raw['status']=='PASS' and raw['source_revision']==revalidation.REPAIR_REVISION
    assert not subprocess.check_output(['git','diff',revalidation.REPAIR_REVISION,'--','workbench','acceptance','scripts'],cwd=SOURCE), 'runtime must match the completed coordinator rehearsal'
    prepare=[sys.executable,'-B',BASE/'prepare-09b-executable.py','--scene','09C','--label',PACKET.name,'--protocol',
             '--prompt-file',MATERIAL/'i1-prompt.txt']
    generated=subprocess.run(list(map(str,prepare)),cwd=SOURCE,capture_output=True,text=True,timeout=300)
    save(MATERIAL/'prepare.json',{'argv':list(map(str,prepare)),'exit_code':generated.returncode,'stdout':generated.stdout,'stderr':generated.stderr})
    assert generated.returncode==0,'prepare failed; preserve output; no retry'
    static=json.loads((PACKET/'static-check.json').read_bytes());assert static['revision']==revision
    runner=load_module(BASE/'run-09b.py','C2_stage_a')
    readbacks=[str(BASE/name/'result.json') for name in runner.REGRESSION_REPORTS]
    delta=['workbench/tests/'+name for name in revalidation.REPAIRS]+revalidation.NEW_FILES+[str(BASE.relative_to(SOURCE)/'prepare-09b-executable.py')]
    static.update(regression_readbacks=readbacks,harness_rehearsal=rehearsal,harness_delta_paths=delta,
                  runtime_source_revision=revalidation.REPAIR_REVISION)
    (PACKET/'static-check.json').write_text(json.dumps(static,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    approval={'approved_by':None,'approval_ref':None,'stage':'A','scene':'09C','source_revision':revision,
       'launch_status':'NO_GO','protocol':True,'materials':PACKET.name,'allow_role_cli_spawn':False,
       'final_protocol_api':True,'protocol_tag':'rev2-raw-c-profile-v1','fixture_profile':'rev2-registered-raw-v1',
       'real_vendor_model_turns':0,'regression_readbacks':readbacks,'harness_rehearsal':rehearsal,'harness_delta_paths':delta,
       'runtime_source_revision':revalidation.REPAIR_REVISION,
       'actions':['preflight task card before root or spawn','start two detached fake APIs and daemon',
           'real managed deterministic target dispatch/claim; bind original PID/argv/lstart',
           'stop at READY_FOR_APPROVAL; no role CLI; fresh attempt-2 root only']}
    save(MATERIAL/'stage-a-approval.json',approval)
    regression=runner.validate_regression_readbacks(static,approval)
    runner.validate_material_lineage(PACKET,static)
    with tarfile.open(PACKET/'sources.tar.gz') as archive:
        assert set(archive.getnames())==set(static['source_paths'])
        for name in static['source_paths']:
            assert archive.extractfile(name).read()==(SOURCE/name).read_bytes()==subprocess.check_output(['git','show',revision+':'+name],cwd=SOURCE)
    stage=[sys.executable,'-B',BASE/'run-09b.py','--materials',PACKET,'--stage','A','--protocol',
           '--approval',MATERIAL/'stage-a-approval.json','--output',STAGE_A]
    text(MATERIAL/'STAGE-A-COMMAND.txt',cmd(stage))
    role_commands=[]
    for role in ['ideation','executor']:
        role_commands.append(cmd([sys.executable,'-B',BASE/'prepare-c2-runtime.py','--mode','role','--role',role,
            '--prompt-file',MATERIAL/'i1-prompt.txt','--stage-a',STAGE_A,'--packet',PACKET,
            '--output',BASE/('09c-c2-b1-'+role+'-p1-01')]))
    text(MATERIAL/'ROLE-MATERIAL-COMMANDS.txt','# Stage A实际READY后只写P1；ideation B1/首启/readiness完毕才启动executor B1。\n'+'\n'.join(role_commands))
    ideation=BASE/'09c-c2-b1-ideation-p1-01';executor=BASE/'09c-c2-b1-executor-p1-01'
    text(MATERIAL/'OWNER-BIND-COMMAND.txt',cmd([sys.executable,'-B',BASE/'prepare-rev2-owner.py','--mode','owner',
         '--stage-a',STAGE_A,'--packet',PACKET,'--ideation',ideation,'--executor',executor,'--output',MATERIAL/'owner.json']))
    text(MATERIAL/'RUNTIME-COMMAND-MATERIALS.txt',cmd([sys.executable,'-B',BASE/'prepare-c2-runtime.py','--mode','bind',
         '--stage-a',STAGE_A,'--packet',PACKET,'--ideation',ideation,'--executor',executor,
         '--output',BASE/'09c-c2-preparation-01']))
    save(MATERIAL/'SOURCE.json',{'status':'PASS','revision':revision,'rehearsed_repair_revision':revalidation.REPAIR_REVISION,
        'business_revision':revalidation.BUSINESS_REVISION,'product_app_acceptance_bytes_unchanged':True,
        'runtime_source_revision':revalidation.REPAIR_REVISION,'runtime_workbench_acceptance_scripts_bytes_unchanged':True,
        'freeze_revision_scope':'full checkout including receipt-binding metadata; runtime bytes are exactly dc15dc3f0',
        'regression_validation':regression,'snapshot':str(PACKET/'sources.tar.gz'),'source_paths':static['source_paths'],
        'runtime_root':'NOT_CREATED; Stage A creates a fresh root','role_binding':'actual new Stage A/B1 only',
        'new_timed_coordinator':'completed real CLI rehearsal PASS at dc15dc3f0; second Claude scene NOT_RUN',
        'scene_process_starts':0,'signature_fields_empty':True,'launch_status':'NO_GO'})
    save(MATERIAL/'BUDGET.json',{'ideation':{'roots':4,'POST':7},'executor':{'roots':1,'POST':1},'combined_POST':8,
         'tool_permissions':3,'real_model_turns':0,'early_gate_ms_lt':120000,'late_gate_ms_gt':120000,
         'C_I3_monotonic_min_ms':120100,'scene_max_ms':150000})
    save(MATERIAL/'static-check.json',{'status':'PASS','revision':revision,'regression_validation':regression,
         'Stage_A_command':list(map(str,stage)),'source_member_bytes_compared':len(static['source_paths']),
         'scene_process_starts':0,'signatures_written':False})
    print(json.dumps({'status':'PASS','revision':revision,'materials':str(MATERIAL),'packet':str(PACKET),'scene_process_starts':0}))


if __name__=='__main__':main()
