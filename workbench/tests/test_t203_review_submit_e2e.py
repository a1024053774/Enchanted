"""T-203：审查员按字段提交结论，不再靠模型手写 14 个字段的嵌套 JSON；同一 attempt 的多张问题卡编号不重复。
真实后台与门禁，worker 与审查员都是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。

预期来自需求（T-203 与第 2 轮试用发现 1）：
- 审查员的同一份意见（可合并、无问题、一份报告）：修前只能写成最后一条回复里的 JSON，试用里少一个 `}` 就被拒收、任务暂停；
  修后经 review_submit 工具只填 verdict、findings、report，门禁收下，任务验收通过。
- 格式真不对时仍拒收并说明：工具对不合格的字段当场拒绝并指出字段；结束回合时没有成功提交的结论，审查暂停并留下原因。
- 同一 attempt 的两次审查失败，问题卡编号不同（试用里两张都是“问题 1”）。

场景：同一次交付连开三次审查（第 2、3 次经“为同一次交付新开审查”）。
1. 第一次：调用工具时 verdict 写成“通过”，被拒后就结束回合（工具不存在的修前版本：最后一条回复写 JSON 且少一个 `}`）。
2. 第二次：不调用工具，只在最后一条回复写少一个 `}` 的 JSON。
3. 第三次：先交一次缺 location.line 的问题清单被拒，再交正确的意见（修前同 2）。

失败方式（先列再写）：
1. 少括号的回包仍让审查卡死（修前）。
2. 工具不校验，坏字段先被收下，到回合结束才失败。
3. 门禁回合结束时仍读最后一条回复，不读工具交的结论。
4. 问题编号仍按会话计数，两张卡同号。
5. 修法放宽了检查：坏 verdict 或缺字段的结论被收下。
--revision 在该版本源码上跑同一场景；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import traceback

from scripted_claude import Fixture, prompt_text, quote, working_directory

TOOL = 'mcp__enchanted__review_submit'
OPINION = dict(verdict='可合并', findings=[], report={
    '结论说明': '候选只加了 answer.txt，内容与任务卡一致。',
    '完成条件与变异检查': '脚本化夹具：不声称做过真实变异检查。'})
MUTANTS = {
    'per-thread-number': [('src/gates/core.ts', '    const row = attempt\n', '    const row = false\n')],
    'tool-skips-check': [('src/reviewResult.ts', '  reviewRequest(JSON.stringify(envelope));\n', '')],
    'stop-reads-last-message': [('src/daemon.ts', 'readReviewResult(pane.record.request_dir)', 'stop.last_assistant_message')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real daemon/gate/Claude Code; scripted Messages API; zero vendor model calls', checks=[])
    fixture = None
    reviews = []  # candidate workspaces, in the order the reviews started

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def broken_last_message(text):
        # The only channel before the fix: the whole envelope as the last reply, here missing its final brace (UAT-02).
        shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
        shape.update(OPINION)
        return json.dumps(shape, ensure_ascii=False)[:-1]

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            cwd = working_directory(body)
            if cwd not in reviews:
                reviews.append(cwd)
            n = reviews.index(cwd) + 1
            key = f'review-{n}'
            # A reviewer reads the candidate first (Claude Code connects MCP servers while the session runs, so the first
            # request may come before the tool is listed); what it does next follows the tools it then sees.
            lead = [('Bash', dict(command='ls -la', description='read the candidate copy'))]
            step = sum(1 for m in body['messages'] if m['role'] == 'assistant' and isinstance(m['content'], list)
                       and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in m['content']))
            tools = {tool.get('name') for tool in body.get('tools', [])}
            # Claude Code defers MCP tools behind ToolSearch and lists them by name; a real model loads one before calling it.
            deferred = TOOL not in tools and 'ToolSearch' in tools and TOOL in json.dumps(body, ensure_ascii=False)
            seen = report.setdefault('review_tools', {}).setdefault(key, dict(available=False, deferred=False))
            if step == 1:
                seen.update(available=TOOL in tools or deferred, deferred=deferred)
            load = [('ToolSearch', dict(query='select:' + TOOL, max_results=1))] if seen['deferred'] else []
            if step == 0:
                return key, lead, ''
            if not seen['available'] or n == 2:
                return key, lead, broken_last_message(text) if '"schema": 1' in text else '{"verdict": "可合并"'
            if n == 1:
                return key, lead + load + [(TOOL, {**OPINION, 'verdict': '通过'})], '格式被拒，结束本回合。'
            bad = {**OPINION, 'verdict': '需修复', 'findings': [dict(location=dict(path='answer.txt'),
                   failure_scenario='示例', suggestion='示例')]}
            return key, lead + load + [(TOOL, bad), (TOOL, OPINION)], '已提交审查结论。'
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Write', dict(file_path=f'{cwd}/answer.txt', content='accepted')),
                          ('Bash', dict(command='git add answer.txt', description='stage')),
                          ('Bash', dict(command='git commit -q -m ' + quote('T203 fixture candidate'), description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    try:
        fixture = Fixture('t203-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-203 fixture\n', 'check.py':
            'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'})
        fixture.card('T-1', 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        status = lambda: fixture.request('status', fixture.operator, task='demo+T-1')['task']
        events = lambda: fixture.request('events', fixture.operator, task='demo+T-1')['events']
        fixture.wait('交付', lambda: status()['state'] == 'submitted', 180)
        assert fixture.request('verify', fixture.terminal, task='T-1').get('ok')

        def settled(previous=None):
            return fixture.wait('审查结束', lambda: (lambda t: t if t['state'] in ('paused', 'verified') and
                                t['review']['review_id'] != previous else None)(status()), 240)

        outcomes = []
        task = settled()
        for n in (1, 2, 3):
            failure = next((e['details']['details'] for e in reversed(events()) if e['type'] == 'review_protocol_failed' and
                            e['details']['review']['review_id'] == task['review']['review_id']), None)
            outcomes.append(dict(review=n, state=task['state'], review_state=task['review']['state'],
                                 error=failure and (failure.get('error') or failure.get('receipt', {}).get('result', {}).get('error'))))
            if n == 3 or task['state'] != 'paused':
                break
            restarted = fixture.request('verify', fixture.terminal, task='T-1', attempt=task['current_attempt']['attempt_id'],
                                        review_id=task['review']['review_id'])
            assert restarted.get('ok'), restarted
            task = settled(task['review']['review_id'])
        report['outcomes'] = outcomes
        report['tool_results'] = {key: value for key, value in fixture.api.snapshot()['results'].items() if key.startswith('review-')}

        # The tool's own results, after the read and any ToolSearch load.
        calls = lambda key: fixture.api.snapshot()['results'].get(key, [])[1 + (1 if report.get('review_tools', {}).get(key, {}).get('deferred') else 0):]
        first = calls('review-1')
        check('bad_verdict_refused_at_once', len(first) == 1 and first[0]['is_error'] and 'verdict' in first[0]['text'], first)
        check('refusal_says_how_to_fix', bool(first) and '可合并' in first[0]['text'] and '需修复' in first[0]['text'], first)
        check('review_1_paused_without_result', outcomes[0]['state'] == 'paused' and outcomes[0]['error'] == 'review_result_missing', outcomes[0])
        check('broken_last_message_still_refused', len(outcomes) > 1 and outcomes[1]['state'] == 'paused' and
              outcomes[1]['error'] == 'review_result_missing', outcomes[1:2])
        third = calls('review-3')
        check('missing_line_refused_at_once', len(third) == 2 and third[0]['is_error'] and 'line' in third[0]['text'], third)
        final = status()
        report['final'] = dict(state=final['state'], review=final.get('review'))
        check('same_opinion_accepted', final['state'] == 'verified' and final['review']['state'] == 'passed' and
              final['review'].get('result', {}).get('verdict') == '可合并' and
              final['review'].get('result', {}).get('report') == OPINION['report'], report['final'])
        attempt = final['current_attempt']['attempt_id']
        cards = [v['issue'] for v in fixture.request('issues', fixture.operator, task='T-1')['issues']
                 if v['issue'].get('attempt_id') == attempt]
        report['issue_cards'] = [dict(number=c['number'], title=c['title'], thread=c['thread_id']) for c in cards]
        numbers = [c['number'] for c in cards]
        check('two_failures_two_cards', len(cards) == 2, report['issue_cards'])
        check('issue_numbers_distinct', len(numbers) == len(set(numbers)), numbers)
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        if fixture:
            # What each review conversation ended with, for the record: every tool call and its result.
            report['review_messages'] = {body['key']: [dict(role=m['role'], parts=[{k: (str(v)[:400] if k in ('text', 'content', 'input') else v)
                for k, v in part.items() if k in ('type', 'name', 'is_error', 'text', 'content', 'input')} for part in m['content']]
                if isinstance(m['content'], list) else str(m['content'])[:200]) for m in body['messages'][1:]]
                for body in fixture.api.bodies if body['key'].startswith('review-')}
            try:
                fixture.stop()
            except BaseException as error:
                report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
