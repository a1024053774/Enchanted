"""Freeze a two-role executable launch proposal without starting anything."""
import argparse, json, shutil, subprocess, sys, tarfile, tempfile, uuid
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='09b-executable-materials-02');args=parser.parse_args()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    assert not subprocess.check_output(['git','diff','HEAD','--','workbench'],cwd=SOURCE)
    assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','workbench'],cwd=SOURCE)
    out=BASE/args.label;assert out.name.startswith('09b-executable-materials-') and not out.exists();out.mkdir()
    root=Path(tempfile.mkdtemp(prefix='t078-2-09b-executable-',dir='/tmp')).resolve();task='t078-09b-executable-'+uuid.uuid4().hex[:8]
    for p in ['state','repo','manager-home','oracle']:(root/p).mkdir(parents=True)
    (root/'repo/value.txt').write_text('09B deterministic target baseline\n',encoding='utf-8')
    (root/'oracle/contract-09b.json').write_text(json.dumps({'schema':1,'target':'deterministic-receiver','delta_hex':'1b','candidate_submission':False},indent=2)+'\n',encoding='utf-8')
    node=str(Path(shutil.which('node')).resolve());roles={}
    for role,budget,messages in [('ideation',4,6),('executor',6,11)]:
        role_root=root/'roles'/role
        for name in ['home','claude','tmp','shell','requests','hooks','user-data']: (role_root/name).mkdir(parents=True)
        (role_root/'claude/settings.json').write_text('{"theme":"dark"}\n',encoding='utf-8')
        (role_root/'role.md').write_text('09B '+role+' deterministic role. Use only approved phase input and exact registered text; no retry or extra role.\n',encoding='utf-8')
        data={'schema':1,'root':str(root),'state':str(root/'state'),'task':task,'preset':role,'launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),
              'executable':'/Users/luckye/.local/share/claude/versions/2.1.296','role_file':str(role_root/'role.md'),'code_revision':revision,
              'source_snapshot':str(out/'sources.tar.gz'),'api_url':'http://127.0.0.1:1','turn_limit':budget}
        inp=root/(role+'-input.json');inp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        approval=out/(role+'-approval.json');subprocess.run(['node',SOURCE/'workbench/tests/prepare_t078_p1.ts',inp,approval],cwd=SOURCE,check=True)
        launch=json.loads(approval.read_bytes())['launch'];assert launch['turn_limit']==budget
        assert launch['env']['HOME']==str(role_root/'home') and launch['env']['CLAUDE_CONFIG_DIR']==str(role_root/'claude')
        roles[role]={'input':data,'approval':str(approval.relative_to(BASE)),'root_budget':budget,'messages_budget':messages,'target_claim_status':'PENDING_RUNTIME_DISPATCH','launch_status':'NO_GO'}
    target={'task':task,'claim_status':'PENDING_RUNTIME_DISPATCH','attempt':None,'session':None,'fence':None,'thread':None,'workspace':str(root/'repo'),'oracle_paths':['oracle/contract-09b.json'],'candidate_submission':False,
            'binding_rule':'Populate only from actual card_save/dispatch/claim and live target process; no placeholders or operator writes'}
    plan={'status':'PASS','launch_status':'NO_GO','revision':revision,'root':str(root),'task':task,'roles':roles,'target':target,
          'budgets':{'ideation':{'roots':4,'messages':6},'executor':{'roots':6,'messages':11},'combined_messages':17,'tool_calls':7,'real_vendor_model_turns':0},
          'driver':'workbench/tests/t078_09b_driver.py','identity':'Actual registered dispatch text, stop/request/inbox IDs and global dispatch.seq; no fixed #1/#2'}
    (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'target-card.json').write_text(json.dumps({'id':task,'oracle_paths':['oracle/contract-09b.json'],'allow':['value.txt'],'deny':[],'candidate_submission':False,'oracle_protection':'oracle_paths'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'actions-approval-template.json').write_text(json.dumps({'approved_by':None,'approval_ref':None,'launch_status':'NO_GO','actions':[]},indent=2)+'\n',encoding='utf-8')
    (out/'launch-approval-template.json').write_text(json.dumps({'approved_by':None,'approval_ref':None,'launch_status':'NO_GO','roles':['ideation','executor'],'real_vendor_model_turns':0},indent=2)+'\n',encoding='utf-8')
    files=[SOURCE/'workbench/src/claudeLaunch.ts',SOURCE/'workbench/src/panes.ts',SOURCE/'workbench/src/relay.ts',SOURCE/'workbench/src/gates/core.ts',SOURCE/'workbench/src/gates/cli.ts',SOURCE/'workbench/tests/t078_09b_driver.py',SOURCE/'workbench/tests/t078_09b_fake_api.py',SOURCE/'workbench/tests/t078_09b_protocol_core.py',SOURCE/'workbench/tests/t078_09b_protocol_full.py',SOURCE/'workbench/tests/test_t078_09b_fake_api_stop.py',SOURCE/'workbench/tests/test_t078_09b_fake_api_http.py',SOURCE/'workbench/tests/test_t078_09b_receiver_launch.py',SOURCE/'workbench/tests/test_t078_09b_runner_spies.py',SOURCE/'workbench/tests/test_t078_09b_revision_gate.py',SOURCE/'workbench/tests/test_t078_runner_card_preflight.py',SOURCE/'workbench/tests/test_t078_role_file_boundary.ts',SOURCE/'workbench/tests/regenerate_t078_p1.py',BASE/'09B-DRIVER.md',BASE/'09B-RUN-PLAN.md',BASE/'09B-RUN-SPY.md',BASE/'run-09b.py',BASE/'diagnose-stage-a-04.py',BASE/'cleanup-09b-stage-a-03.py',BASE/'cleanup-09b-stage-a-03-recovery.py',BASE/'cleanup-09b-stage-a-04.py',BASE/'prepare-09b-executable.py']
    with tarfile.open(out/'sources.tar.gz','x:gz') as arc:
        for f in files:arc.add(f,arcname=str(f.relative_to(SOURCE)))
    with tarfile.open(out/'sources.tar.gz') as arc:
        for f in files:assert arc.extractfile(str(f.relative_to(SOURCE))).read()==f.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(f.relative_to(SOURCE))],cwd=SOURCE)
    static={'status':'PASS','launch_status':'NO_GO','revision':revision,'root':str(root),'task':task,'roles':['ideation','executor'],'source_files':len(files),'real_cli_starts':0,'api_starts':0,'target_starts':0,'real_vendor_model_turns':0,'approval_fields_empty':True}
    (out/'static-check.json').write_text(json.dumps(static,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(static,ensure_ascii=False))
if __name__=='__main__':main()
