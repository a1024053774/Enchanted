"""T-171：修订重派后，旧 attempt 名下仍未关闭的问题显示“可能已随修订失效”，不计入等你决定，由用户一键确认关闭。
真实后台、门禁、终端主控，真实 Claude Code worker（模型是本地脚本化接口），真实 Electron 窗口经 DevTools 协议操作。
期望值来自 T-171 ticket 与构思主控 answer 20261024T174012Z 之后的选 A（用户选“建票:标“已随修订失效”，由我一键确认关闭”）。

失败方式（先列再写）：
1. revise 作废 a1、重派 a2 后，a1 的 blocking 问题仍是“等你决定”，项目行与“问题”页签仍把它算进角标（N07 原样）。
2. 提示放得太宽：a2（未被修订作废）的 blocking 问题也被标成失效、不再计数。
3. 失效的问题被自动关闭或删除，而不是等用户确认。
4. 主控（终端身份）借“失效”关闭了 blocking 问题。
5. 一键确认后状态没变成已关闭，或没记成用户输入（form=action，channel=issue-panel，回指该问题）。
6. 一键确认的确认处看不到原问题全文。
--revision 在该版本源码上跑同一场景（修前应复现 1）；--mutant 跑已知坏实现。
"""
import argparse
import json
import re
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, gate_line, prompt_text, quote  # noqa: E402

