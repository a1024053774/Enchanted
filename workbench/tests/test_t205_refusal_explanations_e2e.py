"""T-205：门禁拒绝除代码外还给一句原因和下一步，主控的 a2a 回执、任务页时间线、worker 窗格回执用同一份说明，代码照旧保留。
真实后台、socket、门禁；主控终端是真实 zsh 里的真实 `a2a` 命令；worker 是真实安装的 Claude Code，模型换成本地脚本化接口。

预期来自需求（T-205 与第 2 轮试用发现 2、3）：
- 主控 `a2a call dispatch` 一张验收文件不在 Git 里的卡：回执 `error` 仍是 oracle_not_found，另有原因与下一步；
  任务页时间线这一步除代码外有同一句原因，并点出缺的是哪个文件。
- worker 交付后在新回合补交：回执 `stale_turn`，worker 窗格收到的回执除代码外有原因，下一步说明要改卡、回收、重派。

失败方式（先列再写）：
1. 只显示代码（修前）。
2. 说明替换了代码：error 字段或界面里看不到原来的代码。
3. 三处文案各写一份，彼此不一致：时间线与 worker 回执里的原因必须等于后台回执里的同一句。
4. stale_turn 的下一步仍是“由门禁或主控另行说明”这类不给办法的话，或建议在原 attempt 上重交。
5. oracle_not_found 的说明不点出缺哪个文件。
--revision 在该版本的隔离源码上跑同一场景（修前应在第 1 条失败）；--mutant 去掉某一处接线。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time
import traceback
import uuid

from scripted_claude import Fixture, prompt_text, quote

RESUBMIT = '请再交付一次当前提交'
MUTANTS = {
    # Each drops one of the three places; the run must fail at that place's checks.
    'reply-without-explanation': [('src/daemon.ts', 'connection.end(JSON.stringify(explained(result)) + "\\n");', 'connection.end(JSON.stringify(result) + "\\n");')],
    'history-without-explanation': [('src/gates/taskHistory.ts', "${why ? `。${why.reason}下一步：${why.next}` : ''}", '')],
    'receipt-without-explanation': [('src/gateReceipts.ts', "if (why) return [refused, '原因：' + why.reason, '下一步：' + why.next];", '')],
}


def texts_of(body):
    found = []
    for message in body['messages']:
        if message['role'] != 'user':
            continue
        content = message['content']
        found.append(content if isinstance(content, str) else '\n'.join(part.get('text', '') for part in content
                                                                          if isinstance(part, dict) and part.get('type') == 'text'))
    return [text for text in found if text]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, claude=args.claude,
                  runtime='real daemon/gate/zsh/a2a; real Claude Code worker on a scripted Messages endpoint', checks=[])
    fixture = None
    worker_feedback = []

    # Every check runs; the failures are listed together so a run before the fix shows all three places.
    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if condition:
            report['checks'].append(name)
        else:
            report.setdefault('failed', []).append(name)

    def plan(body):
        cwd = re.search(r'[Ww]orking directory: (/[^\s"\\]+)', json.dumps(body, ensure_ascii=False)).group(1)
        texts = texts_of(body)
        first = prompt_text(body)
        if '审查这一次交付' in first:
            raise AssertionError('本场景不验收，不应有审查')
        submit = re.search(r'显式交付：\n(.+)\n', first)
        assert submit, '派发提示里没有交付命令'
        line = submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        feedback = [text for text in texts if '门禁回执' in text]
        if feedback:
            worker_feedback[:] = feedback
        steps = [('Write', dict(file_path=f'{cwd}/value.txt', content='written by the worker\n')),
                 ('Bash', dict(command='git add value.txt && git commit -q -m "worker change"', description='commit')),
                 ('Bash', dict(command=line, description='submit'))]
        if any(RESUBMIT in text for text in texts):
            steps.append(('Bash', dict(command=line, description='submit again')))
        return 'worker', steps, '收到。'

    try:
        fixture = Fixture('t205-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        fixture.start(args.claude, {'value.txt': 'original\n', 'check.py': 'import pathlib\nraise SystemExit(0 if "worker" in pathlib.Path("value.txt").read_text() else 1)\n'})
        project, out = fixture.project, fixture.out

        # 1. The controller dispatches a card whose acceptance file is not in Git, through the real a2a command.
        fixture.card('T-1', 'value.txt', 'missing_check.py')
        window = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project=project)
        assert window['ok'], window
        reply_file = out / 'a2a-dispatch.json'
        command = 'a2a call ' + quote(json.dumps(dict(command='dispatch', task='T-1', runtimeMode='workspace-write'))) + f' > {reply_file}; print -r -- done > {out}/a2a-done'
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data=command + '\r')['ok']
        fixture.wait('a2a 返回', lambda: (out / 'a2a-done').exists(), 60)
        reply = json.loads(reply_file.read_text(encoding='utf-8'))
        report['a2a_reply'] = reply
        check('a2a_reply_keeps_code', reply.get('ok') is False and reply.get('error') == 'oracle_not_found', reply)
        why = reply.get('explanation') or {}
        check('a2a_reply_explains', bool(why.get('reason')) and bool(why.get('next')), why)
        history = fixture.request('task_history', fixture.operator, task='T-1')
        report['t1_history_raw_keys'] = list(history)
        refused = [step for step in history.get('history', history).get('steps', []) if step['label'] == '门禁拒绝']
        report['t1_history_refusals'] = refused
        check('history_keeps_code_and_same_reason', len(refused) == 1 and 'oracle_not_found' in refused[0]['detail']
              and bool(why.get('reason')) and why['reason'] in refused[0]['detail'], refused)
        check('history_names_missing_file', bool(refused) and 'missing_check.py' in refused[0]['detail'], refused)

        # 2. A worker delivers, then is asked in its pane to deliver again in a new turn: stale_turn.
        fixture.card('T-2', 'value.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-2', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        fixture.wait('T-2 交付', lambda: fixture.request('status', fixture.operator, task='T-2')['task']['state'] == 'submitted', 180)
        fixture.wait('第一份回执到 worker', lambda: worker_feedback, 120)
        first_feedback = list(worker_feedback)
        launch = attempt['runtime_identity']['launch']
        pane = fixture.request('window_open', fixture.operator, launch=launch, task=attempt['task_id'])
        assert pane['ok'], pane
        time.sleep(8)  # the worker answers the receipt with text only; let that turn end before typing
        assert fixture.request('window_input', pane['identity'], sequence=1, request_id=str(uuid.uuid4()), data='\x1b[200~' + RESUBMIT + '\x1b[201~')['ok']
        assert fixture.request('window_input', pane['identity'], sequence=2, request_id=str(uuid.uuid4()), data='\r')['ok']
        fixture.wait('补交被拒的回执到 worker', lambda: worker_feedback != first_feedback and 'stale_turn' in worker_feedback[-1], 180)
        receipt = worker_feedback[-1]
        report['worker_receipt'] = receipt
        receipts = fixture.request('relay_receipts', fixture.operator, project=project)
        refusal = next(row for row in receipts['receipts'] if not row['ok'])
        report['relay_receipt'] = {key: refusal[key] for key in ('command', 'ok', 'summary', 'result')}
        check('relay_result_keeps_code', refusal['result'].get('error') == 'stale_turn', refusal['result'])
        reason = next((line[len('原因：'):] for line in receipt.splitlines() if line.startswith('原因：')), None)
        check('worker_receipt_keeps_code_and_explains', 'stale_turn' in receipt and bool(reason), receipt)
        check('records_page_summary_same_as_pane', '\n'.join(refusal['summary']) in receipt, refusal['summary'])
        check('stale_turn_next_is_redispatch', all(word in receipt for word in ('revise', 'reclaim', 'dispatch')), receipt)
        history = fixture.request('task_history', fixture.operator, task='T-2')
        refused = [step for step in history.get('history', history).get('steps', []) if step['label'] == '门禁拒绝']
        report['t2_history_refusals'] = refused
        check('history_stale_turn_same_reason', bool(reason) and any('stale_turn' in step['detail'] and reason in step['detail'] for step in refused), refused)
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        if fixture:
            report['api'] = fixture.api.snapshot()
            try:
                fixture.stop()
            except Exception as error:
                report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
