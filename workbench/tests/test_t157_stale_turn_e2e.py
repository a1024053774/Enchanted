"""T-157 native-new-turn counterexample and explicit recovery, through real Electron/daemon/Claude CLI.

Failure modes, specified before this test:
1. A delayed old Stop can submit after the real CLI reported a new prompt, or its refusal is silent.
2. Sidebar/header disagree about the refusal or omit the original commit/attempt and cause.
3. Recovery replays the old request, submits as operator, changes attempt, or sends automatically.
4. A repeated click creates multiple recovery prompts/deliveries, or an expired attempt receives input.
5. The fixture invents a new native turn: require an actual CLI UPS with a different prompt id first.

Oracle: user ruling relayed in controller #61 / 20261024T030734Z-001, especially (c).
The negative input is adversarial replay of a captured old real Stop plus a fresh explicit submit file
bound to that old attempt/commit; the real launch credential authenticates it. No database mutation.
Models are local scripted Messages, no vendor turns. --revision selects only product source.
"""
import argparse
from datetime import datetime, timezone
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--scenario', choices=['recover', 'expired'], default='recover')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['execute-old-stop', 'hide-reason', 'hide-recovery'])
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve prior evidence'
    marker = 'T157-NEW-NATIVE-TURN-' + uuid.uuid4().hex
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  scenario=args.scenario,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  vendor_model_turns=0, checks=[], observed={}, errors=[])
    fixture = electron = None
    new_prompt_ready, allow_new_prompt_end = threading.Event(), threading.Event()

    def check(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))
        return bool(passed)

    def plan(body):
        text, cwd = prompt_text(body), working_directory(body)
        messages = json.dumps(body['messages'], ensure_ascii=False)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        initial = [('Write', dict(file_path=f'{cwd}/answer.txt', content='candidate\n')),
                   ('Bash', dict(command='git add answer.txt', description='stage original candidate')),
                   ('Bash', dict(command='git commit -q -m ' + quote('T-157 original candidate'), description='commit original candidate')),
                   ('Bash', dict(command='printf %s "$A2A_CAPABILITY" > "$A2A_REQUEST_DIR/.t157-fixture-token"',
                                 description='export only this fixture launch credential to its private request directory'))]
        recovery = re.search(r'--request-id (recover-\d+)', messages)
        if recovery:
            return cwd, initial + [('Bash', dict(command=submit + ' --request-id ' + quote(recovery.group(1)),
                                                description='explicit submit after bound recovery check'))], '已核对原 attempt 并显式交付。'
        if marker in messages:
            new_prompt_ready.set()
            assert allow_new_prompt_end.wait(90), 'test did not release the actual new prompt'
            return cwd, initial, '新回合说明已收到。'
        return cwd, initial, '原提交已保存，本回合不交付。'

    patches = {
        'execute-old-stop': [('src/panes.ts', 'await transfer(pane, value, false);', 'await transfer(pane, value, true);')],
        'hide-reason': [('app/renderer.tsx', "delivery?.state === 'rejected' && delivery.native_turn_changed &&", 'false &&')],
        'hide-recovery': [('app/renderer.tsx', '<button data-delivery-recovery disabled=', '<button hidden data-delivery-recovery disabled=')],
    }.get(args.mutant, [])

    try:
        fixture = Fixture('t157-stale-turn-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-157 stale native turn fixture\n',
            'check.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == "candidate\\n"\n'})
        electron = Electron(fixture, 't157-stale-' + fixture.dir.name)
        electron.until('project visible', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        task = 'T-157-stale'
        fixture.card(task, 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write', model='claude-haiku-5-5', effort='low')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        report['observed']['attempt'] = attempt

        def events():
            return fixture.request('orchestration_events', task='demo+' + task)['events']

        def state():
            return fixture.request('status', fixture.operator, task='demo+' + task)['task']

        def idle():
            p = fixture.request('pane_status', thread=attempt['thread_id'])
            return p if p.get('state') == 'idle' and not p.get('active') and not p.get('writing') and not p.get('queued') else None

        fixture.wait('original real Stop completed without submit', idle, 120)
        old_stop = next(event for event in events() if event['type'] == 'turn_end_signal')
        launch = old_stop['launch']
        candidate = subprocess.check_output(['git', '-C', attempt['workspace'], 'rev-parse', 'HEAD'], text=True).strip()
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker selectable', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane_selector = '.pane[data-launch-id=' + json.dumps(launch) + ']'
        pane_js = f'document.querySelector({json.dumps(pane_selector)})'
        key = electron.until('worker input connected', f'{pane_js}?.dataset.inputEnabled === "true" && {pane_js}.dataset.paneKey')
        electron.evaluate(f'window.a2a.input({json.dumps(key)},{json.dumps(marker + chr(13))})')
        fixture.wait('actual new prompt reached native CLI model request', new_prompt_ready.is_set, 30)
        starts = [event for event in events() if event['type'] == 'turn_start_signal' and event['launch'] == launch]
        new_start = starts[-1]
        check('actual_native_new_turn_after_original_stop', new_start['seq'] > old_stop['seq'] and
              new_start['data']['prompt_id'] != old_stop['data']['prompt_id'], dict(old=old_stop, new=new_start))
        # This is a deliberately delayed old hook, not a fake current turn.
        launch_env = fixture.request('launch_show', fixture.operator, launch=launch)['launch']['env']
        token_path = Path(launch_env['A2A_REQUEST_DIR']) / '.t157-fixture-token'
        capability = token_path.read_text(encoding='utf-8')
        token_path.unlink()  # No live capability is copied into evidence or retained fixture files.
        request_id = 'late-submit-' + uuid.uuid4().hex
        delayed = dict(schema=1, request_id=request_id, command='submit', task='demo+' + task, attempt=attempt['attempt_id'],
                       session=attempt['session_id'], fence=attempt['fence'], spec_rev=attempt['spec_rev'], commit=candidate)
        outcome = fixture.request('signal', dict(launch=launch, token=capability), launch=launch,
                                  received_at=datetime.now(timezone.utc).isoformat(), raw_stdin=json.dumps(old_stop['data']),
                                  relay_files=[dict(name=request_id + '.json', raw=json.dumps(delayed))])
        report['observed']['delayed_signal_response'] = outcome
        refuses = [event for event in events() if event['type'] == 'relay_rejected' and event['data'].get('request_id') == request_id]
        rejected = bool(refuses and refuses[-1]['data']['result'].get('error') in ('relay_requires_current_stop', 'native_identity_required'))
        check('stale_submit_explicitly_refused', rejected, refuses)
        check('stale_submit_does_not_create_candidate', state()['candidate_commit'] is None)
        # Observe bounded snapshot/sidebar convergence; never repeat the hook/gate request.
        dom_expression = f'''(() => {{const p={pane_js};const b=p?.querySelector('[data-delivery-recovery]');
            return {{text:p?.innerText,header:p?.querySelector('.pane-header')?.innerText,
              sidebar:document.querySelector({json.dumps(selector)})?.innerText,
              action:b?.textContent,visible:!!b?.getClientRects().length,disabled:b?.disabled}};}})()'''
        deadline = time.monotonic() + 8
        while True:
            dom = electron.evaluate(dom_expression)
            if ('旧回合交付被拒' in (dom['header'] or '') and '旧回合交付被拒' in (dom['sidebar'] or '')) or time.monotonic() >= deadline:
                break
            time.sleep(.2)
        report['observed']['refusal_dom'] = dom
        shot = args.summary.with_name(args.summary.stem + '-refused.png')
        assert not shot.exists()
        electron.screenshot(shot)
        report['refusal_screenshot'] = str(shot)
        check('header_and_sidebar_explain_refusal', '旧回合交付被拒' in (dom['header'] or '') and '旧回合交付被拒' in (dom['sidebar'] or ''))
        check('persistent_original_fact_and_reason', '原生 CLI 已开始新回合' in (dom['text'] or '') and
              candidate[:12] in dom['text'] and attempt['attempt_id'][:8] in dom['text'] and '任务尚无候选' in dom['text'])
        check('unmatched_stop_never_enters_execution',
              not any(event['type'] == 'relay_received' and event['data'].get('input', {}).get('command') == 'submit' for event in events()))
        check('recovery_action_exists_but_no_automatic_retry', dom['visible'] and
              not any(event['type'] == 'relay_processed' and event['data'].get('request_id') == request_id for event in events()))
        if args.scenario == 'expired' and rejected and all(c['passed'] for c in report['checks']):
            revoked = fixture.request('revoke', fixture.terminal, task=task, reason='T-157 fixture stale recovery guard')
            assert revoked.get('ok'), revoked
            time.sleep(2)
            expired_dom = electron.evaluate(f'''(() => {{const p={pane_js};const b=p?.querySelector('[data-delivery-recovery]');
                return {{text:p?.innerText,disabled:b?.disabled,input:p?.dataset.inputEnabled}};}})()''')
            report['observed']['expired_dom'] = expired_dom
            check('expired_attempt_cannot_request_recovery', expired_dom['input'] == 'false' and expired_dom['disabled'] is True and
                  '已失效' in expired_dom['text'])
            before = len([event for event in events() if event['type'] == 'terminal_input_write_intent'])
            electron.evaluate(f'{pane_js}?.querySelector("[data-delivery-recovery]")?.click()')
            time.sleep(.3)
            check('expired_recovery_click_sends_no_input', before == len([event for event in events() if event['type'] == 'terminal_input_write_intent']))
            expired_shot = args.summary.with_name(args.summary.stem + '-expired.png')
            assert not expired_shot.exists()
            electron.screenshot(expired_shot)
            report['expired_screenshot'] = str(expired_shot)
        allow_new_prompt_end.set()
        if args.scenario == 'recover':
            fixture.wait('actual new prompt completed', idle, 30)
        if args.scenario == 'recover' and rejected and all(c['passed'] for c in report['checks']):
            button = pane_selector + ' [data-delivery-recovery]'
            electron.until('explicit recovery available', f'!document.querySelector({json.dumps(button)})?.disabled')
            recovery_seq = refuses[-1]['seq']
            recovery_id = 'recover-' + str(recovery_seq)
            report['observed']['expected_recovery_request_id'] = recovery_id
            # Same-event-loop double click, before either asynchronous preflight can finish.
            electron.evaluate(f'(() => {{const b=document.querySelector({json.dumps(button)});b.click();b.click();}})()')
            fixture.wait('original attempt explicitly submitted after recovery', lambda: state()['candidate_commit'] == candidate, 60)
            fixture.wait('recovery receipt acknowledged and idle', idle, 45)
            recovered = state()
            recovered_requests = [event for event in events() if event['type'] == 'relay_received' and event['data'].get('input', {}).get('command') == 'submit']
            check('recovery_is_single_fresh_request', len(recovered_requests) == 1 and recovered_requests[0]['data']['input']['request_id'] == recovery_id,
                  recovered_requests)
            prompts = [event for event in events() if event['type'] == 'terminal_input_write_intent' and
                       isinstance(event['data'].get('data'), str) and event['data']['data'].startswith('\x1b[200~') and
                       '--request-id ' + recovery_id in event['data']['data']]
            check('double_click_sends_one_recovery_prompt', len(prompts) == 1, prompts)
            check('recovery_preserves_attempt_session_fence_version_commit', recovered['current_attempt']['attempt_id'] == attempt['attempt_id'] and
                  recovered['current_attempt']['session_id'] == attempt['session_id'] and recovered['current_attempt']['fence'] == attempt['fence'] and
                  recovered['spec_rev'] == attempt['spec_rev'] and recovered['candidate_commit'] == candidate)
            submit_stop = next(event for event in reversed(events()) if event['type'] == 'turn_end_signal' and
                               event['seq'] < recovered_requests[0]['seq'])
            check('recovery_uses_new_native_turn_and_one_delivery', recovered['current_attempt'].get('turn_id') == submit_stop['data']['prompt_id'] and
                  recovered['current_attempt'].get('turn_id') != old_stop['data']['prompt_id'] and
                  recovered['current_attempt'].get('delivery', {}).get('number') == 1)
            check('old_request_never_accepted', not any(event['type'] == 'relay_processed' and event['data'].get('request_id') == request_id for event in events()))
            report['observed']['recovered_task'] = recovered
        report['observed']['events'] = events()
        report['observed']['final_task'] = state()
        report['status'] = 'PASS' if report['checks'] and all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['errors'].append(dict(error=str(error), traceback=traceback.format_exc()))
    finally:
        allow_new_prompt_end.set()
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
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), errors=report['errors']), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
