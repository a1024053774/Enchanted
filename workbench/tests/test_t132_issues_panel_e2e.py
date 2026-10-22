"""T-132：面板里的问题上报。真实后台、门禁、终端主控，真实 Claude Code worker（模型是本地脚本化接口），
真实 Electron 窗口经 DevTools 协议操作。期望值来自 ticket 与门禁既有规则（问题状态、blocking 只有用户能关、
答复写进上报方会话并记为 answer 用户输入）。

失败方式（先列再写）：
1. 界面上没有问题列表，或者列出的状态与门禁 `issues` 读回不一致。
2. 项目行与“问题”页签不提示等你决定的问题。
3. 界面里的答复没有写进上报它的 worker 会话，或者没记为 `answer` 用户输入。
4. 关闭需要的原因、依据没传到门禁；关闭后记录被删除，而不是状态变为已关闭。
5. 读取失败时显示为空列表（“还没有问题上报”），用户以为没有问题；或者把已有卡片连同没发出的草稿一起卸掉（审查 01）。
6. 本来就没有问题的项目读取失败时，同时显示失败提示和“还没有问题上报”（审查 01；--empty-failure）。
--revision 在该版本的源码上跑同一场景（修前没有问题页）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote  # noqa: E402

ANSWER = '先按卡做，验收文件的问题我另开票。'
DRAFT = '这条我还没想好，先写一半'
SET_VALUE = ("var set=(el,v)=>{const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
             "Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['error-shown-as-empty', 'disposition-as-executor', 'cards-dropped-on-error', 'empty-shown-with-error'])
    parser.add_argument('--empty-failure', action='store_true', help='项目没有问题时断开后台')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, real_model_turns=0, checks=[])
    patches = {
        # A failed read clears the list instead of saying it failed.
        'error-shown-as-empty': [('app/IssuesPage.tsx', "(reason: unknown) => { if (mounted) setError('问题列表读取失败：' + String(reason)); }",
                                  "(reason: unknown) => { if (mounted) setTasks([]); }")],
        # The desktop's disposition recorded as the executor's, as before T-132: a blocking issue cannot be closed.
        'disposition-as-executor': [('src/daemon.ts', 'address: input.command === "disposition" ? "user" : "executor",', 'address: "executor",')],
        # Candidate 1: a failed read unmounted every card, and the drafts in them.
        'cards-dropped-on-error': [('app/IssuesPage.tsx', '    {rows.map(({ task, view })', '    {!error && rows.map(({ task, view })')],
        # Candidate 1: an empty project's failed read also said there were no reports.
        'empty-shown-with-error': [('app/IssuesPage.tsx', ': tasks !== null && !error && !rows.length ?', ': tasks !== null && !rows.length ?')],
    }.get(args.mutant, [])

    def plan(body):
        # The worker reports two issues (the second blocking), ends its turn, and acknowledges any answer.
        text = prompt_text(body)
        assert '显式交付' in text, '只有 worker 会话'
        issue = lambda title, issue_body, blocking: gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote(title)} '--body' {quote(issue_body)} '--blocking' '{blocking}'")
        return 'worker', [
            ('Bash', dict(command=issue('验收文件只查文件存在', 'check.py 只看 hello.txt 在不在，不看内容；建议加内容检查。', 'false'), description='issue 1')),
            ('Bash', dict(command=issue('需要确认 hello.txt 的内容', '卡里没写内容；不确定就不能交付，等你决定。', 'true'), description='issue 2')),
            ('Bash', dict(command=issue('README 没写怎么跑检查', '顺手记一下：README 里没写 check.py 怎么跑。', 'false'), description='issue 3')),
        ], '已上报三条问题，等待答复。'

    fixture = Fixture('t132-', plan, revision=args.revision, patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def gate_issues():
        result = fixture.request('issues', fixture.operator, task='T-1')
        assert result['ok'], result
        return result

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n'})
        if args.empty_failure:
            # 6: a project with no reports, then the daemon goes away.
            electron = Electron(fixture, 't132-' + fixture.dir.name[5:])
            electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
            electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
            electron.until('问题页签', "!!document.querySelector('[data-issues-tab]')", 20)
            electron.evaluate("document.querySelector('[data-issues-tab]').click()")
            electron.until('空列表', "document.querySelector('.issues-page')?.innerText.includes('还没有问题上报') ?? false", 30)
            fixture.stop()
            electron.until('读取失败提示', "document.querySelector('.issues-page [role=\"alert\"]')?.textContent.includes('问题列表读取失败') ?? false", 30)
            electron.screenshot(fixture.out / '04-empty-read-failed.png')
            empty = electron.evaluate("document.querySelector('.issues-page').innerText.includes('还没有问题上报')")
            check('empty_project_failure_is_not_no_reports', empty is False, empty)
            report['status'] = 'PASS'
            return
        fixture.card('T-1', 'hello.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        worker = dispatched['attempt']['runtime_identity']['launch']
        views = fixture.wait('三条问题进门禁', lambda: (lambda r: r['issues'] if len(r['issues']) == 3 else None)(gate_issues()), 180)
        report['gate_states_before'] = {view['issue']['title']: view['state'] for view in views}

        electron = Electron(fixture, 't132-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        # 2: one issue (the blocking one) waits for the user's decision from the start.
        badge = electron.until('项目行提示', "document.querySelector('[data-project-issues]')?.dataset.projectIssues ?? null", 30)
        tab = electron.evaluate("document.querySelector('[data-issues-tab] .tab-needs')?.textContent ?? null")
        report['badges'] = dict(project=badge, tab=tab)
        check('project_row_and_tab_show_waiting_issue', badge == '1' and tab == '1', report['badges'])

        # 1: the panel lists both reports with the gate's states.
        electron.evaluate("document.querySelector('[data-issues-tab]').click()")
        electron.until('问题卡片', "document.querySelectorAll('.issue-card').length === 3")
        electron.screenshot(fixture.out / '01-issues.png')
        cards = electron.evaluate("[...document.querySelectorAll('.issue-card')].map(c=>({id:c.dataset.issueId,state:c.dataset.issueState,"
                                  "blocking:!!c.dataset.issueBlocking,text:c.innerText}))")
        report['cards'] = cards
        by_id = {view['issue']['id']: view for view in views}
        check('panel_lists_reports_with_gate_states', sorted(card['id'] for card in cards) == sorted(by_id) and
              all(card['state'] == by_id[card['id']]['state'] and card['blocking'] == by_id[card['id']]['issue']['blocking'] and
                  by_id[card['id']]['issue']['title'] in card['text'] for card in cards), cards)
        plain = next(view for view in views if view['issue']['title'] == '验收文件只查文件存在')
        spare = next(view for view in views if view['issue']['title'] == 'README 没写怎么跑检查')
        blocking = next(view for view in views if view['issue']['blocking'])

        # 3: the answer typed in the panel reaches the reporting worker and is recorded as the user's answer.
        electron.evaluate(SET_VALUE + f"set(document.querySelector('[data-issue-id=\"{plain['issue']['id']}\"] textarea'),{json.dumps(ANSWER)});")
        electron.evaluate(f"[...document.querySelectorAll('[data-issue-id=\"{plain['issue']['id']}\"] button')].find(b=>b.textContent==='发送答复').click()")
        answered = fixture.wait('答复记入门禁', lambda: (lambda r: r if any(v['issue']['id'] == plain['issue']['id'] and v.get('answer') for v in r['issues']) else None)(gate_issues()), 60)
        delivered = fixture.wait('答复送到 worker', lambda: [b for b in fixture.api.bodies if b['key'] == 'worker' and
                                                         any(ANSWER in json.dumps(m, ensure_ascii=False) for m in b['messages'] if m['role'] == 'user')], 120)
        inputs = [dict(form=i['form'], text=i['text'], thread=i['target']['thread'], channel=i['channel']) for i in answered.get('user_inputs', [])]
        report['user_inputs'] = inputs
        thread = dispatched['attempt']['thread_id']
        check('answer_reaches_worker_and_is_user_answer', bool(delivered) and
              any(i['form'] == 'answer' and ANSWER in i['text'] and i['thread'] == thread for i in inputs), inputs)

        # 4: closing the blocking report needs a reason and a basis; the record stays, now closed.
        electron.evaluate(f"[...document.querySelectorAll('[data-issue-id=\"{blocking['issue']['id']}\"] button')].find(b=>b.textContent==='关闭…').click()")
        electron.evaluate(SET_VALUE + f"const c=document.querySelector('[data-issue-id=\"{blocking['issue']['id']}\"]');"
                          "const [r,b]=c.querySelectorAll('input');set(r,'内容已在答复里定了');set(b,'看过任务卡与上报正文');")
        electron.evaluate(f"[...document.querySelectorAll('[data-issue-id=\"{blocking['issue']['id']}\"] button')].find(b=>b.textContent==='确认关闭').click()")
        closed = fixture.wait('关闭记入门禁', lambda: (lambda r: r if any(v['issue']['id'] == blocking['issue']['id'] and v['state'] == '已关闭' for v in r['issues']) else None)(gate_issues()), 30)
        disposition = next(v for v in closed['issues'] if v['issue']['id'] == blocking['issue']['id'])['disposition']
        report['disposition'] = {key: disposition.get(key) for key in ('action', 'from', 'reason', 'basis')}
        electron.until('界面显示已关闭', f"document.querySelector('[data-issue-id=\"{blocking['issue']['id']}\"]')?.dataset.issueState === '已关闭'", 20)
        cleared = electron.until('提示随关闭消失', "!document.querySelector('[data-project-issues]') && !document.querySelector('[data-issues-tab] .tab-needs')", 20)
        electron.screenshot(fixture.out / '02-answered-and-closed.png')
        check('close_keeps_record_with_reason', cleared and len(closed['issues']) == 3 and disposition['action'] == 'close' and disposition['from'] == 'user' and
              disposition['reason'] == '内容已在答复里定了' and disposition['basis'] == '看过任务卡与上报正文', report['disposition'])

        # 5: with the daemon gone, the panel says the read failed instead of showing an empty list, and keeps the
        # cards with the draft the user has not sent yet.
        electron.evaluate(SET_VALUE + f"set(document.querySelector('[data-issue-id=\"{spare['issue']['id']}\"] textarea'),{json.dumps(DRAFT)});")
        fixture.stop()
        electron.until('读取失败提示', "document.querySelector('.issues-page [role=\"alert\"]')?.textContent.includes('问题列表读取失败') ?? false", 30)
        electron.screenshot(fixture.out / '03-read-failed.png')
        empty = electron.evaluate("document.querySelector('.issues-page')?.innerText.includes('还没有问题上报') ?? null")
        check('read_failure_is_not_an_empty_list', empty is False, empty)
        time.sleep(4)  # one more failed poll
        draft = electron.evaluate(f"document.querySelector('[data-issue-id=\"{spare['issue']['id']}\"] textarea')?.value ?? null")
        check('draft_survives_failed_read', draft == DRAFT, draft)
        report['worker_launch'] = worker
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
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
