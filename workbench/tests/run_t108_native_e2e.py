"""Real controller_start -> installed Claude -> hooks -> Electron -> answer.

Only loopback fixture API; never credentials, vendor calls or screenshots.
Use a new summary path. Runtime fixtures remain in /tmp, summary records commands.
"""
import argparse, json, os, shutil, sqlite3, subprocess, sys, tempfile, threading, time, traceback, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from run_t103_picker import Window
from t108_cleanup import stop_owned, observe

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--summary',type=Path,required=True)
    p.add_argument('--electron-dist',type=Path,required=True)
    args=p.parse_args(); source=Path(__file__).resolve().parents[2]
    assert not args.summary.exists()
    root=Path(tempfile.mkdtemp(prefix='t078-2-t108-',dir='/private/tmp')).resolve()
    repo=root/'repo';repo.mkdir();state=root/'state';state.mkdir()
    role=root/'roles/ideation'
    for name in ['home','claude','tmp','shell','requests','hooks','user-data']:(role/name).mkdir(parents=True)
    (root/'manager-home').mkdir()
    (role/'role.md').write_text('你是隔离验收主控。只回答用户请求。\n',encoding='utf-8')
    (role/'claude/settings.json').write_text(json.dumps({'theme':'dark'}),encoding='utf-8')
    (role/'claude/.claude.json').write_text(json.dumps({'hasCompletedOnboarding':True,'projects':{str(repo):{'hasTrustDialogAccepted':True}}}),encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','CLAUDE_','ANTHROPIC_','GIT_')) and k not in ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE']}
    env.update(HOME=str(root/'manager-home'),LC_ALL='C',TMPDIR='/private/tmp',A2A_OPERATOR_CREDENTIAL=str(root/'operator.json'),
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
        GIT_AUTHOR_NAME='T108 fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_NAME='T108 fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid',
        ELECTRON_OVERRIDE_DIST_PATH=str(args.electron_dist.resolve()))
    dist=args.electron_dist.resolve(strict=True); binary=dist/'Electron.app/Contents/MacOS/Electron'
    assert not str(binary).startswith('/Volumes/') and (dist/'version').read_text().strip()=='43.4.1'
    report={'status':'INCOMPLETE','task':'T-108','attempt':'a1','model_turns':0,'model_calls':0,'vendor_calls':0,'fixture':str(root),'commands':[],'checks':[]}
    cli=['node',source/'workbench/src/gates/cli.ts','--state',state]
    windows=[];started=False;build=None;requests=[];native_owner=None;daemon_owner=None
    question={'questions':[{'question':'选择部署区域？','header':'区域','options':[{'label':'东区','description':'第一个区域'},{'label':'西区','description':'第二个区域'}],'multiSelect':False}]}
    root_calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            path=self.path.split('?')[0]
            if path=='/v1/messages/count_tokens':self.send_response(200);self.end_headers();self.wfile.write(b'{"input_tokens":128}');return
            assert path=='/v1/messages'
            requests.append(body)
            root_call=any(tool.get('name')=='AskUserQuestion' for tool in body.get('tools',[]))
            if root_call:root_calls.append(body)
            if len(root_calls)>2 or len(requests)>10:self.send_error(409);return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            def emit(t,v):self.wfile.write(('event: '+t+'\ndata: '+json.dumps({'type':t,**v},ensure_ascii=False)+'\n\n').encode());self.wfile.flush()
            emit('message_start',{'message':{'id':'msg_t108_'+str(len(requests)),'type':'message','role':'assistant','model':'claude-haiku-5-5','content':[],
                'stop_reason':None,'usage':{'input_tokens':128,'output_tokens':0}}})
            if root_call and len(root_calls)==1:
                emit('content_block_start',{'index':0,'content_block':{'type':'tool_use','id':'toolu_e2e_sentinel','name':'AskUserQuestion','input':{}}})
                emit('content_block_delta',{'index':0,'delta':{'type':'input_json_delta','partial_json':json.dumps(question,ensure_ascii=False)}});reason='tool_use'
            else:
                emit('content_block_start',{'index':0,'content_block':{'type':'text','text':''}})
                emit('content_block_delta',{'index':0,'delta':{'type':'text_delta','text':'已收到答复。'}});reason='end_turn'
            emit('content_block_stop',{'index':0});emit('message_delta',{'delta':{'stop_reason':reason,'stop_sequence':None},'usage':{'output_tokens':20}});emit('message_stop',{})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    def run(argv):
        r=subprocess.run(list(map(str,argv)),cwd=source,env=env,capture_output=True,text=True,timeout=180)
        report['commands'].append({'argv':list(map(str,argv)),'exit':r.returncode,'stdout':r.stdout[-4000:],'stderr':r.stderr[-2000:]})
        assert r.returncode==0,report['commands'][-1]
        return r.stdout
    def call(command,*fields):
        value=json.loads(run([*cli,command,*fields]));assert value.get('ok'),value;return value
    def until(read,message):
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            value=read()
            if value:return value
            time.sleep(.1)
        raise AssertionError(message)
    def events():
        with sqlite3.connect('file:'+str(state/'state.sqlite3')+'?mode=ro',uri=True) as db:
            return [{'seq':seq,'launch':launch,'type':t,'data':json.loads(d)} for seq,launch,t,d in db.execute('SELECT seq,launch,type,data FROM orchestration_events ORDER BY seq')]
    try:
        run(['git','init','-b','main',repo]);(repo/'fixture').write_text('isolated\n',encoding='utf-8')
        run(['git','-C',repo,'add','.']);run(['git','-C',repo,'commit','-m','fixture'])
        revision=run(['git','rev-parse','HEAD']).strip()
        card={'id':'T108-fixture','source':None,'goal':'原生提问验收','non_goals':['交付与集成'],
              'paths':{'allow':['.'],'deny':[]},'oracle_paths':['fixture'],
              'completion_conditions':[{'argv':['/usr/bin/false']}],'red_commands':[],'task_type':'后端逻辑','repair_target':None,
              'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'high'},'base_commit':None,'writer':None}
        (root/'card.json').write_text(json.dumps(card,ensure_ascii=False),encoding='utf-8')
        daemon=call('daemon_start');started=True
        daemon_owner=observe(daemon['pid'])
        assert daemon_owner is not None and str(state) in daemon_owner['command'] and str(source/'workbench/src/daemon.ts') in daemon_owner['command']
        call('card_save','--task','T108-fixture','--card',root/'card.json','--expected-version','0')
        call('create','--task','T108-fixture','--repo',repo,'--branch','refs/heads/main','--card-version','1','--project','T108-project')
        manifest={'schema':1,'root':str(root),'state':str(state),'task':'T108-fixture','preset':'ideation',
                  'launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),
                  'executable':'/Users/luckye/.local/bin/claude','version':'2.1.304','role_file':str(role/'role.md'),
                  'code_revision':revision,'source_snapshot':str(source),'api_url':'http://127.0.0.1:'+str(server.server_port),'turn_limit':1}
        (root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        call('controller_start','--task','T108-fixture','--manifest',root/'manifest.json')
        leader=until(lambda:call('pane_process_info','--thread',manifest['thread']).get('leader'),'Native leader not verified')
        native_owner=observe(leader)
        assert native_owner is not None and '--session-id '+manifest['session'] in native_owner['command'] and str(role/'claude-debug.log') in native_owner['command']
        report['owned_processes']={'daemon':daemon_owner,'native':native_owner}
        build=json.loads(run(['node',source/'workbench/app/build.mjs','--slot','t108-e2e-'+uuid.uuid4().hex[:8]]).splitlines()[-1])
        window=Window(source,source/'workbench/tests/t108_questions_driver.mjs',Path(build['out']),state,root/'ui',root/'window',env,windows,
                      {'executable':str(binary),'dist':str(dist),'version':'43.4.1'},task='T108-fixture',through_start=False)
        window.wait(lambda v:v['panes'] and v['panes'][0]['input']=='true','Writable native pane')
        window.call('prompt')
        view=window.wait(lambda v:v['questions'] and '等待用户回答' in v['questions'][0]['text'],'Question and state in Electron')
        assert '选择部署区域？' in view['questions'][0]['text'] and '东区' in view['questions'][0]['text'] and '西区' in view['questions'][0]['text']
        qid=view['questions'][0]['id'];assert qid==manifest['launch']+':toolu_e2e_sentinel'
        sidebar=call('sidebar_snapshot');assert sidebar['agents'][0]['state']=='waiting_user_answer'
        receipt=window.call('answer');report['first_answer_receipt']=receipt
        assert receipt['clicked'] and receipt['final_receipt']['ok'] is True
        first_answer=[e for e in events() if e['type']=='request_received' and e['data'].get('input',{}).get('command')=='window_answer']
        assert len(first_answer)==1 and first_answer[0]['data']['id']==receipt['transport_id']
        terminal=[e for e in events() if e['type'] in ['request_result','request_rejected'] and e['data']['id']==receipt['transport_id']]
        assert len(terminal)==1 and terminal[0]['type']=='request_result' and terminal[0]['data']['ok'] is True
        until(lambda:any(e['type']=='native_question_resolved' and e['data']['status']=='answered' for e in events()),'Native confirmed answer')
        window.wait(lambda v:not v['questions'],'Question removed after native answer')
        until(lambda:call('workbench_snapshot','--task','T108-fixture','--launch',manifest['launch'])['pane']['state']=='idle','Expected matched Stop to return pane to idle after answer')
        completed=events()
        hooks=[json.loads(e['data']['raw_stdin']) for e in completed if e['type']=='hook_received']
        submitted=[h for h in hooks if h['hook_event_name']=='UserPromptSubmit']
        stops=[h for h in hooks if h['hook_event_name']=='Stop']
        assert len(submitted)==1 and len(stops)==1 and stops[0]['prompt_id']==submitted[0]['prompt_id'] and stops[0]['stop_hook_active'] is False
        idle=[(i,e) for i,e in enumerate(completed) if e['type']=='pane_idle']
        resolved=[i for i,e in enumerate(completed) if e['type']=='native_question_resolved' and e['data']['status']=='answered']
        assert len(idle)==1 and idle[0][0]>resolved[-1] and idle[0][1]['data']['stop']==stops[0]
        native=[json.loads(line) for line in Path(stops[0]['transcript_path']).read_text().splitlines()]
        final=[row['message'] for row in native if row.get('type')=='assistant' and row.get('message',{}).get('stop_reason')=='end_turn']
        assert len(final)==1 and ''.join(block.get('text','') for block in final[0]['content'])=='已收到答复。'
        report['native_final_text']='已收到答复。'
        # Paste a fresh nonce without Enter. Observe exact bytes and echo on the
        # same launch trace; no additional root prompt or model call is allowed.
        trace=state/'traces'/manifest['launch']/'pty.raw';offset=trace.stat().st_size
        marker='t108-followup-'+uuid.uuid4().hex
        report['followup_input']={'marker':marker,'launch':manifest['launch'],'trace':str(trace),'offset':offset,'submitted':False}
        followup=window.call('followup',text=marker);assert followup['ok'] is True
        report['followup_input']['request_id']=followup['request_id']
        written=until(lambda:[e for e in events() if e['type']=='terminal_input_written' and e['data'].get('request_id')==followup['request_id']],
                      'Next input did not reach the original PTY')
        intent=[e for e in events() if e['type']=='terminal_input_write_intent' and e['data'].get('request_id')==followup['request_id']]
        assert len(written)==len(intent)==1 and intent[0]['data']['data']=='\x1b[200~'+marker+'\x1b[201~'
        assert written[0]['launch']==intent[0]['launch']==manifest['launch']
        assert written[0]['seq']>receipt['terminal_seq']
        until(lambda:marker.encode() in trace.read_bytes()[offset:],'Same PTY did not echo the next input nonce')
        report['followup_input'].update(written_seq=written[0]['seq'],echoed=True)
        assert window.call('duplicate',question=qid)['rejected']
        with sqlite3.connect('file:'+str(state/'state.sqlite3')+'?mode=ro',uri=True) as db:
            inputs=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs')]
        answers=[row for row in inputs if row['form']=='answer'];assert len(answers)==1 and answers[0]['reply_to']==qid and answers[0]['target']['request']==qid
        assert answers[0]['target']['thread']==manifest['thread'] and '西区' in answers[0]['text']
        assert len(root_calls)==2, 'One root turn, one tool continuation; no extra root input'
        report['checks']=['controller_start_installed_cli','electron_question_options_wait_state','dom_answer_to_original_pty',
                          'native_posttool_answer_and_matched_stop','answer_user_input_links_question','duplicate_refused',
                          'first_window_answer_final_receipt_ok','same_pty_followup_input_written_and_echoed']
        report['hooks']=[json.loads(e['data']['raw_stdin']) for e in events() if e['type']=='hook_received']
        report['status']='PASS'
    except Exception as error:report.update(error=str(error),traceback=traceback.format_exc())
    finally:
        if started:
            try:
                observed=events()
                report['hooks']=[json.loads(e['data']['raw_stdin']) for e in observed if e['type']=='hook_received']
                report['turn_events']=[e for e in observed if e['type'] in ['turn_start_signal','turn_end_signal','stop_not_matched','pane_idle','native_question_resolved']]
            except Exception as error:report['event_diagnostic_error']=str(error)
        for window in windows:
            try:window.close()
            except Exception as error:report['status']='INCOMPLETE';report['window_cleanup_error']=str(error)
        if started:
            try:call('daemon_stop');until(lambda:not (state/'daemon.pid').exists(),'Daemon cleanup')
            except Exception as error:report['status']='INCOMPLETE';report['daemon_cleanup_error']=str(error)
        report['cleanup']=[]
        for owner in [native_owner,daemon_owner]:
            if owner:
                try:report['cleanup'].append(stop_owned(owner))
                except Exception as error:report['status']='INCOMPLETE';report.setdefault('process_cleanup_errors',[]).append(str(error))
        report['fake_api_root_requests']=len(root_calls)
        report['fake_api_total_requests']=len(requests)
        report['fake_api_requests']=[{'ordinal':i+1,'root':any(t.get('name')=='AskUserQuestion' for t in body.get('tools',[])),
            'tool_results':[part.get('tool_use_id') for message in body.get('messages',[]) if isinstance(message.get('content'),list)
                            for part in message['content'] if part.get('type')=='tool_result']} for i,body in enumerate(requests)]
        server.shutdown();server.server_close()
        if build and all(window.proc.poll() is not None for window in windows):
            # Only this test's newly created build cache, after Electron exited.
            shutil.rmtree(Path(build['out']).parent)
        elif build:
            report['preserved_build']=build['out']
            report['status']='INCOMPLETE'
        args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':report['status'],'summary':str(args.summary),'error':report.get('error'),'model_turns':0},ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
