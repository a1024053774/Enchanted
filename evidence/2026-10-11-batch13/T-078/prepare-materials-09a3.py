"""Prepare two independent 09A-3 fixtures. Never launch CLI/API/Electron/build."""
import json
from pathlib import Path
import shutil
import subprocess

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=Path(__file__).resolve().parent
for suffix in ['09a3','09a3-block']:
    label='p1-materials-'+suffix
    subprocess.run(['python3','-B',str(SOURCE/'workbench/tests/regenerate_t078_p1.py'),'--label',label,'--extra-source',
                    str(Path(__file__).resolve()),str(BASE/'check-materials-09a3.py'),str(BASE/'outside-09a3.sh')],cwd=SOURCE,check=True)
    m=BASE/label;a=json.loads((m/'input.json').read_text(encoding='utf-8'));root=Path(a['root'])
    (m/'approvals').mkdir()
    shutil.copyfile(BASE/'p1-materials-09a2/security-notice-text.txt',m/'security-notice-text.txt')
    template=json.loads((BASE/'p1-materials-09a2/screen-key-approval-template.json').read_text(encoding='utf-8'))
    template.update(launch=a['launch'],session=a['session'],directory=str(root/'repo'),notice_reference=str(m/'security-notice-text.txt'))
    actions=['Escape','manual-draft-handling','empty-declaration-release'] if suffix=='09a3' else ['Escape','retain-draft','false-empty-declaration-release']
    consent={'launch':a['launch'],'session':a['session'],'scenario':suffix,'actions':actions,
             'approved_by':None,'approval_ref':None,'basis':None}
    driver={'scope':'逐次批准；两夹具串行运行；本材料只请求 launch，后续阶段另批',
            'launch_argv':['bash',str(BASE/'outside-09a3.sh'),'clean' if suffix=='09a3' else 'block','launch'],
            'continue_argv':['python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(m),'--phase','continue-esc',
                             '--readiness-file',str(m/'readiness.json'),'--actions-approval',str(m/'actions-approval.json')],
            'slot':'t078-09-'+a['launch'],'slot_cleanup_argv':['python3','-B',str(SOURCE/'workbench/tests/cleanup_t078_electron_slot.py'),'--materials',str(m)],
            'draft_handling':'主控在本隔离 Electron 窗口手动处理草稿及点击声明；驱动不代发清空键、不自动点击',
            'timeouts_seconds':{'observed_state':30,'manual_handling':180,'build':90,'blocked_no_request_observation':2},
            'expected_messages_requests':2 if suffix=='09a3' else 1,'messages_request_budget':2,'real_model_budget':0,'starts':0}
    for name,value in [('screen-key-approval-template.json',template),('actions-approval-template.json',consent),('scenario-driver.json',driver)]:
        with (m/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'PASS','scope':'静态材料生成','materials':str(m),'root':str(root),'launch':a['launch'],'starts':0},ensure_ascii=False))
