"""T-179（L06）：worker 窗格里直接打印整段门禁回执原始 JSON，用户无法阅读。
真实后台、门禁、终端主控，真实 Claude Code worker 与审查员（模型是本地脚本化接口），真实 Electron 窗口经 DevTools 协议操作。
期望值来自 T-179 ticket：发给 worker 的门禁回执在窗格里是简短可读的中文摘要（状态、候选提交、下一步），完整 JSON 留在
记录/门禁库可查；不改门禁语义；worker 交付后窗格只出现几行摘要，完整内容在记录页可查；门禁与 worker 后续动作不受影响。

场景：worker 写 one.txt、提交、submit；回合结束时门禁处理 submit，后台把回执发回 worker；之后主控照常 verify、审查、integrate。

失败方式（先列再写）：
1. 发回 worker 的回执仍是整段 JSON（L06 原样）：worker 收到的文字与窗格里出现 card_snapshot_id、integration_ref 这类门禁内部字段。
2. 摘要缺要素：没有“已交付”的状态、没有候选提交（短号）、没有下一步。
3. 摘要过长，不是“几行”（超过 6 行）。
4. 完整回执丢了：门禁库里没有，或记录页看不到；记录页的全文与门禁库不一致（候选提交完整号对不上）。
5. 改了门禁语义：交付后 verify、审查、integrate 走不通。
6. 门禁回执混进“用户输入记录”（那里只记用户亲手的输入）。
--revision 在该版本源码上跑同一场景（修前应复现 1、2、4）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory  # noqa: E402

MUTANTS = {
    # The summary drops the candidate commit.
    'no-commit': [('src/gateReceipts.ts', "task.candidate_commit ? `候选提交 ${String(task.candidate_commit).slice(0, 12)}` : '还没有候选提交'", "''")],
    # The records page lists receipts without their full content.
    'no-full-text': [('app/RecordsPage.tsx', '<pre className="receipt-full">{JSON.stringify(receipt.result, null, 2)}</pre>', '<pre className="receipt-full" />')],
}
INTERNAL = ('card_snapshot_id', 'integration_ref', 'user_input_observer')


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

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            shape.update(verdict='可合并', findings=[], report={'结论': '候选只改了 one.txt，满足任务卡。',
                                                                '完成条件与变异检查': '变异：删除 one.txt，完成条件退出 1。'})
            return 'reviewer', [('Bash', dict(command='rm one.txt; python3 check.py; echo "mutation rc=$?"', description='mutation'))], \
                json.dumps(shape, ensure_ascii=False)
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Write', dict(file_path=f'{cwd}/one.txt', content='one\n')),
                          ('Bash', dict(command='git add one.txt', description='stage')),
                          ('Bash', dict(command=f'git commit -q -m {quote("T-1 fixture change")}', description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    fixture = Fixture('t179-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    electron = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def status():
        return fixture.request('status', fixture.operator, task='demo+T-1')['task']

    def worker_prompts():
        # What the worker's model was given as user text after its first prompt, in order.
        texts = []
        for body in fixture.api.bodies:
            if body['key'] != 'worker':
                continue
            for message in body['messages']:
                if message['role'] != 'user':
                    continue
                content = message['content']
                parts = [content] if isinstance(content, str) else [p.get('text', '') for p in content if isinstance(p, dict) and p.get('type') == 'text']
                for part in parts:
                    if part and part not in texts:
                        texts.append(part)
        return texts

    try:
        fixture.start(args.claude, {'README.md': 'demo\n', 'check.py': 'import pathlib, sys\nsys.exit(0 if pathlib.Path("one.txt").read_text() == "one\\n" else 1)\n'})
        fixture.card('T-1', 'one.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        launch = dispatched['attempt']['runtime_identity']['launch']
        fixture.wait('交付', lambda: status()['state'] == 'submitted', 180)
        candidate = status()['candidate_commit']
        receipt_text = fixture.wait('回执发回 worker', lambda: next((t for t in worker_prompts() if '异步请求处理结果' in t or '门禁回执' in t), None), 60)
        report['observed']['receipt_to_worker'] = receipt_text
        lines = [line for line in receipt_text.splitlines() if line.strip()]
        # 1: no raw gate record in what the worker gets.
        check('worker_receipt_not_raw_json', not any(word in receipt_text for word in INTERNAL), [w for w in INTERNAL if w in receipt_text])
        # 2 and 3: a short summary with state, short candidate commit and next step.
        check('worker_receipt_has_state_commit_next', '已交付' in receipt_text and candidate[:12] in receipt_text and '下一步' in receipt_text, receipt_text[:400])
        check('worker_receipt_few_lines', len(lines) <= 6, len(lines))
        trace = fixture.state / 'traces' / launch / 'pty.raw'
        raw = trace.read_bytes().decode('utf-8', 'replace') if trace.exists() else ''
        report['observed']['pty_internal_words'] = {w: raw.count(w) for w in INTERNAL}
        check('pane_shows_no_raw_receipt', trace.exists() and not any(raw.count(w) for w in INTERNAL), report['observed']['pty_internal_words'])

        # 5: the gate goes on as before.
        verified = fixture.request('verify', fixture.terminal, task='T-1')
        assert verified.get('ok'), verified
        fixture.wait('审查通过', lambda: (lambda s: s['state'] == 'verified' and s.get('review', {}).get('state') == 'passed')(status()), 240)
        fixture.wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in fixture.request('events', fixture.operator, task='demo+T-1')['events']), 60)
        score = fixture.out / 'score.json'
        score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=3,
                                         engineering_reason='夹具', notes='T-179 fixture'), ensure_ascii=False), encoding='utf-8')
        integrated = fixture.request('integrate', fixture.terminal, task='T-1', score_file=str(score))
        check('gate_flow_unchanged', integrated.get('ok') and status()['state'] == 'accepted', integrated.get('error'))

        # 4: the full receipt is in the gate store, and readable on the records page.
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            stored = [json.loads(row[0]) for row in connection.execute(
                "SELECT r.data FROM relay_results r JOIN relay_requests q ON q.key=r.key WHERE q.launch=? AND json_extract(q.input,'$.command')='submit'", (launch,))]
        check('full_receipt_in_store', len(stored) == 1 and stored[0].get('task', {}).get('candidate_commit') == candidate, len(stored))
        electron = Electron(fixture, 't179-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('记录页签', "[...document.querySelectorAll('.task-header nav button')].some(b => b.textContent === '记录')", 30)
        electron.evaluate("[...document.querySelectorAll('.task-header nav button')].find(b => b.textContent === '记录').click()")
        rows = electron.until('回执出现', "(() => { const r = [...document.querySelectorAll('[data-receipt-key]')]; return r.length ? r.map(n => ({ key: n.dataset.receiptKey, command: n.dataset.receiptCommand, text: n.innerText })) : null; })()", 30) \
            if electron.evaluate("!!document.querySelector('.receipts')") else []
        report['observed']['records_receipts'] = rows
        submit_row = next((row for row in rows if row['command'] == 'submit'), None)
        check('records_page_lists_submit_receipt', submit_row is not None and '已交付' in submit_row['text'], rows)
        if submit_row:
            electron.evaluate(f"document.querySelector('[data-receipt-key=\"{submit_row['key']}\"] details').open = true")
            full = electron.evaluate(f"document.querySelector('[data-receipt-key=\"{submit_row['key']}\"] .receipt-full')?.textContent ?? ''")
            check('records_page_full_receipt_matches_store', candidate in full and 'card_snapshot_id' in full, full[:300])
            electron.screenshot(fixture.out / '01-records-receipt.png')
        else:
            check('records_page_full_receipt_matches_store', False, '没有回执行')
        # 6: user input records do not carry gate receipts.
        inputs = fixture.request('user_input_records', fixture.operator, project='demo')
        texts = [record.get('text', '') for record in inputs.get('records', [])] if inputs.get('ok') else []
        check('receipts_not_user_input', not any('异步请求处理结果' in t or '门禁回执' in t for t in texts), len(texts))
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
