"""Prepare two independent 09A-3 fixtures. Never launch CLI/API/Electron/build."""
import argparse,json,sys
from pathlib import Path
import shutil
import subprocess

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE/'workbench/tests'))
from p1_simulated_actions import action_plan
p=argparse.ArgumentParser();p.add_argument('--generation',choices=['09a3r2'],required=True);args=p.parse_args()
for suffix in [args.generation,args.generation+'-block']:
    label='p1-materials-'+suffix
    subprocess.run(['python3','-B',str(SOURCE/'workbench/tests/regenerate_t078_p1.py'),'--label',label,'--extra-source',
                    str(Path(__file__).resolve()),str(BASE/'check-materials-09a3.py'),str(BASE/'outside-09a3.sh'),str(BASE/'KEY-BASIS-09A3R2.md')],cwd=SOURCE,check=True)
    m=BASE/label;a=json.loads((m/'input.json').read_text(encoding='utf-8'));root=Path(a['root'])
    (m/'approvals').mkdir()
    shutil.copyfile(BASE/'p1-materials-09a2/security-notice-text.txt',m/'security-notice-text.txt')
    template=json.loads((BASE/'p1-materials-09a2/screen-key-approval-template.json').read_text(encoding='utf-8'))
    template.update(launch=a['launch'],session=a['session'],directory=str(root/'repo'),notice_reference=str(m/'security-notice-text.txt'))
    block=suffix.endswith('-block')
    handling='retain-draft-for-block' if block else 'simulated-empty-declaration'
    actions=[{**step,'approved_by':None,'approval_ref':None,'basis':None} for step in action_plan(handling)]
    consent={'launch':a['launch'],'session':a['session'],'scenario':suffix,'source':'test-simulated-user','actions':actions,'key_basis':str(BASE/'KEY-BASIS-09A3R2.md'),
             'approved_by':None,'approval_ref':None,'basis':None}
    driver={'scope':'逐次批准；两夹具串行运行；本材料只请求 launch，后续阶段另批',
            'launch_argv':['bash',str(BASE/'outside-09a3.sh'),args.generation,'block' if block else 'clean','launch'],
            'continue_argv':['python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(m),'--phase','continue-esc',
                             '--readiness-file',str(m/'readiness.json'),'--actions-approval',str(m/'actions-approval.json')],
            'slot':'t078-09-'+a['launch'],'slot_cleanup_argv':['python3','-B',str(SOURCE/'workbench/tests/cleanup_t078_electron_slot.py'),'--materials',str(m)],
            'draft_handling':'executor 逐项预批的 test-simulated-user；保留草稿后作反例声明' if block else 'executor 逐项预批的 test-simulated-user；同窗一次 Ctrl+C，空框快照成立后点击声明',
            'automation_source':'test-simulated-user','key_basis':str(BASE/'KEY-BASIS-09A3R2.md'),'control_c_attempt_budget':0 if block else 1,
            'timeouts_seconds':{'observed_state':30,'build':90,'blocked_no_request_observation':2},
            'expected_messages_requests':1 if block else 2,'messages_request_budget':2,'real_model_budget':0,'starts':0}
    for name,value in [('screen-key-approval-template.json',template),('actions-approval-template.json',consent),('scenario-driver.json',driver)]:
        with (m/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'PASS','scope':'静态材料生成','materials':str(m),'root':str(root),'launch':a['launch'],'starts':0},ensure_ascii=False))