OLD = ('验收读的是主仓库绝对路径', '完成条件里写的是主仓库的绝对路径，worktree 里的交付读不到；卡不改就交付不了，等你决定。')
NEW = ('需要确认 hello.txt 的内容', '新卡仍没写 hello.txt 的内容；不确定就不能交付，等你决定。')
MUTANTS = {
    # Every open issue of a revoked attempt, including a plain revoke, counts as superseded and is closed for the user.
    'auto-close': [('src/gates/core.ts', 'state: superseded ? "可能已随修订失效" : state,', 'state: superseded ? "已关闭" : state,')],
    # The hint ignores which attempt the issue belongs to.
    'any-attempt': [('src/gates/core.ts', 'if (revised.get(issue.attempt_id)) superseded', 'if (true) superseded')],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, real_model_turns=0,
                  checks=[], failed=[], observed={})
    attempts = []

    def plan(body):
        # Each worker session reports one blocking issue and ends its turn: the first under a1, the second under a2.
        text = prompt_text(body)
        assert '显式交付' in text, '只有 worker 会话'
        attempt = re.search(r'"attempt":\s*"([0-9a-f-]{36})"', text).group(1)
        if attempt not in attempts:
            attempts.append(attempt)
        title, issue_body = OLD if attempts.index(attempt) == 0 else NEW
        command = gate_line(body, f"'issue' '--task' '{{task}}' '--title' {quote(title)} '--body' {quote(issue_body)} '--blocking' 'true'")
        return 'worker', [('Bash', dict(command=command, description='blocking issue'))], '已上报阻塞问题，等你决定。'

    fixture = Fixture('t171-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def gate_issues():
        result = fixture.request('issues', fixture.operator, task='T-1')
        assert result['ok'], result
        return result

    def by_title(views, title):
        return next((view for view in views if view['issue']['title'] == title), None)

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("hello.txt").is_file() else 1)\n'})
        fixture.card('T-1', 'hello.txt', 'check.py')
        first = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert first.get('ok'), first
        old_attempt = first['attempt']['attempt_id']
        fixture.wait('a1 的问题进门禁', lambda: by_title(gate_issues()['issues'], OLD[0]), 180)
        fixture.wait('a1 回合结束', lambda: (lambda p: p.get('state') == 'idle' and p.get('writing') is False and not p.get('failed') and not p.get('active') and not p.get('queued'))(
            fixture.request('pane_status', fixture.operator, thread=first['attempt']['thread_id'])), 120)

        # The controller fixes the card: save v2, revise, reclaim a1, dispatch a2 (T-158 order).
        card = json.loads((fixture.out / 'T-1.json').read_text(encoding='utf-8'))
        card['goal'] = '在仓库根目录加 hello.txt（v2：完成条件用仓库内相对路径）'
        (fixture.out / 'T-1-v2.json').write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
        for command, data in [('card_save', dict(card=str(fixture.out / 'T-1-v2.json'), expected_version=1)),
                              ('revise', dict(spec_rev=2, card_version=2)), ('reclaim', dict(attempt=old_attempt))]:
            result = fixture.request(command, fixture.terminal, task='T-1', **data)
            assert result.get('ok'), (command, result)
        second = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert second.get('ok'), second
        new_attempt = second['attempt']['attempt_id']
        views = fixture.wait('a2 的问题进门禁', lambda: (lambda v: v if by_title(v, NEW[0]) else None)(gate_issues()['issues']), 180)
        old, new = by_title(views, OLD[0]), by_title(views, NEW[0])
        report['observed']['gate_before'] = {v['issue']['title']: dict(state=v['state'], attempt=v['issue']['attempt_id'],
                                             superseded=v.get('superseded_by_revision')) for v in views}
        check('old_issue_under_a1', old['issue']['attempt_id'] == old_attempt, old['issue']['attempt_id'])
        check('new_issue_under_a2', new['issue']['attempt_id'] == new_attempt, new['issue']['attempt_id'])
        # 1 and 3: the revised-away issue is marked, still open, not closed for the user.
        check('old_issue_marked_superseded', old['state'] == '可能已随修订失效' and
              (old.get('superseded_by_revision') or {}).get('attempt') == old_attempt, old['state'])
        # 2: the current attempt's blocking issue keeps waiting for the user.
        check('new_issue_still_waiting', new['state'] == '等你决定' and not new.get('superseded_by_revision'), new['state'])

        # 4: the controller cannot close the blocking issue, superseded or not.
        refused = fixture.request('disposition', fixture.terminal, task='T-1', issue=old['issue']['id'], action='close',
                                  reason='已随修订失效', basis='主控判断')
        report['observed']['controller_close'] = dict(ok=refused.get('ok'), error=refused.get('error'))
        check('controller_cannot_close_blocking', not refused.get('ok'), report['observed']['controller_close'])

        electron = Electron(fixture, 't171-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        badge = electron.until('项目行提示', "document.querySelector('[data-project-issues]')?.dataset.projectIssues ?? null", 30)
        tab = electron.evaluate("document.querySelector('[data-issues-tab] .tab-needs')?.textContent ?? null")
        report['observed']['badges'] = dict(project=badge, tab=tab)
        check('badges_count_only_current_issue', badge == '1' and tab == '1', report['observed']['badges'])
        electron.evaluate("document.querySelector('[data-issues-tab]').click()")
        electron.until('问题卡片', "document.querySelectorAll('.issue-card').length === 2")
        electron.screenshot(fixture.out / '01-superseded-shown.png')
        old_id = old['issue']['id']
        card_text = electron.evaluate(f"document.querySelector('[data-issue-id=\"{old_id}\"]')?.innerText ?? ''")
        report['observed']['old_card_text'] = card_text
        # 6: the full original report is on the card next to the confirm button.
        check('confirm_shows_full_issue', OLD[1] in card_text and '可能已随修订失效' in card_text and
              bool(electron.evaluate(f"!!document.querySelector('[data-confirm-superseded=\"{old_id}\"]')")), card_text[:300])
        check('current_issue_has_no_confirm', not electron.evaluate(
            f"!!document.querySelector('[data-confirm-superseded=\"{new['issue']['id']}\"]')"))

        # 5: one click closes it as the user's input.
        electron.evaluate(f"document.querySelector('[data-confirm-superseded=\"{old_id}\"]').click()")
        closed = fixture.wait('确认关闭进门禁', lambda: (lambda r: r if by_title(r['issues'], OLD[0])['state'] == '已关闭' else None)(gate_issues()), 30)
        disposition = by_title(closed['issues'], OLD[0]).get('disposition') or {}
        inputs = [i for i in closed.get('user_inputs', []) if i.get('reply_to') == old_id]
        report['observed']['disposition'] = dict(from_=disposition.get('from'), reason=disposition.get('reason'), basis=disposition.get('basis'))
        report['observed']['user_inputs'] = inputs
        check('closed_by_user', disposition.get('from') == 'user' and disposition.get('reason') == '已随修订失效', report['observed']['disposition'])
        check('recorded_as_user_input', len(inputs) == 1 and inputs[0]['form'] == 'action' and inputs[0]['channel'] == 'issue-panel', inputs)
        check('current_issue_untouched', by_title(closed['issues'], NEW[0])['state'] == '等你决定')
        electron.until('界面显示已关闭', f"document.querySelector('[data-issue-id=\"{old_id}\"]')?.dataset.issueState === '已关闭'", 20)
        electron.screenshot(fixture.out / '02-confirmed-closed.png')
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            report['out'] = str(fixture.out)
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
