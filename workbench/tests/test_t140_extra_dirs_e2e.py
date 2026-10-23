"""T-140: real daemon, gates, Electron/CDP and installed interactive Claude/Codex CLIs.
The two model APIs are local scripted endpoints; no vendor model turns or user credentials.

Failure modes (written before implementation of the test):
1. No Edit Project menu/dialog; settings never reach the daemon or are not durable events.
2. X is readable but not writable by shell/file tools; unrelated Y becomes writable.
3. Removal only hides X; a newly dispatched worker still has its old write grant.
4. Reviewer launch validation rejects legitimate extra directories, or monitors miss them.
5. Launch records omit the actual extra-directory arguments; non-operator can change grants.
6. Saved removal overwrites the add event; project-terminal launch parameters change.
7. Driver clicks remove/save in one JavaScript task, before React commits the removal.

Expected values come from T-140, not production helpers. --revision runs the same contract on
old sources; --mutant runs an intentionally broken source copy. Every summary path is new.
External X/Y live in a test-owned /Users/Shared fixture because Codex's ordinary /tmp write
grant would make a /tmp-based Y an invalid negative control. CODEX_HOME stays under /tmp.
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
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--codex', default=shutil.which('codex'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['claude-shell-deny-extra', 'removed-directory-retained'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], observed={}, model_calls=0,
                  model_interfaces='local scripted Messages and Responses APIs; no auth.json copied')
    fixture = electron = server = codex_home = None
    api = dict(requests=0, outputs={}, error=None)
    tasks = {'T-C': ('Claude Code', True), 'T-D': ('Codex', True),
             'T-RC': ('Claude Code', False), 'T-RD': ('Codex', False)}

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def probe(cwd, key, result_name='result.json'):
        # Each path has its own result file: a denied/removed write cannot be hidden by an older file.
        code = ('import json,pathlib\nresult={}\n'
                f'for name,path in {repr([(name, str(path / (key + ".txt"))) for name, path in (("x", x), ("y", y))])}:\n'
                ' try:\n  pathlib.Path(path).write_text("T-140\\n"); result[name]=True\n'
                ' except OSError:\n  result[name]=False\n'
                f'pathlib.Path({str(Path(cwd) / result_name)!r}).write_text(json.dumps(result))\nprint(json.dumps(result))')
        return 'python3 -c ' + quote(code)

    def plan(cwd, text):
        monitor = re.search(r'T140_MONITOR_(C|D)', text)
        if monitor:
            key = 'monitor-' + monitor.group(1)
            return key, [probe(cwd, key)], '观察完毕。'
        if '审查这一次交付' in text:
            shape, _ = json.JSONDecoder().raw_decode(text[text.rindex('{\n  "schema": 1'):])
            task = shape['task'].removeprefix('demo+')
            assert task in tasks, f'unknown review task: {shape["task"]}'
            shape.update(verdict='可合并', findings=[], report={'结论': '写入结果满足任务卡，额外目录改动不纳入集成。',
                '完成条件与变异检查': '变异 1：把结果改为空对象，完成条件退出非零；变异 2：删除结果文件，完成条件退出非零。'})
            return 'review-' + task, [probe(cwd, 'review-' + task),
                                      f"printf '{{}}' > result-{task}.json; python3 check_{task}.py; echo \"mutation-1 rc=$?\"",
                                      f'rm result-{task}.json; python3 check_{task}.py; echo "mutation-2 rc=$?"'], json.dumps(shape, ensure_ascii=False)
        task = next((name for name in sorted(tasks, key=len, reverse=True) if f'/{name}-a1' in cwd), None)
        assert task, f'unknown working directory: {cwd}'
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return task, [probe(cwd, task, f'result-{task}.json'), f'git add result-{task}.json',
                      'git commit -q -m ' + quote('T-140 ' + task), submit], ('已交付。改过的额外目录：' + str(x) if tasks[task][1] else '已交付。额外目录：无改动。')

    def claude_plan(body):
        cwd, text = working_directory(body), prompt_text(body)
        key, commands, final = plan(cwd, text)
        steps = [('Bash', dict(command=command, description='T-140 write boundary')) for command in commands]
        if key in ('T-C', 'T-RC'):
            steps.insert(1, ('Write', dict(file_path=str(x / (key + '-file-tool.txt')), content='file tool\n')))
        return key, steps, final

    class CodexApi(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                if request_source(body) == 'thread_title':
                    events = message_events(json.dumps({'title': 'T-140 fixture'}), body['model'])
                else:
                    text = '\n'.join(part.get('text', '') for item in body['input'] if item.get('type') == 'message' and item.get('role') == 'user'
                                     for part in item.get('content', []) if isinstance(part, dict))
                    cwd = re.search(r'<cwd>([^<]+)</cwd>', text).group(1)
                    key, commands, final = plan(cwd, text)
                    done = [item for item in body['input'] if item.get('type') == 'custom_tool_call']
                    api['outputs'][key] = [str(item.get('output'))[:4000] for item in body['input'] if item.get('type') == 'custom_tool_call_output']
                    events = (tool_events(shell_item(request_tools(body), commands[len(done)], cwd), body['model'])
                              if len(done) < len(commands) else message_events(final, body['model']))
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'{type(error).__name__}: {error}'
                self.send_error(500)

    try:
        patches = {
            # --add-dir and Edit allow also grant Bash writes. Explicitly deny only the worker's
            # shell write to X, leaving file-tool grants and the reviewer launch unchanged.
            'claude-shell-deny-extra': [('src/panes.ts',
                'review || monitor ? [] : await workerGitDenied(launchWorkspace), extraDirectories)',
                'review || monitor ? [] : [...await workerGitDenied(launchWorkspace), ...extraDirectories], extraDirectories)')],
            'removed-directory-retained': [('src/store.ts', "else if (opened.has(data.project_id)) opened.get(data.project_id)!.extra_directories = data.extra_directories;",
                                          "else if (opened.has(data.project_id) && data.extra_directories.length) opened.get(data.project_id)!.extra_directories = data.extra_directories;")],
        }.get(args.mutant, [])
        fixture = Fixture('t140-', claude_plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        external = Path(tempfile.mkdtemp(prefix='t140-extra-', dir='/Users/Shared')).resolve()
        report['external_fixture'] = str(external)
        x, y = external / 'X', external / 'Y'
        x.mkdir(); y.mkdir()
        codex_home = fixture.home / '.codex'
        (codex_home / 'rules').mkdir(parents=True)
        server = ThreadingHTTPServer(('127.0.0.1', 0), CodexApi)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (codex_home / 'config.toml').write_text('model_provider="t140"\ncli_auth_credentials_store="file"\n[model_providers.t140]\nname="T140 fixture"\n'
            f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
        (codex_home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                     'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
        # Reuse the real daemon/terminal fixture while supplying both installed CLI executables.
        original_cli = fixture.run_cli

        def configured_cli(*arguments):
            if arguments[0] == 'daemon_start':
                path = fixture.dir / 'launch-config.json'
                config = json.loads(path.read_text(encoding='utf-8'))
                config.update(codex_bin=args.codex, codex_home=str(codex_home))
                path.write_text(json.dumps(config), encoding='utf-8')
            return original_cli(*arguments)

        fixture.run_cli = configured_cli
        files = {'README.md': 'T-140 fixture\n'}
        for task, (_, allowed) in tasks.items():
            expected = dict(x=allowed, y=False)
            files[f'check_{task}.py'] = ('import json,pathlib\n'
                f'assert json.loads(pathlib.Path("result-{task}.json").read_text()) == {expected!r}\n')
        fixture.start(args.claude, files)
        report['versions'] = {name: subprocess.check_output([binary, '--version'], text=True).strip()
                              for name, binary in [('Claude Code', args.claude), ('Codex', args.codex)]}
        electron = Electron(fixture, fixture.dir.name)
        electron.until('project row', "!!document.querySelector('[data-project-id=\"demo\"]')")

        def edit():
            electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:80,clientY:120}))")
            electron.until('Edit Project menu', "!!document.querySelector('[data-edit-project]')", 10)
            electron.evaluate("document.querySelector('[data-edit-project]').click()")
            electron.until('Edit Project dialog', "document.querySelector('dialog.project-settings')?.open && !document.querySelector('[data-project-save]').disabled")

        edit()  # The old revision must fail here, for the expected absent Edit Project menu.
        check('edit_project_dialog', electron.evaluate("document.querySelector('.project-settings').innerText.includes('额外目录里的改动不进门禁的审查与集成')"))
        electron.evaluate("document.querySelector('[aria-label=\"关闭编辑项目\"]').click()")
        refused = fixture.request('project_settings_save', fixture.terminal, project='demo', extra_directories=[str(x)])
        check('operator_only_settings', not refused.get('ok'), refused)
        saved = fixture.request('project_settings_save', fixture.operator, project='demo', extra_directories=[str(x)])
        check('directory_added', saved.get('ok'), saved)
        def create(task):
            cli, _ = tasks[task]
            path = fixture.out / (task + '.json')
            card = dict(id=task, source=None, goal=f'写 result-{task}.json 记录 X/Y 的实际写入结果', non_goals=['不改其他受控文件'],
                paths=dict(allow=[f'result-{task}.json'], deny=[]), oracle_paths=[f'check_{task}.py'],
                completion_conditions=[dict(argv=['python3', f'check_{task}.py'])], red_commands=[], task_type='测试', repair_target=None,
                complexity='S', executor=dict(cli=cli, model='claude-haiku-5-5' if cli == 'Claude Code' else 'gpt-6.1-sol', effort='low'), base_commit=None, writer=None)
            path.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            for result in [fixture.request('card_save', fixture.terminal, task=task, card=str(path), expected_version=0),
                           fixture.request('create', fixture.terminal, task=task, project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)]:
                assert result.get('ok'), result
            dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            attempt = dispatched['attempt']
            file = Path(attempt['workspace']) / f'result-{task}.json'
            fixture.wait(task + ' writes', lambda: file.exists(), 180)
            observed = json.loads(file.read_text())
            report['observed'][task] = dict(attempt=attempt, result=observed)
            check(task + '_shell_boundary', observed == dict(x=tasks[task][1], y=False), observed)
            fixture.wait(task + ' submitted', lambda: fixture.request('status', fixture.operator, task=task)['task']['state'] == 'submitted', 180)

        for task in ('T-C', 'T-D'):
            create(task)
        check('claude_file_tool_allowed', (x / 'T-C-file-tool.txt').is_file())

        # Reviewers must still pass the unchanged gate pipeline with these explicit write grants.
        for task in ('T-C', 'T-D'):
            verified = fixture.request('verify', fixture.terminal, task=task)
            assert verified.get('ok'), verified
            fixture.wait(task + ' review complete', lambda: fixture.request('status', fixture.operator, task=task)['task']['state'] == 'verified', 240)
            check(task + '_reviewer_extra_write', (x / ('review-' + task + '.txt')).is_file() and not (y / ('review-' + task + '.txt')).exists())

        # Monitor roles remain observational in their role cards, but get the project's write grant too.
        for suffix, cli in [('C', 'Claude Code'), ('D', 'Codex')]:
            instructions = fixture.out / ('monitor-' + suffix + '.txt')
            instructions.write_text('T140_MONITOR_' + suffix, encoding='utf-8')
            attached = fixture.request('attach', fixture.terminal, task='T-C', role='monitor', instructions=str(instructions), cli=cli,
                                       model='claude-haiku-5-5' if suffix == 'C' else 'gpt-6.1-sol', effort='low')
            assert attached.get('ok'), attached
            result_file = Path(attached['attachment']['workspace']) / 'result.json'
            fixture.wait('monitor ' + suffix + ' write', lambda: result_file.exists(), 180)
            check('monitor_' + suffix + '_boundary', json.loads(result_file.read_text()) == dict(x=True, y=False))

        edit()
        electron.until('saved X listed', f"!!document.querySelector('[data-extra-directory={json.dumps(str(x))}]')")
        electron.screenshot(fixture.out / '01-project-settings.png')
        electron.evaluate("document.querySelector('[data-extra-directory] button').click()")
        # A separate browser task observes the committed React state before clicking Save.
        electron.until('X removed from draft', "document.querySelectorAll('.project-settings [data-extra-directory]').length === 0")
        electron.evaluate("document.querySelector('[data-project-save]').click()")
        electron.until('settings closed', "!document.querySelector('dialog.project-settings')")
        settings = [event['data'] for event in fixture.request('orchestration_events')['events'] if event['type'] == 'project_settings_saved']
        report['observed']['settings_after_remove'] = settings
        check('remove_saves_empty_directory_list', [event['extra_directories'] for event in settings] == [[str(x)], []], settings)
        for task in ('T-RC', 'T-RD'):
            create(task)
        check('claude_file_tool_removed', not (x / 'T-RC-file-tool.txt').exists())
        rows = fixture.request('orchestration_events')['events']
        settings = [event['data'] for event in rows if event['type'] == 'project_settings_saved']
        check('append_only_add_and_remove', [event['extra_directories'] for event in settings] == [[str(x)], []], settings)
        # Launch records are persisted in the real SQLite store, independently of the renderer.
        import sqlite3
        with sqlite3.connect(fixture.state / 'state.sqlite3') as db:
            launches = [json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records ORDER BY rowid')]
        report['observed']['launches'] = launches
        for task, (_, allowed) in tasks.items():
            launch = next(row for row in launches if row['task'] == 'demo+' + task and row['role'] == 'worker')
            check(task + '_argv', ('--add-dir' in launch['argv'] and str(x) in launch['argv']) if allowed else str(x) not in launch['argv'], launch['argv'])
        shell = next(row for row in launches if row['id'] == fixture.terminal_launch)
        check('project_terminal_unchanged', shell['shell_argv'] == ['-l', '-i'])
        edit()
        check('removed_directory_not_listed', electron.evaluate("document.querySelectorAll('[data-extra-directory]').length === 0"))
        electron.screenshot(fixture.out / '02-project-settings-removed.png')
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['codex_api'] = api
        if fixture:
            report['claude_api'] = fixture.api.snapshot()
            # Keep the real launch parameters even if an early shell assertion rejects a mutant.
            database = fixture.state / 'state.sqlite3'
            if database.exists():
                import sqlite3
                with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as db:
                    report['observed']['launches'] = [json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records ORDER BY rowid')]
        try:
            if electron:
                electron.stop()
            if fixture:
                fixture.stop()
        finally:
            if server:
                server.shutdown()
            if codex_home and codex_home.exists():
                shutil.rmtree(codex_home)  # Only this test's isolated /tmp CODEX_HOME, never the user's.
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
