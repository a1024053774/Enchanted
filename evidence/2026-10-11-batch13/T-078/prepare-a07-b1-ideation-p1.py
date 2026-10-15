"""Generate A-07 ideation P1 materials only after real Stage-A readiness exists."""
import argparse, json, shutil, subprocess, tarfile, uuid
from pathlib import Path

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'

def write_json(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--stage-a',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    packet=a.packet.resolve();stage=a.stage_a.resolve();out=a.output.resolve();assert not out.exists()
    static=json.loads((packet/'static-check.json').read_bytes());ready=json.loads((stage/'readiness.json').read_bytes())
    assert static['status']=='PASS' and static['protocol'] is True and static.get('protocol_tag')=='a07-registered-anthropic-v1'
    assert ready['status']=='READY_FOR_APPROVAL' and ready['stage']=='A' and ready['roles_started']==[]
    root=Path(ready['root']).resolve();assert root.is_dir() and ready['source_revision']==static['revision']
    out.mkdir(parents=False);role_root=root/'roles/ideation'
    for name in ['home','claude','tmp','shell','requests','hooks','user-data']:(role_root/name).mkdir(parents=True,exist_ok=True)
    role_text='09B ideation deterministic role. Use only approved phase input and exact registered text; no retry or extra role.\n';(role_root/'role.md').write_text(role_text,encoding='utf-8');write_json(role_root/'claude/settings.json',{'theme':'dark'})
    input_data={'schema':1,'root':str(root),'state':str(root/'state'),'task':ready['task'],'preset':'ideation','launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),'executable':'/Users/luckye/.local/share/claude/versions/2.1.296','role_file':str(role_root/'role.md'),'code_revision':static['revision'],'source_snapshot':str((packet/'sources.tar.gz').resolve()),'api_url':'http://127.0.0.1:0','turn_limit':4}
    (root/'nonce.txt').write_text('A07_B1_IDEATION_'+uuid.uuid4().hex,encoding='utf-8');write_json(root/'scenario.json',{'schema':1,'name':'stage-b-ideation','nonce':(root/'nonce.txt').read_text()});write_json(root/'input.json',input_data)
    approval=root/'approval.json';subprocess.run([shutil.which('node') or '/opt/homebrew/bin/node',str(SOURCE/'workbench/tests/prepare_t078_p1.ts'),str(root/'input.json'),str(approval)],cwd=SOURCE,check=True)
    write_json(out/'input.json',input_data);shutil.copyfile(approval,out/'approval.json');shutil.copyfile(root/'nonce.txt',out/'nonce.txt');shutil.copyfile(root/'scenario.json',out/'scenario.json');(out/'role.md').write_text(role_text,encoding='utf-8');shutil.copyfile(role_root/'claude/settings.json',out/'isolated-settings.json');shutil.copyfile(packet/'sources.tar.gz',out/'sources.tar.gz')
    with tarfile.open(out/'sources.tar.gz') as arc:write_json(out/'source-files.json',arc.getnames())
    write_json(out/'readiness-template.json',{'launch':input_data['launch'],'session':input_data['session'],'confirmed_by':None,'readiness':'unconfirmed','basis':None})
    write_json(out/'control-plane.json',{'api_reuse':{'root':str(role_root),'readiness_file':str((stage/'readiness.json').resolve()),'api_url_template':'http://127.0.0.1:0','protocol_tag':'a07-registered-anthropic-v1'},'p1_args':['--reuse-stage-a','--reuse-api-root',str(role_root),'--reuse-readiness-file',str((stage/'readiness.json').resolve())],'launch_status':'NO_GO','real_cli_starts':0})
    write_json(out/'generation.json',{'status':'PASS','scope':'A-07 B1 P1 static generation after real Stage-A readiness','root':str(root),'task':ready['task'],'protocol_tag':'a07-registered-anthropic-v1','real_cli_starts':0,'api_starts':0})
    print(json.dumps({'status':'PASS','output':str(out),'launch':'NO_GO'},ensure_ascii=False))
if __name__=='__main__':main()
