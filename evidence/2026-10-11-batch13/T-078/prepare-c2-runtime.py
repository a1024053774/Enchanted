"""Write attempt-2 commands from this attempt's actual Stage A and B1 receipts."""
import argparse
import base64
from contextlib import closing
import json
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE/'workbench/tests'))
from t078_raw_retention import read_json, save, require
from p1_output import validate_capture
from p1_simulated_actions import empty_manual_prompt


def text(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(value)


def command(argv):return shlex.join(list(map(str,argv)))+'\n'


def driver(plan,p1,stage,mode,label):
    return [sys.executable,'-B',SOURCE/'workbench/tests/t078_09c_driver.py','--plan',plan,'--stage',stage,
            '--approval',p1/'phases'/stage/'approval.json','--mode',mode,'--output',p1/'phases'/stage/label]


def role(args):
    require(not args.output.exists(),'role_output_exists')
    argv=[sys.executable,'-B',BASE/'prepare-a14.py','--mode','role','--instance','c2','--prompt-file',args.prompt_file,
          '--role',args.role,'--stage-a',args.stage_a,'--packet',args.packet,'--output',args.output]
    subprocess.run(list(map(str,argv)),cwd=SOURCE,check=True)
    p1=args.output;inp=read_json(p1/'input.json')
    save(p1/'readiness-consent.json',{**read_json(p1/'readiness-template.json'),'approval_ref':None})
    text(p1/'READINESS-COMMAND.txt', '# 主控签 readiness-consent.json；s13初读不符仅用-02重读，并把本条--screen改为那份完整原屏。\n'+command([
        sys.executable,'-B',Path(__file__),'--mode','readiness','--p1',p1,'--screen',p1/('c2-'+args.role+'-s13-screen'),
        '--approval',p1/'readiness-consent.json','--output',p1/'readiness.json']))
    # Stage B keeps security-notice + exact screen_text; individual key purpose
    # remains onboarding-notice. Both are produced by the unchanged standard generator.
    approval=read_json(p1/'stage-b-approval.json')
    require(approval['screen_approvals']==read_json(BASE/'stage-b-a12-ideation-approval-01.json')['screen_approvals'], 'B1_screen_plan_changed')
    require(read_json(p1/'onboarding/s7-Enter.json')['purpose']=='onboarding-notice','s7_purpose')
    for folder in (p1/'phases').iterdir():
        stage=folder.name;plan=Path(inp['root'])/'protocol-plan.json'
        text(folder/'ARM-COMMAND.txt',command(driver(plan,p1,stage,'arm','armed-01')))
        if stage=='C-I1':
            text(folder/'INITIALIZE-COMMAND.txt',command(driver(plan,p1,stage,'initialize','initialized-01')))
            text(folder/'START-COMMAND.txt',command(driver(plan,p1,stage,'start','start-01')))
            text(folder/'OBSERVE-COMMAND.txt',command([sys.executable,'-B',Path(__file__),'--mode','c1-observe',
                '--p1',p1,'--stage-a',args.stage_a,'--approval',BASE/'09c-c2-preparation-01/timed-preapproval.json',
                '--output',folder/'observe-logs-01']))
            text(folder/'PREPARE-PERMISSION-COMMAND.txt',command([sys.executable,'-B',Path(__file__),'--mode','c1-permission',
                '--p1',p1,'--stage-a',args.stage_a,'--output',folder/'permission-approval-01.json']))


def readiness(args):
    require(not args.output.exists(),'readiness_exists')
    inp=read_json(args.p1/'input.json');consent=read_json(args.approval)
    require(consent['launch']==inp['launch'] and consent['session']==inp['session'] and
        consent['confirmed_by']=='executor' and consent['readiness']=='confirmed' and consent.get('approval_ref') and consent.get('basis'), 'signed_readiness_required')
    meta=read_json(args.screen/'screen.json');raw=(args.screen/'screen.bin').read_bytes()
    require(meta['screen_id']==inp['preset']+'-s13' and meta['launch']==inp['launch'] and meta['session']==inp['session'] and
            meta['directory']==str(Path(inp['root'])/'repo'),'readiness_screen_binding')
    validate_capture(raw,meta['capture']);require(raw==base64.b64decode(meta['output']['data_base64'],validate=True),'readiness_complete_bytes')
    empty_manual_prompt(raw,meta['capture'])
    api=Path(inp['root'])/'roles'/inp['preset']
    require(not list((api/'http-exchanges').glob('*.request.bin')) and
        all(not (api/name).exists() or not (api/name).read_bytes().strip() for name in ['requests.ndjson','responses.ndjson']), 'readiness_zero_POSTs')
    with closing(sqlite3.connect((Path(inp['root'])/'state/state.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        count=db.execute("SELECT count(*) FROM orchestration_events WHERE launch=? AND type IN ('turn_submit_intent','turn_submitted','turn_start_signal','turn_end_signal')",(inp['launch'],)).fetchone()[0]
    require(count==0,'readiness_zero_business_input')
    save(args.output,{**consent,'screen_file':str(args.screen/'screen.bin'),'screen_capture':meta['capture'],'messages':0,'submission_events':0})


def c1_permission(args):
    p1=args.p1.resolve();folder=p1/'phases/C-I1';binding=read_json(p1/'launch-binding.json')
    require(not args.output.exists(),'permission_draft_exists')
    subprocess.run(list(map(str,[sys.executable,'-B',BASE/'prepare-a14.py','--mode','permission','--p1',p1,
        '--result',folder/'dispatch-01/result.json','--output',args.output])),cwd=SOURCE,check=True)
    label='c2-ideation-C-I1-permission-screen-02'
    text(folder/'SCREEN-CMP-COMMAND.txt',command([sys.executable,'-B',SOURCE/'workbench/tests/run_t078_p1.py',
        '--materials',p1,'--reuse-stage-a','--launch-label',binding['launch_label'],'--phase','screen','--label',label,
        '--screen-id','ideation-C-I1-permission'])+command(['cmp',p1/label/'screen.bin',folder/'dispatch-01/permission-screen.bin']))


def bind(args):
    args.output.mkdir(parents=True,exist_ok=False)
    ready=read_json(args.stage_a/'readiness.json');root=Path(ready['root']);plan_file=root/'protocol-plan.json';plan=read_json(plan_file)
    p1=args.ideation.resolve();executor=args.executor.resolve();inp=read_json(p1/'input.json')
    require(read_json(p1/'launch-binding.json')['process_manifest'] and read_json(executor/'launch-binding.json')['process_manifest'],'actual_B1_required')
    require(read_json(plan['owner_file'])['claim_binding']==ready['target_binding'],'owner_must_be_bound_first')
    require(plan['package']==str(args.packet.resolve()) and plan['roles']['ideation']==inp and
            plan['roles']['executor']==read_json(executor/'input.json'),'C2_runtime_material_binding')
    policy={'approved_by':None,'approval_ref':None,'scene':'09C','role':'ideation','source':'test-simulated-user',
            'source_revision':plan['source_revision'],'package':plan['package'],'target_binding':plan['target_binding'],
            'launch':inp['launch'],'session':inp['session'],'thread':inp['thread'],'stages':['C-I2','C-I3'],'max_Enter_per_stage':1,
            'stop_binding':'actual original C-I1 queued request -> Stop/relay entry only',
            'conditions':['exact actual registered command and argv; no concatenation','same source/owner/target/native prompt/dispatch/permission',
                'complete screen == dispatch original','one-time Yes selected in actual Electron view','no ack; continued original stop demand',
                'C-I2 age <90000ms then actual gate stop_too_early','C-I3 wall >120000ms and mono >=120100ms; scene <=150000ms',
                'any mismatch stops future keys; never retry an uncertain key']}
    save(args.output/'timed-preapproval.json',policy)
    slot='t078-c2-CI3-'+inp['launch']+'-timed-01';build=Path('/Volumes/WD-Elements/a2a-workbench')/slot/'dist'
    require(not build.parent.exists(),'build_slot_exists')
    text(args.output/'C-I3-BUILD-COMMAND.txt',command([sys.executable,'-B',Path(__file__),'--mode','build','--slot',slot,
        '--output',args.output/'C-I3-build-01']))
    arm=[]
    for stage in ['C-I1','C-E1','C-I2','C-I3','C-I4']:
        actual=executor if stage=='C-E1' else p1
        arm.append(command(driver(plan_file,actual,stage,'arm','armed-01')))
    text(args.output/'ARM-ALL-COMMANDS.txt','# 先逐份签五阶段approval，再串行arm；不发送输入。首败即停。\n'+'\n'.join(arm))
    timed=[sys.executable,'-B',SOURCE/'workbench/tests/t078_09c_timed_run.py','--plan',plan_file,'--stage-a',args.stage_a,
        '--ideation',p1,'--executor',executor,'--build',build,'--preapproval',args.output/'timed-preapproval.json',
        '--signature-ref','FILL_WITH_PREAPPROVED_SIGNATURE_REF','--output',args.output/'timed-01']
    text(args.output/'TIMED-RUN-COMMAND.txt','# 主控预先签timed-preapproval，并把--signature-ref替换为完全相同的签名文本；先核对/签C-I1许可。\n'+command(timed))
    save(args.output/'BOUND.json',{'status':'PASS','root':str(root),'source_revision':plan['source_revision'],
        'stage_a':str(args.stage_a),'packet':str(args.packet),'ideation':str(p1),'executor':str(executor),'build':str(build),
        'scene_process_starts':0,'signatures_written':False})


def build(args):
    args.output.mkdir(parents=True,exist_ok=False)
    require(re.fullmatch(r't078-c2-CI3-[0-9a-f-]+-timed-01',args.slot),'explicit_C2_build_slot')
    require(not (Path('/Volumes/WD-Elements/a2a-workbench')/args.slot).exists(),'build_slot_exists')
    argv=['node',str(SOURCE/'workbench/app/build.mjs'),'--slot',args.slot]
    result=subprocess.run(argv,cwd=SOURCE,capture_output=True,timeout=120)
    for name,raw in [('stdout.bin',result.stdout),('stderr.bin',result.stderr)]:
        with (args.output/name).open('xb') as stream:stream.write(raw)
    require(result.returncode==0,'C2_build_failed')
    value=json.loads(result.stdout.decode().strip().splitlines()[-1]);require(Path(value['out']).is_dir(),'C2_build_out_missing')
    save(args.output/'result.json',{'status':'PASS','argv':argv,'build':value,'scene_process_starts':0})


def observe_C1(args):
    from t078_09c_timed_run import Timed
    args.output.mkdir(parents=True,exist_ok=False)
    inp=read_json(args.p1/'input.json')
    runtime=argparse.Namespace(plan=Path(inp['root'])/'protocol-plan.json',ideation=args.p1,
        executor=BASE/'09c-c2-b1-executor-p1-01',preapproval=args.approval,stage_a=args.stage_a,
        signature_ref='',build=None)
    runner=Timed(runtime,args.output)
    try:
        dispatch,raw=runner.observe('C-I1')
        save(args.output/'result.json',{'status':'READY_FOR_PERMISSION','dispatch':dispatch['dispatch']['id'],
            'screen_bytes':len(raw),'steps':runner.steps,'key_writes':0})
    finally:runner.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['role','readiness','c1-permission','c1-observe','bind','build'],required=True)
    for name in ['stage-a','packet','prompt-file','p1','screen','approval','ideation','executor','output']:
        parser.add_argument('--'+name,type=Path,required=name=='output')
    parser.add_argument('--role',choices=['ideation','executor']);parser.add_argument('--slot');args=parser.parse_args()
    {'role':role,'readiness':readiness,'c1-permission':c1_permission,'c1-observe':observe_C1,'bind':bind,'build':build}[args.mode](args)
    print(json.dumps({'status':'PASS','mode':args.mode,'output':str(args.output)},ensure_ascii=False))


if __name__=='__main__':main()
