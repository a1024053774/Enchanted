"""T-133 方案 A 与 T-107 #2、#4、#5：项目终端里由用户自己启动、经角色申请批准的 Claude Code 主控。真实后台、门禁、
项目终端（zsh 与包装脚本），终端里跑真实 Claude Code（模型是本地脚本化接口），真实 Electron 窗口经 DevTools 协议操作。

场景（期望来自 ticket 与用户决定，不读被测代码的输出）：
1. 终端 I 里启动 claude，用户提交 REQUEST_IDEATION；它运行 `a2a request ideation`，用户在界面批准。这条提示词在批准
   之前提交，不记（只记已批准主控提交的整句）。
2. 用户在终端 I 提交 IDEA_PROMPT（批准之后）。主控用 AskUserQuestion 问用户，此时侧栏是“等待用户回答”；用户在终端里
   选第一个选项，之后主控跑一条 20 秒的命令，侧栏是“运行中”；回合结束后是“空闲”。
3. 终端 X 里启动 claude，用户提交 REQUEST_EXECUTOR，它申请执行主控。界面上的批准卡片有“上级”选项，默认是终端 I 的
   构思主控；用户批准。侧栏里执行主控挂在构思主控下。
（审查 01 后补充：同一次运行里，桌面操作员派出 T-1 的 worker，用户在问题面板答复它的上报、在它的窗格里打一段字，两条都标人工介入。）
4. 用户在终端 I 让它放弃身份（`a2a release`），之后再提交 AFTER_RELEASE。
   记录页列出 IDEA_PROMPT、RELEASE（主控终端提交、构思主控）和对 AskUserQuestion 的答复，不列 REQUEST_IDEATION、
   REQUEST_EXECUTOR（批准之前）与 AFTER_RELEASE（身份结束之后）。
5. 项目行第二行显示分支与领先/落后数，与 `git rev-list --left-right --count` 一致（本地领先上游 1 个提交）。

失败方式（先列再写）：
1. 批准前或没有角色的会话的提示词被记下（不该记的记了）。
2. 批准后的整句没记、记成别的文字，或记录页的角色/来源不对。
3. 终端主控的状态不随回合变化：问用户时不是“等待用户回答”，跑命令时不是“运行中”，结束后不是“空闲”。
4. 批准时选的上级没保存，执行主控进“未归属”。
5. 分支行不显示或数字与 git 不一致。
6. 钩子往终端输出或改变回合（提示词被拦下、模型看到钩子输出）。
--revision 在该版本源码上跑（修前没有钩子）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote  # noqa: E402

REQUEST_IDEATION = 'T-133：请申请构思主控'
REQUEST_EXECUTOR = 'T-133：请申请执行主控'
IDEA_PROMPT = 'T-133 用户对构思主控说：先看看哪些 ticket 就绪了'
QUESTION = '先做哪一个？'
CHOICE = 'T-1 先做'
RELEASE = 'T-133：请放弃构思主控身份'
AFTER_RELEASE = 'T-133：放弃身份之后说的话'
ANSWER = 'T-133：先按卡做，格式以后再说。'
TYPED = 'T-133：用户在 worker 窗格里打的字'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['recorded-without-role', 'terminal-state-unknown', 'parent-not-saved'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    patches = {
        # A prompt kept whether or not the terminal holds an approved role.
        'recorded-without-role': [('src/daemon.ts', "if (!held || !held.native_session || payload?.session_id !== held.native_session) return { ok: true, kept: false };",
                                   "const held = roleRequests.all().filter(row => row.launch === terminal.id).at(-1) ?? roleRequests.approved(terminal.id);\n"
                                   "      if (!held) return { ok: true, kept: false };"),
                                  ('src/daemon.ts', "      const held = roleRequests.approved(terminal.id);\n      let payload: any;", "      let payload: any;")],
        # The terminal controller's state left unknown, as before T-107 #4.
        'terminal-state-unknown': [('src/sidebar.ts', "parent: roleRequest.parent_launch, state, question_id: null, state_label: stateLabels[state],",
                                    "parent: roleRequest.parent_launch, state: 'unknown', question_id: null, state_label: stateLabels.unknown,")],
        # The parent the user picked not saved with the decision.
        'parent-not-saved': [('src/roleRequests.ts', "...(parent ? { parent_launch: parent } : {})", "")],
    }.get(args.mutant, [])

    def plan(body):
        text = json.dumps(body['messages'], ensure_ascii=False)
        cwd = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        if cwd and cwd.group(1).endswith('/T-1-a1'):
            # The managed worker: it reports an issue, then delivers.
            first = prompt_text(body)
            submit = re.search(r'显式交付：\n(.+)\n', first).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
            issue = gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote('a.txt 的格式没写')} '--body' {quote('先按纯文本做。')} '--blocking' 'false'")
            return 'worker:T-1', [('Bash', dict(command=issue, description='issue')),
                                  ('Write', dict(file_path=f'{cwd.group(1)}/a.txt', content='a\n')),
                                  ('Bash', dict(command='git add a.txt', description='stage')),
                                  ('Bash', dict(command='git commit -q -m "T-1 fixture change"', description='commit')),
                                  ('Bash', dict(command=submit, description='submit'))], '已交付。'
        if REQUEST_EXECUTOR in text:
            return 'executor', [('Bash', dict(command='a2a request executor', description='request the executor role'))], '执行主控已获批。'
        assert REQUEST_IDEATION in text, prompt_text(body)[:300]
        steps = [('Bash', dict(command='a2a request ideation', description='request the ideation role'))]
        if IDEA_PROMPT in text:
            steps += [('AskUserQuestion', dict(questions=[dict(question=QUESTION, header='顺序', multiSelect=False,
                                                                options=[dict(label=CHOICE, description='先做 T-1'), dict(label='T-2 先做', description='先做 T-2')])])),
                      ('Bash', dict(command='sleep 20', description='read the map slowly'))]
        if RELEASE in text:
            steps += [('Bash', dict(command='a2a release', description='give the role back'))]
        return 'ideation', steps, '好的。'

    fixture = Fixture('t133t-', plan, revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def git(repo, *arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True, env=fixture.env).strip()

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def terminal(name):
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        return dict(name=name, launch=launch, identity=window['identity'], sequence=0)

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def screen(term):
        raw = (fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    def ready(term):
        # Claude Code's input box is up once its banner and the prompt marker are drawn.
        text = screen(term)
        return 'ClaudeCodev' in text and '❯' in text[text.index('ClaudeCodev'):]

    def submit(term, text):
        type_in(term, text)
        time.sleep(1)
        type_in(term, '\r')

    def approve(card):
        # The approve button is disabled while the sidebar settles; click it once it is enabled.
        electron.until('批准', f"(()=>{{const b=[...document.querySelectorAll('[data-role-request=\"{card}\"] button')].find(b=>b.textContent==='批准');"
                       "if(!b||b.disabled)return false;b.click();return true})()", 20)

    def agent(launch):
        return electron.evaluate(f"(()=>{{const r=document.querySelector('.agent-row[data-agent-launch=\"{launch}\"]');"
                                 "return r&&{state:r.dataset.agentState,parent:r.dataset.agentParent,level:r.dataset.agentLevel,role:r.querySelector('.agent-role').textContent}})()")

    def state_is(launch, value):
        return f"document.querySelector('.agent-row[data-agent-launch=\"{launch}\"]')?.dataset.agentState === {json.dumps(value)}"

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check_T-1.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("a.txt").is_file() else 1)\n'})
        # The fixture's own socket-only executor gives its role back, so the user's CLI can ask for it.
        assert fixture.request('role_release', fixture.terminal)['ok']
        # The fixture user already trusts the project in their own Claude and allows the two commands the controllers run.
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        (fixture.home / '.claude').mkdir(exist_ok=True)
        (fixture.home / '.claude/settings.json').write_text(json.dumps({'permissions': {'allow': ['Bash(a2a request:*)', 'Bash(a2a release:*)', 'Bash(sleep:*)']}}), encoding='utf-8')
        # The project one commit ahead of its upstream.
        remote = fixture.dir / 'demo-remote.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(remote)], check=True, env=fixture.env)
        git(fixture.repo, 'remote', 'add', 'origin', str(remote))
        git(fixture.repo, 'push', '-q', '-u', 'origin', 'main')
        (fixture.repo / 'NOTES.md').write_text('notes\n', encoding='utf-8')
        git(fixture.repo, 'add', 'NOTES.md')
        git(fixture.repo, 'commit', '-q', '-m', 'local change')

        electron = Electron(fixture, 't133t-' + fixture.dir.name[6:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")

        ideation = terminal('I')
        type_in(ideation, f'claude --model claude-haiku-5-5\r')
        fixture.wait('终端 I 的 Claude 启动', lambda: ready(ideation), 60)
        submit(ideation, REQUEST_IDEATION)
        request_card = electron.until('构思主控申请出现', "document.querySelector('[data-role-request]')?.dataset.roleRequest ?? null", 60)
        approve(request_card)
        electron.until('构思主控出现', f"!!document.querySelector('.agent-row[data-agent-launch=\"{ideation['launch']}\"]')", 40)
        electron.until('构思主控回合结束：空闲', state_is(ideation['launch'], 'idle'), 60)
        check('ideation_idle_after_first_turn', True)

        submit(ideation, IDEA_PROMPT)
        electron.until('问用户：等待用户回答', state_is(ideation['launch'], 'waiting_user_answer'), 60)
        electron.screenshot(fixture.out / '01-waiting-user-answer.png')
        check('ideation_waiting_user_answer_on_question', True)
        fixture.wait('问题显示在终端', lambda: QUESTION.replace(' ', '') in screen(ideation), 30)
        type_in(ideation, '\r')
        electron.until('答完跑命令：运行中', state_is(ideation['launch'], 'running'), 30)
        electron.screenshot(fixture.out / '02-running.png')
        check('ideation_running_after_answer', True)
        electron.until('回合结束：空闲', state_is(ideation['launch'], 'idle'), 60)
        check('ideation_idle_after_turn', True)
        report['observed']['ideation_results'] = fixture.api.results.get('ideation')

        executor = terminal('X')
        type_in(executor, f'claude --model claude-haiku-5-5\r')
        fixture.wait('终端 X 的 Claude 启动', lambda: ready(executor), 60)
        submit(executor, REQUEST_EXECUTOR)
        request_card = electron.until('执行主控申请出现', "document.querySelector('[data-role-request]')?.dataset.roleRequest ?? null", 60)
        offered = electron.evaluate(f"(()=>{{const s=document.querySelector('[data-role-request-parent=\"{request_card}\"]');"
                                    "return s&&{value:s.value,options:[...s.options].map(o=>({value:o.value,text:o.textContent}))}})()")
        report['observed']['parent_choice'] = offered
        check('approval_offers_ideation_as_parent', offered and offered['value'] == ideation['launch'] and
              [o['value'] for o in offered['options']] == [ideation['launch'], ''], offered)
        electron.screenshot(fixture.out / '03-executor-request.png')
        approve(request_card)
        electron.until('执行主控出现', f"!!document.querySelector('.agent-row[data-agent-launch=\"{executor['launch']}\"]')", 40)
        electron.until('执行主控回合结束', state_is(executor['launch'], 'idle'), 60)
        rows = {launch: agent(launch) for launch in (ideation['launch'], executor['launch'])}
        report['observed']['rows'] = rows
        electron.screenshot(fixture.out / '04-tree.png')
        check('executor_under_ideation', rows[executor['launch']]['parent'] == ideation['launch'] and rows[executor['launch']]['level'] == '1' and
              rows[ideation['launch']]['level'] == '0' and rows[ideation['launch']]['role'] == '构思主控' and rows[executor['launch']]['role'] == '执行主控', rows)

        # Branch line against git itself.
        ahead, behind = git(fixture.repo, 'rev-list', '--left-right', '--count', 'HEAD...@{u}').split()
        branch = git(fixture.repo, 'rev-parse', '--abbrev-ref', 'HEAD')
        shown = electron.until('分支行', "document.querySelector('[data-project-git=\"demo\"]')?.textContent ?? null", 20)
        report['observed']['git'] = dict(branch=branch, ahead=ahead, behind=behind, shown=shown)
        check('branch_line_matches_git', shown == f'{branch} · ↑{ahead} ↓{behind}' and (ahead, behind) == ('1', '0'), report['observed']['git'])

        # Review 01: a managed worker in the same run. The user answers its issue from the desktop and types in its pane.
        # The operator has no project of its own, so it names the task by its full id.
        card = fixture.out / 'T-1.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录加 a.txt', non_goals=['不改别的文件'], paths=dict(allow=['a.txt'], deny=[]),
            oracle_paths=['check_T-1.py'], completion_conditions=[dict(argv=['python3', 'check_T-1.py'])], red_commands=[], task_type='测试', repair_target=None,
            complexity='S', executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        saved = fixture.request('card_save', fixture.operator, task='demo+T-1', card=str(card), expected_version=0)
        assert saved.get('ok'), saved
        created = fixture.request('create', fixture.operator, task='demo+T-1', project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)
        assert created.get('ok'), created
        dispatched = fixture.request('dispatch', fixture.operator, task='demo+T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        views = fixture.wait('T-1 问题进门禁', lambda: fixture.request('issues', fixture.operator, task='demo+T-1')['issues'], 120)
        # The gate's operation lock may be held by the worker's own call at that moment (operation_busy); only that is retried.
        def answer():
            result = fixture.request('answer_issue', fixture.operator, task='demo+T-1', issue=views[0]['issue']['id'], answer=ANSWER)
            assert result.get('ok') or result.get('error') == 'operation_busy', result
            return result.get('ok')
        fixture.wait('答复问题', answer, 60)
        fixture.wait('T-1 交付', lambda: fixture.request('status', fixture.operator, task='demo+T-1')['task']['state'] == 'submitted', 180)
        worker = dispatched['attempt']['runtime_identity']['launch']
        pane = fixture.request('window_open', fixture.operator, launch=worker, task=dispatched['attempt']['task_id'])
        assert pane['ok'], pane
        for sequence, data in enumerate(['\x1b[200~' + TYPED + '\x1b[201~', '\r'], 1):
            assert fixture.request('window_input', pane['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)['ok']
            time.sleep(.5)
        fixture.wait('键入送到 worker', lambda: any(TYPED in json.dumps(b['messages'], ensure_ascii=False) for b in fixture.api.bodies if b['key'] == 'worker:T-1'), 120)

        # The ideation controller gives its role back; what the user says after that is not a controller prompt.
        submit(ideation, RELEASE)
        fixture.wait('身份已放弃', lambda: not any(a['id'] == ideation['launch'] for a in fixture.request('sidebar_snapshot')['agents']), 60)
        # The model answers right after the release command returns; that turn's Stop comes then.
        fixture.wait('放弃身份的回合结束', lambda: len(fixture.api.results.get('ideation', [])) >= 4, 30)
        time.sleep(3)
        submit(ideation, AFTER_RELEASE)
        fixture.wait('放弃之后的话送到模型', lambda: any(AFTER_RELEASE in json.dumps(b['messages'], ensure_ascii=False) for b in fixture.api.bodies), 60)
        time.sleep(3)

        # The records: only what the approved controller's CLI submitted, and the user's answer to its question.
        stored = [json.loads(row['data']) for row in database("SELECT data FROM user_inputs WHERE json_extract(data,'$.target.project')='demo' ORDER BY rowid")]
        report['observed']['stored'] = [dict(id=i['id'], form=i['form'], channel=i['channel'], text=i['text'], thread=i['target']['thread']) for i in stored]
        terminal_rows = [i for i in stored if i['channel'] == 'controller-terminal']
        check('only_approved_prompts_recorded', [(i['form'], i['text']) for i in terminal_rows] ==
              [('message', IDEA_PROMPT), ('answer', f'{QUESTION}：{CHOICE}'), ('message', RELEASE)] and
              not any(text in i['text'] for i in stored for text in (REQUEST_IDEATION, REQUEST_EXECUTOR, AFTER_RELEASE)), report['observed']['stored'])
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('记录页签', "!!document.querySelector('[data-records-tab]')", 20)
        electron.evaluate("document.querySelector('[data-records-tab]').click()")
        electron.until('记录表', f"document.querySelectorAll('.user-input-page tr[data-input-id]').length === {len(stored)}", 30)
        electron.screenshot(fixture.out / '05-records.png')
        listed = electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].map(r=>({id:r.dataset.inputId,text:r.innerText}))")
        report['observed']['records_rows'] = listed
        by_id = {row['id']: row['text'] for row in listed}
        marked = {row['id'] for row in electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].filter(r=>r.dataset.intervention&&r.querySelector('.record-intervention')).map(r=>({id:r.dataset.inputId}))")}
        typed = [i for i in stored if i['text'] == TYPED]
        answer = [i for i in stored if i['form'] == 'answer' and ANSWER in i['text']]
        check('three_kinds_in_one_view', len(typed) == 1 and len(answer) == 1 and typed[0]['id'] in marked and answer[0]['id'] in marked and
              not any(i['id'] in marked for i in terminal_rows) and all(i['id'] in by_id for i in typed + answer + terminal_rows) and
              not any('显式交付' in text for text in by_id.values()), dict(marked=sorted(marked), stored=report['observed']['stored']))
        check('records_page_shows_controller_prompt', all(i['id'] in by_id and '主控终端提交' in by_id[i['id']] and '构思主控' in by_id[i['id']] for i in terminal_rows), listed)

        # The hooks print nothing into the turn: the model never saw hook output and every prompt reached it.
        bodies = json.dumps([b['messages'] for b in fixture.api.bodies], ensure_ascii=False)
        check('hooks_do_not_touch_the_turn', IDEA_PROMPT in bodies and AFTER_RELEASE in bodies and 'UserPromptSubmit' not in bodies, None)
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api_snapshot'] = fixture.api.snapshot()
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
