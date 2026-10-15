"""Freeze review-only 09B proposals. No launch, services, Git repo or target build."""
import json
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent

def main():
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    assert not subprocess.check_output(['git','diff','HEAD','--','workbench'],cwd=SOURCE)
    assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','workbench'],cwd=SOURCE)
    out=BASE/'09b-materials-01';out.mkdir()
    root=Path(tempfile.mkdtemp(prefix='t078-2-09b-plan-',dir='/tmp')).resolve()
    for p in ['state','repo','manager-home','tmp','target/home','target/bin',*[f'roles/{role}/{name}' for role in ['ideation','executor'] for name in ['home','claude','tmp','shell','requests','hooks','user-data']]]:(root/p).mkdir(parents=True,exist_ok=True)
    ident=lambda:str(uuid.uuid4())
    project='t078-09b-'+uuid.uuid4().hex[:8];task=project+'-target';nonce='09B_'+uuid.uuid4().hex
    node=str(Path(shutil.which('node')).resolve());gate=str(SOURCE/'workbench/src/gates/cli.ts');inbox=str(SOURCE/'workbench/bin/inbox')
    role_texts={
      'ideation':'09B 构思主控确定性实验。只按已批准阶段调用精确库命令：发送 stop；确认真实发送结果；收到 executor ack 后尝试确认原 stop 作为权限反例；最后确认真实拒绝。不改文件、重试、开新角色或调用未列工具。模型输出由假服务脚本提供，不自称业务通过。\n',
      'executor':'09B 执行主控确定性实验。先对错误 controller 目标尝试 stop，收到真实拒绝后对受管目标 stop；收到真实成功结果后 ack；再按批准验证重复 ack 和已 ack 后 stop 拒绝；最后确认。不以 queued 当成功、不提前 ack、不 kill/reclaim/archive、不重试或新增角色。\n'}
    roles={}
    for role,roots,messages in [('ideation',4,6),('executor',6,11)]:
        directory=root/'roles'/role;(directory/'role.md').write_text(role_texts[role],encoding='utf-8')
        data={'schema':1,'root':str(root),'state':str(root/'state'),'task':task,'preset':role,'launch':ident(),'session':ident(),'thread':ident(),
              'executable':'/Users/luckye/.local/share/claude/versions/2.1.296','role_file':str(directory/'role.md'),'code_revision':revision,
              'source_snapshot':str(out/'sources.tar.gz'),'api_url':'http://127.0.0.1:0','turn_limit':roots}
        roles[role]={'input_proposal':data,'messages_budget':messages,'root_budget':roots,'current_profile_acceptance':'NO_GO',
          'env_proposal':{'HOME':str(directory/'home'),'CLAUDE_CONFIG_DIR':str(directory/'claude'),'TMPDIR':str(directory/'tmp'),'ZDOTDIR':str(directory/'shell'),
          'A2A_REQUEST_DIR':str(directory/'requests'),'A2A_HOOK_TRACE_DIR':str(directory/'hooks'),'A2A_STATE':str(root/'state'),'A2A_PRESET':role,'A2A_ROLE':'controller',
          'A2A_PROJECT':project,'A2A_TASK':task,'A2A_LAUNCH':data['launch'],'A2A_SESSION':data['session'],'A2A_NATIVE_SESSION':data['session'],'A2A_SPEC_REV':'1',
          'ANTHROPIC_BASE_URL':'http://127.0.0.1:RUNTIME_PORT','ANTHROPIC_AUTH_TOKEN':'a2a-fixture-key-not-a-secret'},
          'profile_requirements':{'model':'claude-haiku-5-5','effort':'low','permission_mode':'manual','tools':'Bash,Read','mcp':{},
          'hook_names':['UserPromptSubmit','PermissionRequest','Stop'],'private_capability':'daemon-issued at actual launch; never frozen or copied'},
          'directories':{'debug':str(directory/'claude-debug.log'),'electron_user_data':str(directory/'user-data')}}
        (out/(role+'-role.md')).write_text(role_texts[role],encoding='utf-8')
        signal=shlex.join([node,gate,'--state',str(root/'state'),'signal','--launch',data['launch']])
        settings={'hooks':{name:[{'hooks':[{'type':'command','command':signal,'timeout':3}]}] for name in ['UserPromptSubmit','PermissionRequest','Stop']}}
        roles[role]['argv_proposal']=[data['executable'],'--session-id',data['session'],'--model','claude-haiku-5-5','--effort','low','--permission-mode','manual',
            '--settings',json.dumps(settings),'--append-system-prompt',role_texts[role],'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--tools','Bash,Read','--disable-slash-commands','--debug-file',str(directory/'claude-debug.log')]
        roles[role]['argv_status']='Proposal only; do not execute; current launch producer rejects this profile'
    # Dynamic IDs are typed references to actual gate results, never prefilled attempts.
    binding={'source':'actual managed dispatch/claim receipt and live pane identity','required':['task_id','attempt_id','session_id','fence','thread_id','workspace','launch','shell_pid','leader_pid','native_session'],
             'forbidden':'No placeholder may be passed to a live command; no direct attempt/credential database insertion'}
    commands={
      'I_SEND_STOP':{'argv':[node,inbox,'send','--from','executor','--to','executor','--kind','stop','--body-file',str(root/'roles/ideation/stop-body.txt'),'--ref','thread:{target.thread_id}','--ref','attempt:{target.attempt_id}','--ref','input:{synthetic_user_input.id}'],'result':'one actual stop entry, from=ideation'},
      'I_FOREIGN_ACK':{'argv':[node,inbox,'ack','--id','{stop.id}'],'result':'recipient_required; no new ack/wake'},
      'E_WRONG_TARGET':{'argv':[node,gate,'stop','--thread',roles['ideation']['input_proposal']['thread'],'--stop-id','{stop.id}'],'result':'worker_target_required; no Esc'},
      'E_STOP':{'argv':[node,gate,'stop','--thread','{target.thread_id}','--stop-id','{stop.id}'],'result':'interruptRequested=true; actor=executor; one target Esc'},
      'E_ACK':{'argv':[node,inbox,'ack','--role','ideation','--id','{stop.id}'],'result':'one actual ack from=executor, reply_to=stop.id'},
      'E_DUP_ACK':{'argv':[node,inbox,'ack','--id','{stop.id}'],'result':'same ack entry ID; new request ID; no new ack/wake/Esc'},
      'E_STOP_ACKED':{'argv':[node,gate,'stop','--thread','{target.thread_id}','--stop-id','{stop.id}'],'result':'stop_already_acknowledged; no extra Esc'}}
    phases=[
      {'id':'I1','role':'ideation','input':'approved synthetic user-window stop request','tool':'I_SEND_STOP','messages':2,'Stop_effect':'send actual stop and wake executor; queue actual send receipt'},
      {'id':'I2','role':'ideation','input':'actual send execution feedback','tool':None,'messages':1,'Stop_effect':'confirm only'},
      {'id':'E1','role':'executor','input':'actual inbox wake containing stop.id and target binding','tool':'E_WRONG_TARGET','messages':2,'Stop_effect':'real wrong-target denial'},
      {'id':'E2','role':'executor','input':'actual E1 denial feedback','tool':'E_STOP','messages':2,'Stop_effect':'one managed target interrupt'},
      {'id':'E3','role':'executor','input':'actual successful E2 execution feedback','tool':'E_ACK','messages':2,'Stop_effect':'append actual ack and wake ideation'},
      {'id':'E4','role':'executor','input':'actual E3 ack execution feedback','tool':'E_DUP_ACK','messages':2,'Stop_effect':'idempotent ack; no second wake'},
      {'id':'I3','role':'ideation','input':'actual executor ack inbox wake','tool':'I_FOREIGN_ACK','messages':2,'Stop_effect':'real foreign-recipient denial'},
      {'id':'I4','role':'ideation','input':'actual I3 denial feedback','tool':None,'messages':1,'Stop_effect':'final confirm and idle'},
      {'id':'E5','role':'executor','input':'actual E4 duplicate-ack execution feedback','tool':'E_STOP_ACKED','messages':2,'Stop_effect':'real already-acknowledged denial'},
      {'id':'E6','role':'executor','input':'actual E5 denial feedback','tool':None,'messages':1,'Stop_effect':'final confirm and idle'}]
    oracle={'scope':'future real entry observations; not implemented or run by this review-only packet',
      'expected':{'role_budgets':{'ideation':{'roots':4,'messages':6},'executor':{'roots':6,'messages':11}},'main_Messages_total':17,'stop_entries':1,'ack_entries':1,'successful_target_interrupts':1,
      'typed_user_root_source':'test-simulated-user via window, never called a real human input','target_delta_bytes_hex':'1b','target_delta_rule':'final received.bin == captured post-initial-dispatch baseline + one Esc; do not count bracketed-paste bytes as interrupts',
      'roles_final_idle':True,'target_lifetime_and_attempt_unchanged':True,'target_reclaimed':False,'target_archived':False,'target_candidate_submitted':False,'real_vendor_model_turns':0},
      'required_layers':['native API tool_use/tool_result with exact command and ID','matching UPS/Stop/session/prompt and exit0','actual registered full text, not fixed global sequence numbers','role caller and actual managed target claim/fence identity','gate/inbox/relay rows and actor=executor','raw target bytes and same live PID/start/leader','three-pane task window snapshots and window/action receipts'],
      'additional_boundary_review':['wrong native session and revoked capability through actual authenticated hook entry, counted separately from role-command denials'],
      'stop_conditions':['wrong/missing identity or unresolved runtime token','queued mistaken for execution','ack before actual interrupt success','extra root/Messages/tool/permission key/Esc','unexpected API/header/endpoint or changed approval screen','unknown write, role wake or target lifecycle','any attempt to use operator for stop/send/ack']}
    card={'id':task,'source':None,'goal':'受管确定性接收目标：记录中断字节并保持进程及 attempt；不提交候选',
      'non_goals':['真实 Codex/模型行为','worker交付或集成'],'paths':{'allow':['value.txt'],'deny':['oracle/**']},'oracle_paths':['oracle/contract-09b.json'],
      'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c',"raise SystemExit('09B target does not submit a worker candidate')"]}],
      'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
    actions=[{'id':'setup','scope':'one new broker/project/repo; save baseline oracle and card, real managed dispatch, compile existing deterministic C receiver; no vendor Codex'},
             *[{'id':'launch-'+r,'scope':'proposed profile only; current producer rejects it; re-freeze after prerequisite implementation'} for r in roles],
             {'id':'screens','scope':'each role actual theme/notice/trust/readiness separately; one screen/one key/one approval'},
             {'id':'user-stop','scope':'one approved synthetic user-window message; bind actual target and actual recorded input.id'},
             *[{'id':p['id'],'scope':p['input'],'tool':p['tool']} for p in phases],
             {'id':'cleanup','scope':'separate fixed-PID cleanup after run; no slot deletion'}]
    for a in actions:a.update(approved_by=None,approval_ref=None,basis=None)
    blockers=['role-isolated HOME/config/tmp/shell/requests/hooks/debug/user-data with common state/repo is not supported by current P1 profile',
              'claudeLaunch and Panes signal accept only 1/2 roots; proposed role budgets require 4/6',
              '09B multi-role fake API and real phase driver/oracle runner must be implemented and entry-tested after plan approval; this packet contains protocol proposals only']
    plan={'status':'PASS','scope':'Frozen plan-review packet only','launch_status':'NO_GO','source_revision':revision,'root':str(root),'project':project,'task':task,'nonce':nonce,
      'roles':roles,'target':{'kind':'deterministic C terminal receiver; not real Codex','source':str(SOURCE/'workbench/tests/t078_native_receiver.c'),'home':str(root/'target/home'),'binding':binding,'card':card},
      'operator_scope':'scaffolding, read-only observation and separately approved cleanup only; never role business send/stop/ack',
      'approved_upper_bound':{'per_role_roots':6,'per_role_Messages':12,'combined_Messages':24,'real_models':0},'proposed_budgets':oracle['expected']['role_budgets'],'main_Messages_total':17,'blockers':blockers,'startup_driver':None,'approval_gate':'Review plan first; implementation and a new runnable freeze are required before launch approval'}
    for name,data in [('plan.json',plan),('protocol.json',{'phases':phases,'commands':commands,'identity_binding':binding,'interleaving':'I/E feedback and inbox may arrive in either wall-clock order; correlate by actual dispatch/request/inbox IDs, not global phase order'}),('oracle.json',oracle),('task-card-template.json',card),('actions-approval-template.json',{'stage':'plan-review only','actions':actions}),('launch-approval-template.json',{'stage':'plan-review','launch_status':'NO_GO','source_revision':revision,'approved_by':None,'approval_ref':None,'roles':list(roles),'budgets':plan['proposed_budgets'],'blockers':blockers})]:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=[*SOURCE.joinpath('workbench/src').rglob('*.ts'),SOURCE/'workbench/tests/t078_native_receiver.c',SOURCE/'workbench/tests/test_t078_09b_profile_preconditions.ts',SOURCE/'workbench/bin/inbox',SOURCE/'workbench/README.md',SOURCE/'.project-map/templates/task-card.md',BASE/'PLAN-09BC-01.md',BASE/'prepare-09b-plan.py']
    with tarfile.open(out/'sources.tar.gz','x:gz') as arc:
        for f in files:arc.add(f,arcname=str(f.relative_to(SOURCE)))
    with tarfile.open(out/'sources.tar.gz') as arc:
        for f in files:assert arc.extractfile(str(f.relative_to(SOURCE))).read()==subprocess.check_output(['git','show',revision+':'+str(f.relative_to(SOURCE))],cwd=SOURCE)==f.read_bytes()
    assert roles['ideation']['env_proposal']['HOME']!=roles['executor']['env_proposal']['HOME']
    assert sum(p['messages'] for p in phases)==17 and len([p for p in phases if p['role']=='ideation'])==4 and len([p for p in phases if p['role']=='executor'])==6
    assert not (root/'state/state.sqlite3').exists() and not (root/'repo/.git').exists()
    static={'status':'PASS','scope':'Review proposals, source byte freeze and budget arithmetic only; not accepted launch argv','launch_status':'NO_GO','revision':revision,'root':str(root),'source_files':len(files),'blockers':blockers,'real_cli_starts':0,'api_starts':0,'model_turns':0,'target_starts':0}
    (out/'static-check.json').write_text(json.dumps(static,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(static,ensure_ascii=False))

if __name__=='__main__':main()
