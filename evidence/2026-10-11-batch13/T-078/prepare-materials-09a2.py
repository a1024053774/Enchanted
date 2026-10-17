"""Generate static 09A-2 materials only; no CLI, API, Electron or build starts."""
import json, shutil, subprocess
from pathlib import Path
source=Path('/Users/luckye/Documents/Code/a2a-wt-t078');base=Path(__file__).resolve().parent
label='p1-materials-09a2';m=base/label;old=base/'p1-materials-09'
subprocess.run(['python3','-B',str(source/'workbench/tests/regenerate_t078_p1.py'),'--label',label,'--extra-source',
                str(base/'p1-check-materials-09a2.py'),str(Path(__file__).resolve())],cwd=source,check=True)
approval=json.loads((m/'approval.json').read_text(encoding='utf-8'));a=approval['input']
root=Path(a['root']);(m/'approvals').mkdir()
shutil.copyfile(old/'security-notice-text.txt',m/'security-notice-text.txt')
template=json.loads((old/'screen-key-approval-template.json').read_text(encoding='utf-8'))
template.update(launch=a['launch'],session=a['session'],directory=str(root/'repo'),notice_reference=str(m/'security-notice-text.txt'))
actions=json.loads((old/'actions-approval-template.json').read_text(encoding='utf-8'));actions.update(launch=a['launch'],session=a['session'],scenario='09A-2')
for name,value in [('screen-key-approval-template.json',template),('actions-approval-template.json',actions)]:
    with (m/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
old_input=json.loads((old/'input.json').read_text(encoding='utf-8'))
scenario=(old/'scenario-driver.json').read_text(encoding='utf-8').replace(str(old),str(m)).replace(old_input['root'],a['root']).replace(old_input['task'],a['task']).replace(old_input['launch'],a['launch'])
driver=json.loads(scenario);driver['scope']='09A-2 only; launch does not start Electron or send input'
driver['actions'][0]='wait rendered launch/thread/busy/active/input-enabled; attempt Escape once; confirm stored action/admission/PTY intent/write/retirement'
driver['slot_cleanup_argv']=['/usr/bin/python3','-B',str(source/'workbench/tests/cleanup_t078_electron_slot.py'),'--materials',str(m)]
with (m/'scenario-driver.json').open('x',encoding='utf-8') as f:json.dump(driver,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'PASS','materials':str(m),'root':str(root),'launch':a['launch'],'session':a['session'],'thread':a['thread'],'code_revision':a['code_revision'],'starts':0}))
