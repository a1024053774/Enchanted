"""T-229：agy、opencode worker 窗格里的用户输入记录不带按键，拼不准时标 text_uncertain。
真实后台、门禁、经角色申请批准的终端主控；agy、opencode 用 T-187 的本地原生替身（t187_fake_cli.c 受管模式与
t187_fake_worker.py，不连模型）。按键经后台的窗口输入接口逐块送进 worker 窗格，与界面发出的数据相同。

预期来自需求（用户 2026-11-01：“只记录我发送之后的完整的这一条,不要把输入过程中的操作以及其他琐碎的东西记录进去”，
T-229：“agy、opencode 没有提交钩子，仍按 attach 拼出的那句记；拼不准时照旧标 text_uncertain，不改成猜测”）：
1. 打 “abc”、左方向键、“d”、回车：只记一条 message，文字 “abdc”，记录里没有 content。
2. 打 “xy”、↑、回车：只记一条，文字 “xy”，content 只有 text_uncertain: true，没有按键。
3. 打 “zz”、Ctrl-C 清掉（没发出），再打 “ok”、回车：只记 “ok”。
4. 每条记录一条人工介入。

失败方式（先列再写）：
1. 记录里仍带 content.keys 或 action（修前）。
2. ↑ 之后不再标 text_uncertain，或把拼出的字当成确定的。
3. 方向键能跟上的编辑也被标 text_uncertain。
4. agy、opencode 没有提交钩子，记录因为改走钩子而消失。
5. 被 Ctrl-C 清掉的草稿混进下一条记录。
6. 人工介入不再产生，或与记录条数不符。
--revision 在该版本源码上跑（修前应失败）；--mutant 见 MUTANTS（由 T-206 测试移来：Claude worker 改由钩子记录后，
草稿的编辑只对 agy、opencode 起作用）。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture  # noqa: E402

HERE = Path(__file__).resolve().parent
MUTANTS = {
    # The draft ignores the cursor: the text is appended at the end.
    'cursor-ignored': [('src/inputDraft.ts', '  if (key === "←") draft.cursor = Math.max(0, draft.cursor - 1);\n  else if', '  if')],
    # Ctrl-C does not start the draft over, so the cleared text is recorded with the next message.
    'ctrl-c-keeps-draft': [('src/inputDraft.ts', 'const CLEARS = new Set(["\\x03", "\\x04"]);', 'const CLEARS = new Set<string>();')],
}
FILES = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--cli', choices=['agy', 'opencode'], required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, cli=args.cli, revision=args.revision, mutant=args.mutant, real_model_turns=0,
                  checks=[], observed={})

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    fixture = Fixture('t229m-', lambda body: ('unused', [], '好的。'), revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
    report['fixture'] = str(fixture.dir)
    fake = fixture.dir / 'fake-bin'
    try:
        fake.mkdir()
        subprocess.run(['cc', '-O2', '-o', str(fake / 'agy'), str(HERE / 't187_fake_cli.c')], check=True)
        os.link(fake / 'agy', fake / 'opencode')
        shutil.copy2(HERE / 't187_fake_worker.py', fake / 't187_fake_worker.py')
        settings = fixture.home / '.gemini/antigravity-cli/settings.json'
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({'trustedWorkspaces': []}), encoding='utf-8')
        fixture.start(args.claude, FILES, launch_config=dict(agy_bin=str(fake / 'agy'), opencode_bin=str(fake / 'opencode')))
        fixture.card('T-1', 'done.txt', 'check.py', executor=dict(cli=args.cli, model='fixture-model', effort='high'))
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        thread = attempt['thread_id']
        launch = fixture.run_cli('pane_status', '--thread', thread)['launch']
        idle = lambda: (lambda p: p.get('state') == 'idle' and not p.get('writing') and not p.get('active') and not p.get('queued'))(
            fixture.request('pane_status', thread=thread))
        fixture.wait('worker 做完任务书、空闲', idle, 120)
        window = fixture.request('window_open', fixture.operator, launch=launch, task='demo+T-1')
        assert window['ok'], window
        sequence = 0

        def send(data):
            nonlocal sequence
            sequence += 1
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent
            time.sleep(.1)

        def inputs():
            with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
                return [json.loads(row[0]) for row in db.execute(
                    "SELECT data FROM user_inputs WHERE json_extract(data,'$.target.attempt')=? ORDER BY rowid", (attempt['attempt_id'],))]

        shown = lambda records: [dict(form=i['form'], text=i['text'], content=i.get('content')) for i in records]
        # 1. Keys the draft follows: the record is the text alone.
        for chunk in ('a', 'b', 'c', '\x1b[D', 'd', '\r'):
            send(chunk)
        first = inputs()
        report['observed']['after_1'] = shown(first)
        check('followed_edit_text_only', len(first) == 1 and first[0]['form'] == 'message' and first[0]['text'] == 'abdc' and
              'content' not in first[0], report['observed']['after_1'])
        # 2. Up may change what the CLI holds in a way the draft cannot follow.
        for chunk in ('x', 'y', '\x1b[A', '\r'):
            send(chunk)
        second = inputs()[len(first):]
        report['observed']['after_2'] = shown(second)
        check('unfollowed_key_marked_uncertain_without_keys', len(second) == 1 and second[0]['form'] == 'message' and
              second[0]['text'] == 'xy' and second[0].get('content') == {'text_uncertain': True}, report['observed']['after_2'])
        # 3. A draft cleared with Ctrl-C was never sent.
        for chunk in ('z', 'z', '\x03', 'o', 'k', '\r'):
            send(chunk)
        third = inputs()[len(first) + len(second):]
        report['observed']['after_3'] = shown(third)
        check('cleared_draft_not_recorded', len(third) == 1 and third[0]['text'] == 'ok' and 'content' not in third[0],
              report['observed']['after_3'])
        records = inputs()
        human = [e for e in fixture.request('events', fixture.operator, task='demo+T-1')['events']
                 if e['type'] == 'human_intervention' and e['attempt'] == attempt['attempt_id']]
        report['observed']['human_interventions'] = len(human)
        check('interventions_follow_records', len(human) == len(records) == 3, dict(human=len(human), inputs=len(records)))
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
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
