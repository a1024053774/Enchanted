"""T-194：主控经 MCP 工具走通“申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成”，与经 a2a 命令的同一操作记录一致。真实后台、
socket、项目终端（zsh 与包装脚本），终端里跑真实 Claude Code（交互模式，Enchanted 插件挂上 a2a 的 MCP 服务器），模型换成
本地脚本化的 Messages 接口；worker 与审查员是后台按门禁启动的真实 Claude Code（同一脚本化接口）。

场景：用户在项目终端启动 claude。主控先不带身份调用 MCP 的 status 与 `a2a call` 的 status，再经 MCP 申请执行主控，用户批准；
之后同一回合里 T-1 全程经 MCP 工具（card_template → card_save → create → dispatch），T-2 全程经 `a2a call`；两张卡同形，只差
文件名。worker 交付后用户让它验收（T-1 经 MCP verify，T-2 经命令），审查通过后让它集成（integrate 带打分文件）。

失败方式（先列再写）：
1. 终端里的 Claude Code 看不到 Enchanted 的 MCP 工具（插件没挂上，或服务器起不来、拿不到终端身份）。
2. MCP 绕开身份：没有批准的角色也能调用主控命令，或拒绝码与 a2a 命令不同。
3. 经 MCP 申请的角色记错 CLI 或会话（会话号不是这次 Claude Code 自己的），钩子记录因此对不上；或者批准后没确认，身份不生效。
4. 经 MCP 的建卡、派发、验收、集成有一步走不通，或 worker 不归这个主控终端。
5. 两条入口的门禁记录不一致（事件序列、事件字段、worker 归属、打分记录）。
--revision 在该版本源码上跑（修前没有 MCP 服务器，应在第 1 条失败）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture, prompt_text  # noqa: E402

REQUEST = 'T-194：请申请执行主控'
DISPATCH = 'T-194：派 T-1 与 T-2'
VERIFY = 'T-194：两个都验收'
INTEGRATE = 'T-194：两个都集成'
FILES = {'T-1': 'a.txt', 'T-2': 'b.txt'}
# Not a defect: the MCP server starts 6 seconds late, so the controller's first requests see no Enchanted tools and its
# ToolSearch reports the server still connecting (as review 4 reproduced); the run must wait and then pass.
SLOW_MCP = [('src/terminalCli.ts', '    const cli = rest[0];\n', '    const cli = rest[0];\n    await new Promise(resolve => setTimeout(resolve, 6000));\n')]
MUTANTS = {
    # The role request does not carry the CLI's own session.
    'session-not-reported': [('src/terminalCli.ts', 'cli === "claude" ? process.env.CLAUDE_CODE_SESSION_ID : cli === "codex" ? meta?.threadId : undefined, signal));',
                              'undefined, signal));')],
    # The grant is never confirmed, so the role never takes effect.
    'grant-not-confirmed': [('src/terminalCli.ts', '    if (!answered.ok) return answered;\n', '    return answered;\n')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    parser.add_argument('--slow-mcp', action='store_true', help='MCP 服务器晚 6 秒启动，验证等待分支')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, slow_mcp=args.slow_mcp, checks=[], observed={})
    seen_tools = []
    paths = {}
    discovery = dict(waits=0)

    def plan(body):
        text = json.dumps(body['messages'], ensure_ascii=False)
        found = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False))
        cwd = found.group(1) if found else ''
        first = prompt_text(body)
        if '审查这一次交付' in first:
            shape = json.loads(first[first.rindex('{\n  "schema": 1'):])
            named = [task for task in FILES if f'demo+{task}' in first]
            assert len(named) == 1, f'审查提示里的任务不唯一：{named}'
            shape.update(verdict='可合并', findings=[], report={'结论': '夹具审查', '完成条件与变异检查': '夹具：删除目标文件后完成条件退出 1。'})
            return 'reviewer:' + named[0], [], json.dumps(shape, ensure_ascii=False)
        for task, name in FILES.items():
            if cwd.endswith(f'/{task}-a1'):
                submit = re.search(r'显式交付：\n(.+)\n', first).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
                return 'worker:' + task, [('Write', dict(file_path=f'{cwd}/{name}', content=f'{task}\n')),
                                          ('Bash', dict(command=f'git add {name}', description='stage')),
                                          ('Bash', dict(command=f'git commit -q -m "{task} fixture change"', description='commit')),
                                          ('Bash', dict(command=submit, description='submit'))], '已交付。'
        # The controller in the project terminal.
        assert REQUEST in text, first[:300]
        # Claude Code defers MCP tools: their names are listed in the conversation, loaded with ToolSearch before use.
        names = [tool.get('name', '') for tool in body.get('tools', [])] + re.findall(r'mcp__[A-Za-z0-9_-]+__[a-z_]+', text)
        seen_tools[:] = sorted(set(names))
        prefix = next((name[:-len('request_role')] for name in names if name.startswith('mcp__') and name.endswith('__request_role')), None)
        # Claude Code may still be connecting the plugin's server on the first requests (its tools not listed yet). ToolSearch
        # says so; it is asked again, a second apart, while it does, for at most 30 seconds (T-194 reviews 3 and 4). A server
        # that is not connecting and gives no tools is a missing entry.
        wait = ('ToolSearch', dict(query='+enchanted', max_results=10))
        waits = sum(1 for message in body['messages'] if message['role'] == 'assistant' and isinstance(message['content'], list)
                    for part in message['content'] if isinstance(part, dict) and part.get('type') == 'tool_use'
                    and part.get('name') == 'ToolSearch' and part.get('input', {}).get('query') == '+enchanted')
        last = next((message['content'] for message in reversed(body['messages']) if message['role'] == 'user'), None)
        connecting = 'still connecting' in json.dumps(last, ensure_ascii=False)
        if not prefix and (waits == 0 or connecting and waits < 30):
            if waits:
                time.sleep(1)
            return 'controller', [wait] * (waits + 1), '好的。'
        discovery['waits'] = waits
        assert prefix, f'主控没有 Enchanted 的 MCP 工具：{names}; 文中提到：{sorted(set(re.findall(r"mcp__[A-Za-z0-9_-]+", json.dumps(body, ensure_ascii=False))))[:20]}'

        def call(command, **data):
            return ('Bash', dict(command="a2a call '" + json.dumps(dict(command=command, **data), ensure_ascii=False) + "'", description=command))

        used = ('status', 'request_role', 'card_template', 'card_save', 'create', 'dispatch', 'verify', 'integrate')
        steps = [wait] * waits + [
                 ('ToolSearch', dict(query='select:' + ','.join(prefix + name for name in used), max_results=10)),
                 (prefix + 'status', dict(task='T-1')), call('status', task='T-2'), (prefix + 'request_role', dict(role='executor'))]
        if DISPATCH in text:
            steps += [(prefix + 'card_template', dict(task='T-1', repo=paths['repo'])),
                      (prefix + 'card_save', dict(task='T-1', project='demo', card=paths['T-1'], expected_version=0)),
                      (prefix + 'create', dict(task='T-1', project='demo', repo=paths['repo'], card_version=1, branch='refs/heads/main')),
                      (prefix + 'dispatch', dict(task='T-1', runtimeMode='workspace-write', model='claude-haiku-5-5', effort='low')),
                      call('card_template', task='T-2', repo=paths['repo']),
                      call('card_save', task='T-2', project='demo', card=paths['T-2'], expected_version=0),
                      call('create', task='T-2', project='demo', repo=paths['repo'], card_version=1, branch='refs/heads/main'),
                      call('dispatch', task='T-2', runtimeMode='workspace-write', model='claude-haiku-5-5', effort='low')]
        if VERIFY in text:
            steps += [(prefix + 'verify', dict(task='T-1')), call('verify', task='T-2')]
        if INTEGRATE in text:
            steps += [(prefix + 'integrate', dict(task='T-1', score_file=paths['score'])), call('integrate', task='T-2', score_file=paths['score'])]
        return 'controller', steps, '好的。'

    fixture = Fixture('t194-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []) + (SLOW_MCP if args.slow_mcp else []))
    report['fixture'] = str(fixture.dir)

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def screen(term):
        raw = (fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def submit(term, text):
        type_in(term, text)
        time.sleep(1)
        type_in(term, '\r')

    def results():
        return fixture.api.results.get('controller', [])

    def state_of(task):
        # Before the controller's create the task does not exist yet.
        return fixture.request('status', fixture.operator, task=task).get('task') or {}

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', **{f'check_{task}.py': f'import pathlib, sys\nsys.exit(0 if pathlib.Path("{name}").is_file() else 1)\n'
                                                              for task, name in FILES.items()}})
        # The fixture's own socket-only executor gives its role back, so the user's CLI can ask for it.
        assert fixture.request('role_release', fixture.terminal)['ok']
        paths['repo'] = str(fixture.repo)
        for task, name in FILES.items():
            path = fixture.out / f'{task}.json'
            path.write_text(json.dumps(dict(id=task, source=None, goal=f'在仓库根目录加 {name}', non_goals=['不改别的文件'],
                paths=dict(allow=[name], deny=[]), oracle_paths=[f'check_{task}.py'], completion_conditions=[dict(argv=['python3', f'check_{task}.py'])],
                red_commands=[], task_type='测试', repair_target=None, complexity='S',
                executor=dict(cli='Claude Code', model='claude-haiku-5-5', effort='low'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
            paths[task] = str(path)
        score = fixture.out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只改了卡内文件',
            engineering_taste=2, engineering_reason='夹具', notes='T-194 fixture'), ensure_ascii=False), encoding='utf-8')
        paths['score'] = str(score)
        # The fixture user trusts the project in their own Claude and allows the a2a commands and Enchanted's MCP tools.
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        (fixture.home / '.claude').mkdir(exist_ok=True)
        (fixture.home / '.claude/settings.json').write_text(json.dumps({'permissions': {'allow': [
            'Bash(a2a call:*)', 'mcp__plugin_enchanted-a2a_enchanted']}}), encoding='utf-8')

        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        term = dict(launch=launch, identity=window['identity'], sequence=0)
        type_in(term, 'claude --model claude-haiku-5-5\r')
        fixture.wait('Claude 启动', lambda: (lambda text: 'ClaudeCodev' in text and '❯' in text[text.index('ClaudeCodev'):])(screen(term))
                     if 'ClaudeCodev' in screen(term) else False, 60)
        submit(term, REQUEST)

        # 1, 3: the role request comes through MCP; the user approves it.
        pending = fixture.wait('经 MCP 的角色申请出现', lambda: [row for row in fixture.request('sidebar_snapshot').get('role_requests', [])
                                                               if row.get('launch') == launch], 60)
        report['observed']['mcp_tools'] = sorted(name for name in seen_tools if name.startswith('mcp__'))
        check('mcp_tools_in_controller', all(any(name.endswith('__' + tool) for name in seen_tools)
                                             for tool in ('request_role', 'card_save', 'create', 'dispatch', 'verify', 'integrate', 'status')),
              report['observed']['mcp_tools'])
        # The controller's tool results: the discovery searches, the select search, then the calls in order.
        at = discovery['waits'] + 1
        report['observed']['discovery_waits'] = discovery['waits']
        if args.slow_mcp:
            check('waited_for_slow_server', discovery['waits'] >= 1, discovery)
        before = results()[at:at + 2]
        report['observed']['without_role'] = before
        refused = [json.loads(re.search(r'\{.*\}', item['text'], re.S).group(0)) for item in before]
        check('mcp_refused_like_command_without_role', len(refused) == 2 and refused[0].get('ok') is False and
              refused[0].get('error') == refused[1].get('error') and refused[0].get('error'), before)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        fixture.wait('申请工具返回', lambda: len(results()) >= at + 3, 60)
        report['observed']['role_result'] = results()[at + 2:at + 3]
        confirmed = [json.loads(row['data']) for row in database("SELECT data FROM orchestration_events WHERE type='role_request_confirmed' AND launch=?", launch)]
        check('mcp_role_takes_effect', not results()[at + 2]['is_error'] and [row['role_request'] for row in confirmed] == [pending[0]['id']],
              dict(result=results()[at + 2:at + 3], confirmed=confirmed))
        requested = json.loads(database("SELECT data FROM orchestration_events WHERE type='role_requested' AND launch=?", launch)[0]['data'])
        sessions = [path.stem for path in (fixture.home / '.claude/projects').glob('*/*.jsonl') if REQUEST in path.read_text(encoding='utf-8')]
        report['observed']['role_request'] = {key: requested.get(key) for key in ('cli', 'native_session', 'state')}
        report['observed']['claude_sessions'] = sessions
        check('mcp_role_carries_cli_and_session', requested.get('cli') == 'claude' and len(sessions) == 1 and
              requested.get('native_session') == sessions[0], dict(requested=report['observed']['role_request'], sessions=sessions))

        # 4: one turn: T-1 through MCP tools, T-2 through a2a commands.
        submit(term, DISPATCH)
        for task in FILES:
            fixture.wait(f'{task} 交付', lambda task=task: state_of(task).get('state') == 'submitted', 240)
        submit(term, VERIFY)
        for task in FILES:
            fixture.wait(f'{task} 审查通过', lambda task=task: state_of(task).get('state') == 'verified', 300)
        submit(term, INTEGRATE)
        for task in FILES:
            fixture.wait(f'{task} 集成', lambda task=task: state_of(task).get('state') == 'accepted', 120)
        controller = results()
        report['observed']['controller_results'] = [dict(is_error=item['is_error'], text=item['text'][:300]) for item in controller]
        main_files = fixture.git('ls-tree', '-r', '--name-only', 'refs/heads/main').split()
        check('full_flow_through_mcp', state_of('T-1')['state'] == 'accepted' and 'a.txt' in main_files and
              not any(item['is_error'] for item in controller[at + 2:]), dict(main=main_files, results=report['observed']['controller_results']))

        # 5: the two entries leave the same gate records: every record of the task in the same order and number, the same fields,
        # and the same values where the values do not name the task, attempt or time. Integration differs on purpose: the task
        # integrated second finds the work branch moved and is checked again, from integration_compare_failed through
        # review_reused, whichever entry it came from; that one run of records is set aside (T-194 review 4, R4-F3).
        recheck = ('integration_compare_failed', 'review_reused')
        root = str(fixture.dir)
        uuid_form = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
        commit_form = re.compile(r'\b[0-9a-f]{40}\b')
        time_form = re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z')
        # Measured, not decided: how long things took.
        measured = {'elapsed_seconds', 'elapsed_ms', 'duration_ms'}

        def body(rows):
            return [row for row in rows if row['type'] not in ('command_intent', 'command_result')]

        def details(row):
            return row.get('details') or {}

        def verification_chain(rows):
            # The first verification of the task: verification_intent through verification_worktree_removed.
            kinds = [row['type'] for row in rows]
            begin = kinds.index('verification_intent')
            return rows[begin:kinds.index('verification_worktree_removed', begin) + 1]

        # What a second run of the verification chain changes by being the second; only for comparing it with the first.
        again = {'ordinal', 'revalidation', 'review', 'ref'}

        def masked(value):
            value = time_form.sub('<time>', commit_form.sub('<commit>', uuid_form.sub('<id>', value)))
            return re.sub(r'-verify-\d+(?=/|$)', '-verify-<n>', value)  # the verification workspace carries the run's ordinal

        def leaves(first, second, ignore, pairs):
            # Walks two records side by side; False if their shapes or non-string values differ; collects strings that
            # differ only in their ids, commits, times and verification workspace ordinal. Any other text must match (T-194 review 7, R7-F1).
            if isinstance(first, dict) and isinstance(second, dict):
                keys = [key for key in first if key not in ignore]
                return sorted(keys) == sorted(key for key in second if key not in ignore) and all(
                    leaves(first[key], second[key], ignore, pairs) for key in keys)
            if isinstance(first, list) and isinstance(second, list):
                return len(first) == len(second) and all(leaves(a, b, ignore, pairs) for a, b in zip(first, second))
            if isinstance(first, str) and isinstance(second, str):
                if first == second:
                    return True
                pairs.append((second, first))
                return masked(first) == masked(second)
            return first == second

        def recheck_of(rows):
            # The re-check the gate runs when the work branch moved before this task's integration (T-194 reviews 5 and 6):
            # integration_compare_failed on the first miss, naming the task's attempt, candidate and verification; one more run
            # of the task's verification chain, the same record by record but for what being the second run changes, ending
            # passed; review_reused carrying the task's review unchanged, the task verified, bound to the re-run. Returns
            # (start, stop, aliases from the re-run's ids, commits and paths to the first run's, the re-run's revalidation), or
            # None when the records are anything else.
            kinds = [row['type'] for row in rows]
            if kinds.count(recheck[0]) != 1 or kinds.count(recheck[1]) != 1 or kinds.index(recheck[1]) < kinds.index(recheck[0]):
                return None
            start, stop = kinds.index(recheck[0]), kinds.index(recheck[1])
            first, inner = verification_chain(rows[:start]), rows[start + 1:stop]
            if [row['type'] for row in inner] != [row['type'] for row in first]:
                return None
            pairs = []
            if not all(leaves(details(a), details(b), again, pairs) for a, b in zip(first, inner)):
                return None
            aliases = dict(pairs)
            if len(aliases) != len(set(pairs)) or len(set(aliases.values())) != len(aliases):
                return None  # one value of the re-run standing for two of the first run, or two for one
            attempt = details(next(row for row in rows[:start] if row['type'] == 'submitted'))['attempt']
            reviewed = details(next(row for row in rows[:start] if row['type'] == 'review_result'))['review']
            first_result = details(first[-3])['verification'] if first[-3]['type'] == 'verification_result' else None
            result = next((details(row)['verification'] for row in inner if row['type'] == 'verification_result'), None)
            missed, reused = details(rows[start]), details(rows[stop])
            binding = missed.get('review_reuse_binding') or {}
            if not (first_result and result and result.get('state') == 'passed' and missed.get('misses') == 1 and
                    missed.get('verification_id') == first_result['verification_id'] and
                    missed.get('candidate') == reviewed.get('candidate_commit') == binding.get('candidate_commit') and
                    all(str(binding.get(key)) == str(attempt.get(key)) for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'card_snapshot_id')) and
                    reused.get('review') == reviewed and (reused.get('task') or {}).get('state') == 'verified' and
                    reused.get('verification_id') == result['verification_id'] and
                    reused.get('G') == result.get('G') and reused.get('M') == result.get('M')):
                return None
            revalidation = details(inner[0]).get('attempt', {}).get('revalidation')
            return start, stop, aliases, revalidation

        def after_recheck(value, aliases, ordinals, revalidation):
            # A record after the re-check as it reads against the first run: the re-run's values back to the first run's, the
            # verification's ordinal with them, and the revalidation the re-check recorded set aside (only that one).
            if isinstance(value, dict):
                out = {}
                for key, item in value.items():
                    if key == 'revalidation' and item == revalidation:
                        continue
                    out[key] = after_recheck(item, aliases, ordinals, revalidation)
                if value.get('verification_id') in aliases and value.get('ordinal') in ordinals:
                    out['ordinal'] = ordinals[value['ordinal']]
                return out
            if isinstance(value, list):
                return [after_recheck(item, aliases, ordinals, revalidation) for item in value]
            if isinstance(value, str):
                value = aliases.get(value, value)
                # Ids and commits inside a longer text (a ref update, a command line) read as the first run's too.
                for form in (uuid_form, commit_form):
                    value = form.sub(lambda match: aliases.get(match.group(0), match.group(0)), value)
                return value
            return value

        def own(rows):
            # The task's records, the controller command's own left out; the re-check, if it is exactly that, set aside.
            rows = body(rows)
            found = recheck_of(rows)
            if not found:
                return rows
            start, stop, aliases, revalidation = found
            first = details(verification_chain(rows[:start])[0])
            again_ordinal = details(rows[start + 1]).get('ordinal')
            ordinals = {again_ordinal: first.get('ordinal')}
            tail = [dict(row, details=after_recheck(details(row), aliases, ordinals, revalidation)) for row in rows[stop + 1:]]
            return rows[:start] + tail

        def sequence(rows):
            return [row['type'] for row in own(rows)]

        def canonical(values, task):
            # The values as they read for any task: ids, commits and process ids numbered in order of first use within the
            # task (so a record pointing at another attempt, commit or process than the task's own reads differently), times
            # set aside, the fixture root, the task's name and its own file named; refs of the other task in shared_refs left
            # out. Anything else, the other task's file or a path outside the fixture, stays as it is.
            other = next(name for name in FILES if name != task)
            numbers = {}

            def number(kind, raw):
                return numbers.setdefault((kind, raw), f'<{kind}{sum(1 for key in numbers if key[0] == kind) + 1}>')

            def text(value):
                value = time_form.sub('<time>', value).replace(root, '<root>')
                value = uuid_form.sub(lambda match: number('id', match.group(0)), value)
                value = commit_form.sub(lambda match: number('commit', match.group(0)), value)
                value = re.sub(rf'(?<![A-Za-z0-9-]){re.escape(task)}(?![0-9A-Za-z])', '<task>', value)
                return re.sub(rf'(?<![\w.]){re.escape(FILES[task])}(?![\w])', '<file>', value)

            def walk(value, key=None):
                if isinstance(value, dict):
                    return {name: walk(item, name) for name, item in value.items() if name not in measured}
                if isinstance(value, list):
                    return [walk(item) for item in value]
                if key in ('shell_pid', 'leader_pid', 'pid'):
                    return number('pid', value)
                if isinstance(value, str):
                    if key == 'shared_refs':
                        value = '\n'.join(line for line in value.split('\n') if f'+{other}/' not in line and f'/{other}-' not in line)
                    return text(value)
                return value
            return [walk(value) for value in values]

        def differences(first, second):
            left, right = own(first), own(second)
            if [row['type'] for row in left] != [row['type'] for row in right]:
                return [('sequence', [row['type'] for row in left], [row['type'] for row in right])]
            task_of = lambda rows: next(row['details']['task_id'].split('+')[1] for row in rows if isinstance(details(row).get('task_id'), str))
            a = canonical([details(row) for row in left], task_of(left))
            b = canonical([details(row) for row in right], task_of(right))
            return [(row['type'], x, y) for row, x, y in zip(left, a, b) if x != y]

        def same_records(first, second):
            return not differences(first, second)

        def same_scores(first, second, first_rows, second_rows):
            # The whole score record, facts included, read in its task's numbering (it names the task's attempt and launch).
            if not (len(first) == len(second) == 1 and first[0].get('data')):
                return False
            task_of = lambda score: score['task'].split('+')[1]
            a = canonical([details(row) for row in own(first_rows)] + [first[0]], task_of(first[0]))[-1]
            b = canonical([details(row) for row in own(second_rows)] + [second[0]], task_of(second[0]))[-1]
            return a == b

        events = {task: fixture.request('events', fixture.operator, task='demo+' + task)['events'] for task in FILES}
        report['observed']['event_types'] = {task: [row['type'] for row in rows if row['type'] not in ('command_intent', 'command_result')]
                                              for task, rows in events.items()}
        report['observed']['sequences'] = {task: sequence(rows) for task, rows in events.items()}
        check('same_gate_events', all(kind in report['observed']['sequences']['T-1'] for kind in
                                      ('card_saved', 'created', 'dispatched', 'verification_intent', 'review_requested', 'integrated', 'score_recorded'))
              and same_records(events['T-1'], events['T-2']), dict(sequences=report['observed']['sequences'],
                                                                     differences=differences(events['T-1'], events['T-2'])[:5]))
        parents = {task: sorted({json.loads(row['data']).get('parent_launch') for row in database("SELECT data FROM launch_records WHERE task=?", 'demo+' + task)})
                   for task in FILES}
        report['observed']['parents'] = parents
        # The worker, and its reviewer, started by this controller's calls (their launches name its terminal).
        check('workers_belong_to_controller', all(value == [launch] for value in parents.values()), parents)
        scores = {task: [json.loads(row['details']) for row in database("SELECT details FROM events WHERE task=? AND type='score_recorded'", 'demo+' + task)]
                  for task in FILES}
        report['observed']['scores'] = scores
        check('same_score_record', same_scores(scores['T-1'], scores['T-2'], events['T-1'], events['T-2']), scores)
        # The two comparisons above must refuse records that differ (reviews 4 and 5's counterexamples), each built from these
        # records by changing one thing the gate decided.
        def edited(rows, kind, path, value, occurrence=0):
            rows = json.loads(json.dumps(rows))
            target = [row for row in rows if row['type'] == kind][occurrence]['details']
            for key in path[:-1]:
                target = target[key]
            assert path[-1] in target, f'反例的字段不在记录里：{kind} {path}'
            target[path[-1]] = value(target[path[-1]]) if callable(value) else value
            return rows
        recheck_task = next(task for task, rows in events.items() if any(row['type'] == recheck[0] for row in rows))
        other_task = next(task for task in events if task != recheck_task)
        base_rows = events[recheck_task]
        kinds = [row['type'] for row in base_rows]
        begin, stop = kinds.index(recheck[0]), kinds.index(recheck[1])
        dispatched = next(row for row in base_rows if row['type'] == 'dispatched')
        def score_with(change):
            changed = json.loads(json.dumps(scores[recheck_task]))
            change(changed[0])
            return same_scores(scores[other_task], changed, events[other_task], base_rows)
        doubled = list(base_rows)
        doubled.insert(kinds.index('dispatched'), dispatched)
        compare = lambda rows: same_records(events[other_task], rows)
        unrelated = '11111111-1111-4111-8111-111111111111'
        refusals = dict(
            changed_score=score_with(lambda score: score['data'].update(boundary_discipline=1)),
            score_facts=score_with(lambda score: score['facts'].update(human_interventions=9)),
            score_attempt=score_with(lambda score: score.update(attempt=unrelated)),
            reversed=compare(list(reversed(base_rows))),
            repeated_dispatch=compare(doubled),
            dispatch_inside_recheck=compare(base_rows[:begin + 1] + [dispatched] + base_rows[begin + 1:]),
            empty_recheck=compare(base_rows[:begin + 1] + base_rows[stop:]),
            completion_failed=compare(edited(base_rows, 'completion_check', ['passed'], False)),
            completion_exit=compare(edited(base_rows, 'completion_check', ['result', 'exit'], 1)),
            verification_failed=compare(edited(base_rows, 'verification_result', ['verification', 'state'], 'failed')),
            review_verdict=compare(edited(base_rows, 'review_result', ['review', 'result', 'verdict'], '需修改')),
            runtime_mode=compare(edited(base_rows, 'dispatched', ['attempt', 'runtime_mode'], 'read-only')),
            unrelated_workspace=compare(edited(base_rows, 'completion_check', ['result', 'cwd'], '/private/tmp/unrelated-repo')),
            recheck_unrelated_workspace=compare(edited(base_rows, 'completion_check', ['result', 'cwd'], '/private/tmp/unrelated-repo', 1)),
            # A text that appears once in the re-run, so swapping it keeps the alias map one-to-one (review 7, R7-F1).
            recheck_other_check=compare(edited(base_rows, 'completion_check', ['result', 'argv'], lambda argv: argv[:-1] + ['check_other.py'], 1)),
            trailer_other_attempt=compare(edited(base_rows, 'trailer_check', ['trailers', 'attempt'], [unrelated])),
            other_task_file=compare(edited(base_rows, 'path_check', ['paths'], [FILES[other_task]])),
            integrated_other_candidate=compare(edited(base_rows, 'integrated', ['intent', 'C'], '1' * 40)),
            recheck_fourth_miss=compare(edited(base_rows, 'integration_compare_failed', ['misses'], 4)),
            recheck_binding_fence=compare(edited(base_rows, 'integration_compare_failed', ['review_reuse_binding', 'fence'], 999)),
            reused_review_failed=compare(edited(base_rows, 'review_reused', ['review', 'state'], 'needs_fix')),
            reused_review_verdict=compare(edited(base_rows, 'review_reused', ['review', 'result', 'verdict'], '需修改')),
            reused_task_paused=compare(edited(base_rows, 'review_reused', ['task', 'state'], 'paused')),
            revalidation_misses=compare(edited(base_rows, 'integrated', ['intent', 'attempt', 'revalidation', 'misses'], 9)),
            own_ref_missing=compare(edited(base_rows, 'review_result', ['review', 'shared_refs'],
                                           lambda refs: '\n'.join(line for line in refs.split('\n') if f'+{recheck_task}/' not in line))))
        report['observed']['refusals'] = refusals
        check('comparisons_refuse_different_records', not any(refusals.values()), refusals)
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api'] = fixture.api.snapshot()
        raise
    finally:
        try:
            fixture.stop()
        finally:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
