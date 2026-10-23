"""T-141: real daemon, Electron and installed interactive CLIs; scripted Messages/Responses.

Independent observations: public curl response, actual external files, MCP server receipt,
native escalation rejection, the issue panel, controller answer and worker continuation.
Known-bad runs: --revision; network-closed, answer-dropped, shared-temp-writable,
native-tools-unrestricted mutants.
No vendor model calls or user config writes. The fixture HOME contains its own user-scope
MCP configuration; CODEX_HOME contains only fixture config and two git prefix rules.

失败方式：
1. 任一真实 CLI 的 curl 被拒，或 Codex 启动记录仍关闭网络。
2. 用户作用域 MCP 未加载、调用被拒，或服务未收到真实工具请求。
3. 范围外写入成功、额外目录不能写，或收紧临时目录导致 shell 不能运行。
4. 原生审批请求等待而非返回拒绝，或 issue 没进问题面板。
5. 执行主控的答复没送到原 worker，worker 没继续并交付。
6. 新启动参数被 reviewer 门禁拒收，或 reviewer 未运行独立的两个坏结果。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote, working_directory
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events

ANSWER = 'T141_REPLY: 保持写入边界，改用 worktree 内的结果文件，然后完成交付。'
TITLE = 'T141_NATIVE_APPROVAL_DENIED'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--codex', default=shutil.which('codex'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['network-closed', 'answer-dropped', 'shared-temp-writable', 'native-tools-unrestricted'])
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve previous evidence: choose a fresh summary path'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], observed={}, model_calls=0,
                  authentication='scripted local APIs; no auth.json copied; isolated /tmp CODEX_HOME removed at exit')
    repo_root = Path(__file__).resolve().parents[2]
    report['source_revision'] = subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=repo_root, text=True).strip()
    report['source_worktree_changes'] = subprocess.check_output(['git', 'status', '--short'], cwd=repo_root, text=True).splitlines()
    fixture = electron = server = codex_home = None
    api = dict(requests=0, outputs={}, error=None, answers_seen=0, escalation_call=None)
    mcp_receipt = None
    tasks = {'T-C': 'Claude Code', 'T-D': 'Codex'}

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def gate(text, arguments):
        line = re.search(r'显式交付：\n(.+)\n', text).group(1)
        task = re.search(r"'--task' '([^']+)'", line).group(1)
        return line[:line.index("'submit'")] + arguments.replace('{task}', task)

    def boundary(cwd, task):
        paths = [('extra', x / (task + '.txt')), ('outside', y / (task + '.txt')),
                 ('slash_tmp', Path('/tmp') / (fixture.dir.name + '-' + task)),
                 ('original_tmpdir', Path(os.environ.get('TMPDIR', '/tmp')) / (fixture.dir.name + '-' + task))]
        code = ('import json,os,pathlib,tempfile\nr={}\n'
                f'for key,path in {[(key, str(path)) for key, path in paths]!r}:\n'
                ' try:\n  pathlib.Path(path).write_text("T141"); r[key]=True\n'
                ' except OSError:\n  r[key]=False\n'
                'r["shell_tmpdir"]=os.environ.get("TMPDIR")\n'
                'try:\n'
                ' with tempfile.TemporaryFile() as f: f.write(b"ok")\n'
                ' r["temporary_file"]=True\n'
                'except OSError:\n r["temporary_file"]=False\n'
                f'pathlib.Path({str(Path(cwd) / ("result-" + task + ".json"))!r}).write_text(json.dumps(r))\n'
                'print(json.dumps(r))')
        return 'python3 -c ' + quote(code)

    def plan(cwd, text):
        if '审查这一次交付' in text:
            shape, _ = json.JSONDecoder().raw_decode(text[text.rindex('{\n  "schema": 1'):])
            task = shape['task'].removeprefix('demo+')
            assert task in tasks
            shape.update(verdict='可合并', findings=[], report={
                '结论': '写入边界与结果符合任务卡。',
                '完成条件与变异检查': '把 extra 改为 false、把 outside 改为 true，完成条件分别拒绝。'})
            commands = []
            for field, value in [('extra', False), ('outside', True)]:
                code = ('import json,pathlib,subprocess\n' + f'p=pathlib.Path("result-{task}.json"); original=p.read_text(); r=json.loads(original)\n'
                        f'r[{field!r}]={value!r}; p.write_text(json.dumps(r))\n'
                        f'try:\n rc=subprocess.run(["python3","check_{task}.py"]).returncode; print("mutation-{field} rc="+str(rc))\n'
                        'finally:\n p.write_text(original)\n')
                commands += ['python3 -c ' + quote(code)]
            return 'review-' + task, commands, json.dumps(shape, ensure_ascii=False)
        task = next((name for name in tasks if f'/{name}-a1' in cwd), None)
        assert task, f'unknown worker directory {cwd}'
        commands = ['curl --fail --location --max-time 30 https://example.com', boundary(cwd, task)]
        if task == 'T-D':
            commands += ['T141_ESCALATION', gate(text, f"'issue' '--task' '{{task}}' '--title' '{TITLE}' '--body' '原生审批被 never 拒绝，无法写范围外文件；请确认改用 worktree 内结果。' '--blocking' 'true'")]
            if ANSWER not in text:
                return task, commands, '已上报审批问题，等待主控答复。'
            code = 'import json,pathlib; p=pathlib.Path("result-T-D.json"); r=json.loads(p.read_text()); r["continued"]=True; p.write_text(json.dumps(r))'
            commands += ['python3 -c ' + quote(code)]
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        commands += [f'git add result-{task}.json', 'git commit -q -m ' + quote('T-141 ' + task), submit]
        return task, commands, '已交付；改过的额外目录：' + str(x)

    def claude_plan(body):
        cwd, text = working_directory(body), prompt_text(body)
        key, commands, final = plan(cwd, text)
        steps = [('Bash', dict(command=command, description='T-141 network/write boundary')) for command in commands]
        if key == 'T-C':
            steps[2:2] = [
                ('Write', dict(file_path=str(x / 'T-C-native-file.txt'), content='T141_NATIVE_FILE_OK\n')),
                ('Write', dict(file_path=str(y / 'T-C-native-file.txt'), content='T141_NATIVE_FILE_FORBIDDEN\n')),
                ('mcp__t141_user__ping', {}),
            ]
        return key, steps, final

    class CodexApi(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model'}]}).encode())

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                if request_source(body) == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-141 fixture'}), body['model'])
                else:
                    text = '\n'.join(part.get('text', '') for item in body['input'] if item.get('type') == 'message' and item.get('role') == 'user'
                                     for part in item.get('content', []) if isinstance(part, dict))
                    cwd = re.search(r'<cwd>([^<]+)</cwd>', text).group(1)
                    key, commands, final = plan(cwd, text)
                    done = [item for item in body['input'] if item.get('type') == 'custom_tool_call']
                    api['outputs'][key] = [str(item.get('output')) for item in body['input'] if item.get('type') == 'custom_tool_call_output']
                    if ANSWER in text:
                        api['answers_seen'] += 1
                    if len(done) < len(commands):
                        command = commands[len(done)]
                        item = shell_item(request_tools(body), 'touch ' + quote(str(y / 'escalated.txt')) if command == 'T141_ESCALATION' else command, cwd)
                        if command == 'T141_ESCALATION':
                            # Ask the installed CLI's real shell tool for escalation. Policy never must
                            # return the refusal to the model, without a native approval wait.
                            assert 'sandbox_permissions' in json.dumps(request_tools(body)), 'native shell lacks escalation parameter'
                            item['input'] = item['input'].replace('}));', ', "sandbox_permissions":"require_escalated", "justification":"T141 approval probe"}));')
                            api['escalation_call'] = item['input']
                        events = tool_events(item, body['model'])
                    else:
                        events = message_events(final, body['model'])
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'{type(error).__name__}: {error}'
                self.send_error(500)

    try:
        patches = {
            'network-closed': [('src/panes.ts', '"sandbox_workspace_write.network_access=true"', '"sandbox_workspace_write.network_access=false"')],
            'answer-dropped': [('src/panes.ts', 'const item = await this.dispatch(pane, message, origin === "user" ? "user" : "executor");',
                                'const item = { id: "t141-dropped-answer" };')],
            'shared-temp-writable': [('src/panes.ts', '"sandbox_workspace_write.exclude_slash_tmp=true"',
                                     '"sandbox_workspace_write.exclude_slash_tmp=false"')],
            'native-tools-unrestricted': [('src/panes.ts', '"Bash", "Read", "Glob", "Grep", "mcp__*", ...writable.map',
                                          '"Bash", "Read", "Glob", "Grep", "Write", "mcp__*", ...writable.map')],
        }.get(args.mutant, [])
        fixture = Fixture('t141-', claude_plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        external = Path(tempfile.mkdtemp(prefix='t141-extra-', dir='/Users/Shared')).resolve()
        report['external_fixture'] = str(external)
        x, y = external / 'X', external / 'Y'
        x.mkdir(); y.mkdir()
        mcp_receipt = fixture.out / 'mcp-receipt.jsonl'
        mcp = fixture.dir / 'user-mcp.py'
        mcp.write_text('''import json,sys,pathlib
for line in sys.stdin:
 r=json.loads(line)
 if 'id' not in r: continue
 method=r.get('method')
 if method=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'t141-user','version':'1'}}
 elif method=='tools/list': result={'tools':[{'name':'ping','description':'Return T141_USER_MCP_OK','inputSchema':{'type':'object','properties':{}}}]}
 elif method=='tools/call':
  pathlib.Path(sys.argv[1]).open('a').write(json.dumps(r)+'\\n')
  result={'content':[{'type':'text','text':'T141_USER_MCP_OK'}]}
 else: result={}
 print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':result}),flush=True)
''', encoding='utf-8')
        user_config = fixture.home / '.claude.json'
        settings = json.loads(user_config.read_text(encoding='utf-8'))
        settings['mcpServers'] = {'t141_user': {'type': 'stdio', 'command': sys.executable, 'args': [str(mcp), str(mcp_receipt)]}}
        user_config.write_text(json.dumps(settings), encoding='utf-8')
        codex_home = fixture.home / '.codex'
        (codex_home / 'rules').mkdir(parents=True)
        server = ThreadingHTTPServer(('127.0.0.1', 0), CodexApi)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (codex_home / 'config.toml').write_text('model_provider="t141"\ncli_auth_credentials_store="file"\n'
            f'[projects.{json.dumps(str(fixture.dir))}]\ntrust_level="trusted"\n'
            '[model_providers.t141]\nname="T141 fixture"\n'
            f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
        (codex_home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                     'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
        original_cli = fixture.run_cli

        def configured_cli(*arguments):
            if arguments[0] == 'daemon_start':
                path = fixture.dir / 'launch-config.json'
                config = json.loads(path.read_text(encoding='utf-8'))
                config.update(codex_bin=args.codex, codex_home=str(codex_home))
                config.update(code_revision=report['source_revision'], source_snapshot=str(fixture.source),
                              role_card_revision=report['source_revision'], reviewer_role_card_revision=report['source_revision'])
                path.write_text(json.dumps(config), encoding='utf-8')
            return original_cli(*arguments)

        fixture.run_cli = configured_cli
        files = {'README.md': 'T-141 fixture\n'}
        for task in tasks:
            files[f'check_{task}.py'] = ('import json,pathlib\n' + f'r=json.loads(pathlib.Path("result-{task}.json").read_text())\n'
                'assert r["extra"] is True and r["outside"] is False and r["temporary_file"] is True\n'
                + ('assert r["continued"] is True and r["slash_tmp"] is False and r["original_tmpdir"] is False\n' if task == 'T-D' else ''))
        fixture.start(args.claude, files)
        report['versions'] = {name: subprocess.check_output([binary, '--version'], text=True).strip()
                              for name, binary in [('Claude Code', args.claude), ('Codex', args.codex)]}
        electron = Electron(fixture, fixture.dir.name)
        electron.until('project', "!!document.querySelector('[data-project-id=\"demo\"]')")
        saved = fixture.request('project_settings_save', fixture.operator, project='demo', extra_directories=[str(x)])
        assert saved.get('ok'), saved
        launches = {}
        for task in ('T-D', 'T-C'):
            path = fixture.out / (task + '.json')
            card = dict(id=task, source=None, goal='记录真实写入结果并显式交付', non_goals=['不修改其他受控文件'],
                paths=dict(allow=[f'result-{task}.json'], deny=[]), oracle_paths=[f'check_{task}.py'],
                completion_conditions=[dict(argv=['python3', f'check_{task}.py'])], red_commands=[], task_type='测试', repair_target=None,
                complexity='S', executor=dict(cli=tasks[task], model='claude-haiku-5-5' if task == 'T-C' else 'gpt-6.1-sol', effort='low'), base_commit=None, writer=None)
            path.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            for result in [fixture.request('card_save', fixture.terminal, task=task, card=str(path), expected_version=0),
                           fixture.request('create', fixture.terminal, task=task, project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)]:
                assert result.get('ok'), result
            dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            attempt = dispatched['attempt']
            launch = fixture.request('launch_show', fixture.operator, launch=attempt['runtime_identity']['launch'])['launch']
            launches[task] = launch
            report['observed'][task] = dict(attempt=attempt, launch=launch)
            if task == 'T-D':
                argv = launch['argv']
                check('codex_no_network_denial_in_argv', 'sandbox_workspace_write.network_access=false' not in argv, argv)
                check('codex_inherits_trust_tools_proxy', not any(value.startswith(('projects=', 'features.network_proxy=', 'tools.')) for value in argv), argv)
                check('codex_approval_never', argv[argv.index('-a') + 1] == 'never')
                issue = fixture.wait('native refusal then issue', lambda: next((v for v in fixture.request('issues', fixture.operator, task=task).get('issues', [])
                    if v['issue']['title'] == TITLE), None), 180)
                outputs = api['outputs'].get('T-D', [])
                report['observed']['native_approval_outputs'] = outputs
                check('native_escalation_returns_refusal', len(outputs) >= 3 and
                      any(word in outputs[2].lower() for word in ['never', 'reject', 'approval', 'not allowed']) and not (y / 'escalated.txt').exists(), outputs)
                electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
                electron.until('issue tab', "!!document.querySelector('[data-issues-tab]')")
                electron.evaluate("document.querySelector('[data-issues-tab]').click()")
                electron.until('native approval issue in panel', f"document.querySelector('[data-issue-id=\"{issue['issue']['id']}\"]')?.innerText.includes('{TITLE}') ?? false")
                electron.screenshot(fixture.out / '01-native-approval-issue.png')
                check('native_approval_issue_in_panel', True)
                answered = fixture.request('answer_issue', fixture.terminal, task=task, issue=issue['issue']['id'], answer=ANSWER)
                assert answered.get('ok'), answered
                report['observed']['controller_answer'] = answered
            file = Path(attempt['workspace']) / f'result-{task}.json'
            fixture.wait(task + ' result', lambda: file.exists(), 180)
            if task == 'T-D':
                fixture.wait('worker continues after controller reply', lambda: json.loads(file.read_text()).get('continued'), 120)
                check('answer_received_and_worker_continued', api['answers_seen'] > 0)
            result = json.loads(file.read_text(encoding='utf-8'))
            report['observed'][task]['result'] = result
            if task == 'T-C':
                # The oracle runs in the test process, outside the CLI sandbox. Actual file
                # effects and the native Write results must agree; shell booleans cannot prove this.
                fixture.wait('native file tools have returned', lambda: len(fixture.api.snapshot()['results'].get('T-C', [])) >= 5, 120)
                rows = fixture.api.snapshot()['results']['T-C']
                allowed_file, denied_file = x / 'T-C-native-file.txt', y / 'T-C-native-file.txt'
                check('claude_native_file_tool_boundary', allowed_file.is_file() and
                      allowed_file.read_text(encoding='utf-8') == 'T141_NATIVE_FILE_OK\n' and not denied_file.exists() and
                      rows[2]['is_error'] is False and rows[3]['is_error'] is True, rows[2:4])
                check('claude_mcp_result_reaches_worker', rows[4]['is_error'] is False and 'T141_USER_MCP_OK' in rows[4]['text'], rows[4])
            host_files = dict(extra=x / (task + '.txt'), outside=y / (task + '.txt'),
                              slash_tmp=Path('/tmp') / (fixture.dir.name + '-' + task),
                              original_tmpdir=Path(os.environ.get('TMPDIR', '/tmp')) / (fixture.dir.name + '-' + task))
            host_writes = {key: path.is_file() for key, path in host_files.items()}
            report['observed'][task]['host_writes'] = host_writes
            check(task + '_host_readback_matches_shell_results', host_writes['extra'] and not host_writes['outside'] and
                  all(result[key] is value for key, value in host_writes.items()) and
                  host_files['extra'].read_text(encoding='utf-8') == 'T141', host_writes)
            check(task + '_write_boundary_and_shell_temp', result['extra'] is True and result['outside'] is False and result['temporary_file'] is True, result)
            if task == 'T-D':
                check('codex_shared_temp_roots_denied', not result['slash_tmp'] and not result['original_tmpdir'], result)
            fixture.wait(task + ' submitted', lambda: fixture.request('status', fixture.operator, task=task)['task']['state'] == 'submitted', 180)
        check('claude_user_mcp_executed', mcp_receipt.exists() and json.loads(mcp_receipt.read_text().splitlines()[0])['params']['name'] == 'ping')
        report['observed']['mcp_receipt'] = mcp_receipt.read_text(encoding='utf-8')
        snapshot = fixture.api.snapshot()
        for task, outputs in [('T-C', [row['text'] for row in snapshot['results'].get('T-C', [])]), ('T-D', api['outputs'].get('T-D', []))]:
            check(task + '_public_curl', bool(outputs) and 'Example Domain' in outputs[0], outputs[:1])
        check('claude_curl_exit_success', snapshot['results']['T-C'][0]['is_error'] is False)
        check('codex_curl_exit_success', bool(re.search(r'"exit_code"\s*:\s*0', api['outputs']['T-D'][0].replace('\\', ''))), api['outputs']['T-D'][:1])
        for task in tasks:
            verified = fixture.request('verify', fixture.terminal, task=task)
            assert verified.get('ok'), verified
            fixture.wait(task + ' new reviewer accepted', lambda: fixture.request('status', fixture.operator, task=task)['task']['state'] == 'verified', 240)
            check(task + '_gate_accepts_new_reviewer_argv', True)
            outputs = (api['outputs'].get('review-' + task, []) if task == 'T-D' else
                       [row['text'] for row in fixture.api.snapshot()['results'].get('review-' + task, [])])
            check(task + '_reviewer_rejects_two_independent_bad_results', len(outputs) >= 2 and
                  'mutation-extra rc=1' in outputs[0] and 'mutation-outside rc=1' in outputs[1], outputs)
        electron.screenshot(fixture.out / '02-complete.png')
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['codex_api'] = api
        if fixture:
            report['claude_api'] = fixture.api.snapshot()
            if fixture.running:
                try:
                    events = fixture.request('orchestration_events')['events']
                    report['launches'] = [fixture.request('launch_show', fixture.operator, launch=launch)['launch']
                        for launch in sorted({event['launch'] for event in events if event.get('launch')})]
                    report['diagnostics'] = [event for event in events if any(word in event['type'] for word in ['fail', 'unrecognised', 'trust'])][-20:]
                except (OSError, AssertionError, KeyError) as error:
                    report['status'] = 'INCOMPLETE'
                    report['snapshot_error'] = str(error)
        try:
            if electron:
                electron.stop()
        finally:
            try:
                if fixture:
                    fixture.stop()
            finally:
                try:
                    if server:
                        server.shutdown()
                    if codex_home and codex_home.exists():
                        shutil.rmtree(codex_home)
                finally:
                    report['isolated_codex_home_removed'] = codex_home is None or not codex_home.exists()
                    if not report['isolated_codex_home_removed']:
                        report['status'] = 'INCOMPLETE'
                    args.summary.parent.mkdir(parents=True, exist_ok=True)
                    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
