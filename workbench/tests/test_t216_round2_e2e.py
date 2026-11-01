"""T-216 第二轮：真实后台/socket/门禁、两个项目、原生 Claude 交互终端、本地脚本化 API、Electron。

先列失败方式：
1. A 主控派发 B 任务时按 B 项目路由：B 主控在线则误投，B 无主控则排队而漏投 A。
2. 只在队列里登记一次，却在 CLI 内实际提交多次；用 API 历史请求重复计数也会误判。
3. 主控先答再关闭，界面仍显示历史答复者/动作，或为改处理人把历史答复隐藏/删除。

独立 oracle 来自本轮任务书；提交次数从 CLI 自己的 root user transcript 行逐条计数，
不去重、不按 dispatch_queued 或反复携带整段历史的 API 请求计数。
--source 可在保留的修前源码上跑完全相同场景；--duplicate-submit 是真实 CLI 重复提交反例，
在唯一一次队列投递完成后，经测试窗口再次提交同一正文，生产源码不变。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['routing-online', 'routing-offline', 'processor'], required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--duplicate-submit', action='store_true')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], real_supplier_calls=0)
    nonce = uuid.uuid4().hex[:10]
    title, body_text = '第二轮问题-' + nonce, '原文-' + nonce + '：只交给实际派发它的主控。'

    def plan(body):
        text = prompt_text(body)
        for name in ['A', 'B']:
            if 'T216_R2_CONTROLLER_' + name in text:
                return 'controller-' + name, [('Bash', dict(command='a2a request executor', description='request role'))], '主控 ' + name + ' 已就绪。'
        assert '显式交付' in text
        command = gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote(title)} '--body' {quote(body_text)} '--blocking' '{str(args.case == 'routing-online').lower()}'")
        return 'worker', [('Bash', dict(command=command, description='report issue'))], '问题已上报，等待答复。'

    fixture = Fixture('t216-r2-', plan, source=args.source)
    report['fixture'] = str(fixture.dir)
    electron = None
    controllers = {}

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        assert condition, f'{name}: {detail}'

    def events():
        return fixture.request('orchestration_events')['events']

    def start_controller(name, project, repo, launch=None, terminal=None):
        if launch is None:
            result = fixture.request('shell_start', fixture.operator, project=project, cwd=str(repo))
            assert result['ok'], result
            launch = result['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=project)
        assert window['ok'], window
        context = dict(name=name, launch=launch, window=window['identity'], sequence=0)

        def send(data):
            context['sequence'] += 1
            result = fixture.request('window_input', context['window'], sequence=context['sequence'], request_id=str(uuid.uuid4()), data=data)
            assert result['ok'], result
        context['send'] = send
        if terminal is None:
            token = fixture.out / ('token-' + name)
            send(f'print -r -- $A2A_TERMINAL_TOKEN > {quote(str(token))}\r')
            fixture.wait('终端令牌 ' + name, lambda: token.exists() and token.read_text(encoding='utf-8').strip(), 30)
            terminal = dict(kind='terminal', launch=launch, token=token.read_text(encoding='utf-8').strip())
        context['terminal'] = terminal
        command = ('claude --model claude-haiku-5-5 --effort low --permission-mode dontAsk --allowedTools Bash '
                   f'--session-id {uuid.uuid4()} T216_R2_CONTROLLER_{name}')
        send(command + '\r')
        pending = fixture.wait('主控申请 ' + name, lambda: fixture.request('sidebar_snapshot').get('role_requests'), 90)
        assert len(pending) == 1, pending
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        held = fixture.wait('主控身份 ' + name, lambda: (lambda r: r if r.get('role') == 'executor' else None)(fixture.request('terminal_whoami', terminal)), 30)
        context['role_request'] = held['role_requests'][-1]
        fixture.wait('主控空闲 ' + name, lambda: any(e['type'] == 'terminal_turn' and e['launch'] == launch and e['data']['state'] == 'idle' for e in events()), 45)
        controllers[name] = context
        return context

    def submissions(controller, issue_id):
        held = controller['role_request']
        paths = list((Path(held['native_home']) / 'projects').rglob(held['native_session'] + '.jsonl'))
        rows = []
        for path in paths:
            lines = path.read_text(encoding='utf-8').split('\n')
            for line in lines[:-1]:
                if not line:
                    continue
                entry = json.loads(line)
                content = entry.get('message', {}).get('content')
                if (entry.get('type') == 'user' and entry.get('isSidechain') is False and entry.get('sessionId') == held['native_session'] and
                        isinstance(content, str) and '\n收件箱 issue ' + issue_id + '\n' in content):
                    rows.append(dict(file=str(path), uuid=entry.get('uuid'), prompt_id=entry.get('promptId'), text=content))
        return rows

    def issues(task):
        result = fixture.request('issues', fixture.operator, task=task)
        assert result['ok'], result
        return result

    try:
        fixture.start(args.claude, {'README.md': 'A\n', 'check.py': 'raise SystemExit(0)\n'})
        fixture.card('T-1', 'hello.txt', 'check.py')
        other = fixture.dir / 'other'
        other.mkdir()
        for argv in [['git', 'init', '-q', '-b', 'main', str(other)]]:
            subprocess.run(argv, env=fixture.env, check=True)
        (other / 'check.py').write_text('raise SystemExit(0)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(other), 'add', '.'], env=fixture.env, check=True)
        subprocess.run(['git', '-C', str(other), 'commit', '-qm', 'fixture B'], env=fixture.env, check=True)
        assert fixture.request('project_open', fixture.operator, repo=str(other))['ok']
        config = fixture.home / '.claude.json'
        value = json.loads(config.read_text(encoding='utf-8'))
        value.update(hasSeenAutoDefaultNudge=True, projects={str(repo): {'hasTrustDialogAccepted': True} for repo in [fixture.repo, other]})
        config.write_text(json.dumps(value), encoding='utf-8')
        assert fixture.request('role_release', fixture.terminal)['ok']
        a = start_controller('A', 'demo', fixture.repo, fixture.terminal_launch, fixture.terminal)
        if args.case == 'routing-online':
            start_controller('B', 'other', other)

        task = 'demo+T-1' if args.case == 'processor' else 'other+T-1'
        if task.startswith('other+'):
            card = fixture.request('card_save', a['terminal'], project='other', task=task, card=str(fixture.out / 'T-1.json'), expected_version=0)
            assert card['ok'], card
            created = fixture.request('create', a['terminal'], project='other', task=task, repo=str(other), branch='refs/heads/main', card_version=1)
            assert created['ok'], created
        started = fixture.request('dispatch', a['terminal'], task=task, runtimeMode='workspace-write')
        assert started['ok'], started
        report['worker'] = started['attempt']
        view = fixture.wait('问题上报', lambda: (lambda r: r['issues'][0] if r['issues'] else None)(issues(task)), 150)
        issue_id = view['issue']['id']
        report['issue'] = view
        # Gather both positive/negative recipient observations before asserting: a wrong B delivery is also evidence.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not submissions(a, issue_id):
            assert not fixture.api.error, fixture.api.error
            time.sleep(.2)
        if submissions(a, issue_id):
            fixture.wait('主控完成收件回合', lambda: any(b['key'] == 'controller-A' and issue_id in json.dumps(b, ensure_ascii=False) for b in fixture.api.bodies), 30)
            time.sleep(2)
        received = {name: submissions(controller, issue_id) for name, controller in controllers.items()}
        inbox = fixture.request('inbox_list', fixture.operator, role='executor')
        receipt = next((row.get('delivery') for row in inbox.get('entries', []) if row['entry']['id'] == issue_id), None)
        report['routing'] = dict(submissions=received, delivery=receipt, controllers={name: dict(launch=c['launch'], role_request=c['role_request']) for name, c in controllers.items()})
        check('only_actual_dispatcher_receives', len(received['A']) >= 1 and not received.get('B') and receipt and receipt['state'] == 'delivered', report['routing'])
        check('original_issue_reaches_cli', title in received['A'][0]['text'] and body_text in received['A'][0]['text'], received['A'])
        if args.duplicate_submit:
            # Real extra CLI submission, while dispatch_queued remains one. This must fail the following count.
            fixture.wait('重复提交前空闲', lambda: (lambda rows: rows[-1]['data']['state'] == 'idle' if rows else False)([e for e in events() if e['type'] == 'terminal_turn' and e['launch'] == a['launch']]), 30)
            a['send']('\x1b[200~' + received['A'][0]['text'] + '\x1b[201~')
            a['send']('\r')
            fixture.wait('CLI 实际记录第二次提交', lambda: len(submissions(a, issue_id)) >= 2, 30)
        actual = submissions(a, issue_id)
        registrations = [e for e in events() if e['type'] == 'dispatch_queued' and e['data'].get('inbox_entry') == issue_id]
        check('cli_actual_submission_count_is_one', len(actual) == 1, dict(actual_submissions=actual, dispatch_queued_count=len(registrations)))

        if args.case == 'processor':
            answer = '保留的历史答复-' + nonce
            answered = fixture.request('answer_issue', a['terminal'], task=task, issue=issue_id, answer=answer)
            assert answered['ok'], answered
            fixture.wait('worker 实际收到答复', lambda: any(b['key'] == 'worker' and answer in json.dumps(b, ensure_ascii=False) for b in fixture.api.bodies), 90)
            closed = fixture.request('disposition', a['terminal'], task=task, issue=issue_id, action='close', reason='已完成核对', basis='本次上报和历史答复')
            assert closed['ok'], closed
            current = next(v for v in closed['issues'] if v['issue']['id'] == issue_id)
            check('close_keeps_answer_and_actor', current['state'] == '已关闭' and current['answer']['body'] == answer and current['disposition']['from'] == 'executor', current)
            electron = Electron(fixture, 't216-r2-' + uuid.uuid4().hex[:10])
            electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
            electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
            electron.until('问题页签', '!!document.querySelector("[data-issues-tab]")')
            electron.evaluate('document.querySelector("[data-issues-tab]").click()')
            selector = '[data-issue-id="' + issue_id + '"]'
            electron.until('已关闭的问题', f'document.querySelector({json.dumps(selector)})?.dataset.issueState === "已关闭"')
            processor = electron.evaluate(f'document.querySelector({json.dumps(selector + " [data-issue-processor]")}).textContent')
            text = electron.evaluate(f'document.querySelector({json.dumps(selector)}).innerText')
            electron.screenshot(fixture.out / 'answer-then-close.png')
            check('current_closer_shown_history_visible', processor == '主控已关（executor）' and answer in text, dict(processor=processor, text=text))
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['api'] = fixture.api.snapshot()
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
