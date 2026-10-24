"""T-166：普通工作回合中的用户输入。真实 Electron / 后台 / PTY / Claude CLI，本地脚本化 Messages。

失败方式（先列再写）：
1. 输入发生在普通工作回合（模型仍在生成最终回复，不是 Stop 交付批次），CLI 的
   UserPromptSubmit 沿用运行中回合的 prompt_id，后台判 claude_prompt_id_reused，
   回合变得不可信，随后原回合的 Stop 被拒（current_turn_untrusted），worker 停在未知。
2. 修复把原回合的身份换成输入回合，或把输入吞掉、改写、延后，门禁通过却没有原样进入 CLI。
3. 输入引起的新回合没有由原生转录登记，最终 Stop 不匹配，停在运行中。
4. 用重复 submit / 自动重试取得表面成功，或接受了别的 attempt/提交。
5. 把启动失败、脚本化模型错误或时序未命中算成产品红态，或覆盖旧证据。

期望来自 T-166 ticket 与用户原则（构思主控 answer 20261024T030734Z-001）：输入原样直达 CLI，
只记人工介入；原回合交付照常通过；门禁核对不放松。
--revision 只选择产品源码（修前运行应复现红态）；不修补时序、不暂停进程。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid

from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory


ROOT = Path(__file__).resolve().parents[2]
NOTE = '人工介入：仅在交付说明注明收到此消息，继续原卡。'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  vendor_model_turns=0, model_backend='local scripted Messages endpoint',
                  red_reproduced=False, checks=[], observed={}, errors=[])
    note = NOTE + ' sentinel-' + uuid.uuid4().hex
    input_packets = ['\x1b[200~' + note + '\x1b[201~', '\r']
    report['input'] = note
    report['input_packets'] = input_packets
    report['scope'] = 'input typed while the original turn is still generating its final reply (not a Stop batch)'
    fixture = electron = None
    finish_ready, allow_finish = threading.Event(), threading.Event()

    def plan(body):
        text, cwd = prompt_text(body), working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1)
        submit = submit.replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        steps = [('Write', dict(file_path=f'{cwd}/answer.txt', content='原任务草稿\n')),
                 ('Bash', dict(command='git add answer.txt', description='stage candidate')),
                 ('Bash', dict(command='git commit -q -m ' + quote('T-166 isolated draft'), description='commit candidate')),
                 ('Bash', dict(command=submit, description='queue explicit submit'))]
        count = sum(1 for message in body['messages'] if message['role'] == 'assistant' and isinstance(message['content'], list)
                    and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
        # Hold the original turn's final reply: the user types while the model is
        # still working, as in T-164 (input at 06:26:12, final reply at 06:26:13).
        if count >= len(steps) and not allow_finish.is_set():
            finish_ready.set()
            assert allow_finish.wait(60), '未在期限内完成输入'
        return cwd, steps, '已完成原任务。'

    def record(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        fixture = Fixture('t166-busy-input-', plan, revision=args.revision)
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-166 一次性仓库\n',
            'check.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == "原任务草稿\\n"\n'})
        electron = Electron(fixture, 't166-' + fixture.dir.name)
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        task = 'T-166-probe'
        fixture.card(task, 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write',
                                     model='claude-haiku-5-5', effort='low')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        report['observed']['attempt'] = attempt
        fixture.wait('原回合工具已执行完、最终回复仍在生成', finish_ready.is_set, 150)
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane_selector = '.pane[data-launch-id=' + json.dumps(launch) + ']'
        expression = f'document.querySelector({json.dumps(pane_selector)})'
        pane_key = electron.until('worker 窗格可输入', f'{expression}?.dataset.inputEnabled === "true" && {expression}.dataset.paneKey')

        def events():
            return fixture.request('orchestration_events', task='demo+' + task)['events']

        before = [event for event in events() if event['launch'] == launch and event['type'] == 'turn_end_signal']
        record('input_precedes_original_stop', not before, before)
        writes = []
        for data in input_packets:
            result = electron.evaluate(f'window.a2a.input({json.dumps(pane_key)},{json.dumps(data)})')
            writes.append(dict(data=data, result=result))
        report['observed']['writes'] = writes

        def ups_seen():
            return [event for event in events() if event['launch'] == launch and (event['type'] == 'claude_prompt_queued' or (
                event['type'] == 'native_question_unverified' and event['data'].get('hook_event_name') == 'UserPromptSubmit'))]

        report['observed']['ups'] = fixture.wait('CLI 对输入发出 UserPromptSubmit', ups_seen, 30)
        allow_finish.set()

        def outcome_seen():
            # A Stop refused as untrusted never transfers the submit, so it has no receipt.
            return [event for event in events() if event['launch'] == launch and (event['type'] in ('relay_processed', 'relay_rejected') or (
                event['type'] == 'native_question_unverified' and event['data'].get('hook_event_name') == 'Stop'))]

        fixture.wait('原回合 Stop 有明确结果', outcome_seen, 45)
        results = [event for event in events() if event['launch'] == launch and event['type'] in ('relay_processed', 'relay_rejected')]
        accepted = [event for event in results if event['type'] == 'relay_processed' and event['data'].get('result', {}).get('ok')]
        record('original_submit_accepted', bool(accepted), results)
        if accepted:
            fixture.wait('原样输入进入真实 CLI 的下一次模型请求',
                         lambda: any(note in json.dumps(body, ensure_ascii=False) for body in fixture.api.bodies), 30)
            fixture.wait('worker 回到空闲', lambda: (
                lambda p: p.get('state') == 'idle' and not p.get('writing') and not p.get('active') and not p.get('queued'))(
                    fixture.request('pane_status', thread=attempt['thread_id'])), 45)
        else:
            # Observe the refused state for the red verdict; this is not a retry.
            time.sleep(5)
        trace = events()
        mine = [event for event in trace if event['launch'] == launch]
        report['observed']['timeline'] = [event for event in mine if event['type'] in (
            'turn_end_signal', 'relay_received', 'relay_processed', 'relay_rejected', 'stop_not_matched', 'native_question_unverified',
            'turn_submit_intent', 'turn_start_signal', 'claude_prompt_queued', 'claude_stop_waiting_transcript',
            'terminal_input_write_intent', 'terminal_input_written', 'pane_idle', 'pane_waiting_native_queue', 'stop_transfer_failed')]
        report['observed']['gate_events'] = fixture.request('events', fixture.operator, task='demo+' + task)['events']
        time.sleep(2)
        report['observed']['pane'] = fixture.request('pane_status', thread=attempt['thread_id'])
        report['observed']['task'] = fixture.request('status', fixture.operator, task='demo+' + task)['task']
        report['observed']['sidebar'] = fixture.request('sidebar_snapshot')
        report['observed']['dom'] = electron.evaluate(f'''(() => {{const p={expression};
            return {{header:p?.querySelector('.pane-state')?.textContent, sidebar:document.querySelector({json.dumps(selector)})?.innerText}};}})()''')
        screenshot = args.summary.with_suffix('.png')
        assert not screenshot.exists(), '保留既有截图'
        electron.screenshot(screenshot)
        report['screenshot'] = str(screenshot)
        poisoned = [event for event in mine if event['type'] == 'native_question_unverified' and
                    'claude_prompt_id_reused' in str(event['data'].get('reason'))]
        untrusted_stop = [event for event in mine if event['type'] == 'native_question_unverified' and
                          'current_turn_untrusted' in str(event['data'].get('reason'))]
        record('busy_input_not_judged_reused', not poisoned, poisoned)
        record('original_stop_trusted', not untrusted_stop, untrusted_stop)
        input_written = [event for event in mine if event['type'] == 'terminal_input_written']
        request_ids = {event['data']['request_id'] for event in input_written}
        record('input_bytes_unchanged', [event['data'].get('data') for event in mine
               if event['type'] == 'terminal_input_write_intent' and event['data'].get('request_id') in request_ids] == input_packets)
        record('native_cli_received_original_input', any(note in json.dumps(body, ensure_ascii=False) for body in fixture.api.bodies))
        human = [event for event in report['observed']['gate_events'] if event['type'] == 'human_intervention']
        record('human_intervention_bound_original_attempt', any(event['attempt'] == attempt['attempt_id'] for event in human))
        task_state = report['observed']['task']
        submit_received = [event for event in mine if event['type'] == 'relay_received' and event['data'].get('input', {}).get('command') == 'submit']
        record('exactly_one_submit_no_automatic_retry', len(submit_received) == 1)
        record('submit_bound_original_attempt_and_commit', bool(submit_received) and
               task_state['current_attempt']['attempt_id'] == attempt['attempt_id'] and
               task_state['candidate_commit'] == submit_received[0]['data']['input']['commit'])
        original_start = next((event for event in mine if event['type'] == 'turn_start_signal'), None)
        record('submit_bound_original_native_turn', bool(original_start) and
               task_state['current_attempt'].get('turn_id') == original_start['data'].get('prompt_id'))
        queued = [event for event in mine if event['type'] == 'claude_prompt_queued']
        starts = [event for event in mine if event['type'] == 'turn_start_signal' and event['data'].get('origin') == 'native-transcript'
                  and queued and event['seq'] > queued[0]['seq']]
        record('queued_native_turn_bound_and_completed', bool(starts) and any(
            event['type'] == 'pane_idle' and event['data'].get('stop', {}).get('prompt_id') == starts[0]['data']['prompt_id'] for event in mine))
        agent = next(row for row in report['observed']['sidebar']['agents'] if row['id'] == launch)
        record('returns_idle', agent['state'] == 'idle' and report['observed']['pane'].get('state') == 'idle' and
               report['observed']['pane'].get('failed') is None, dict(sidebar=agent['state'], pane=report['observed']['pane'].get('state')))
        # Red as observed in T-164: the reused UPS poisons the turn, its real Stop is refused, delivery never lands.
        report['red_reproduced'] = bool(poisoned and untrusted_stop and not accepted and task_state['candidate_commit'] is None)
        report['status'] = 'PASS' if all(check['passed'] for check in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['errors'].append(dict(error=str(error), traceback=traceback.format_exc()))
    finally:
        allow_finish.set()
        if fixture:
            report['observed']['api'] = fixture.api.snapshot()
            if 'attempt' in report['observed']:
                try:
                    report['observed']['final_pane'] = fixture.request('pane_status', thread=report['observed']['attempt']['thread_id'])
                    report['observed']['final_timeline'] = fixture.request('orchestration_events', task='demo+T-166-probe')['events']
                except Exception as error:
                    report['errors'].append(dict(diagnostics=str(error)))
        for name, resource in [('electron', electron), ('fixture', fixture)]:
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    report['status'] = 'INCOMPLETE'
                    report['errors'].append(dict(cleanup=name, error=str(error)))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
