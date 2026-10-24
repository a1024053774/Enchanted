"""T-167：Codex worker 的门禁回执粘贴后提交未生效。真实 Electron、后台、PTY 与真实 Codex CLI；
模型端为本地脚本化 Responses（响应头报告额度已用 94%），不调用厂商模型、不读写用户 ~/.codex。

失败方式（先列再写）：
1. 额度接近上限时 Codex 在回合结束后弹出换模型提示；a2a 随后写入的回执粘贴与回车被提示吃掉，
   模型被换成较小的模型，回合没有开始，后台却记“已提交”，界面看不出来（T-164 N01）。
2. 修法用自动重发、补按回车或替用户回答提示取得表面成功。
3. 修法只隐藏提示，CLI 因别的原因没开始回合时界面仍显示为正常处理中。
4. 修法改变了 worker 的模型或强度，或影响 Claude worker 的粘贴提交。

期望来自 T-167 ticket 与用户原则：不把 Enter 当默认批准、不自动重发；以原生回合开始为准。
--scenario receipt：产品启动参数原样，期望回执开始新回合且模型不变。
--scenario dialog-open：去掉隐藏提示的启动参数，让提示真实出现，期望界面如实显示“回合未开始”且不重发。
--revision 只选产品源码（修前运行应复现红态）；--mutant 注入已知坏实现。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripted_claude import Electron, Fixture, ROOT
from t112_native_api import message_events, request_source

MODEL = 'gpt-6.1-sol'
RECEIPT = '⟦测试回执⟧ T167-RECEIPT 请仅确认收到并结束。'
HIDE = '      "-c", "notice.hide_rate_limit_model_nudge=true",\n'
START_CHECK = 'if (this.store.lastEvent(pane.record.id, ["turn_submitted", "turn_start_signal"])?.type !== "turn_submitted") return;'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--codex', default=shutil.which('codex'))
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--scenario', choices=['receipt', 'dialog-open'], default='receipt')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['no-start-check'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请换新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, scenario=args.scenario, revision=args.revision, mutant=args.mutant,
                  model_backend='local scripted Responses (x-codex-primary-used-percent: 94)', vendor_model_turns=0,
                  code_version=subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip(),
                  codex_version=subprocess.check_output([args.codex, '--version'], text=True).strip(),
                  red_reproduced=False, checks=[], observed={}, errors=[])
    bodies = []
    fixture = electron = server = None

    def check(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            title = request_source(body) == 'thread_title'
            if not title:
                bodies.append(body)
            text = json.dumps({'title': 'T-167'}) if title else 'T167 已收到。'
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('x-codex-primary-used-percent', '94')
            self.send_header('x-codex-primary-window-minutes', '10080')
            self.send_header('x-codex-primary-reset-at', str(int(time.time()) + 86400))
            self.end_headers()
            for sequence, (name, payload) in enumerate(message_events(text, body.get('model', MODEL))):
                self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
            self.wfile.flush()

    try:
        patches = []
        if args.scenario == 'dialog-open':
            patches.append(('src/panes.ts', HIDE, ''))
        if args.mutant == 'no-start-check':
            patches.append(('src/panes.ts', START_CHECK, 'return;'))
        fixture = Fixture('t167-', lambda _: (_ for _ in ()).throw(AssertionError('禁止 Claude 模型请求')),
                          revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        codex_home = fixture.home / '.codex'
        (codex_home / 'rules').mkdir(parents=True)
        (codex_home / 'config.toml').write_text('model_provider="t167"\ncli_auth_credentials_store="file"\n'
            f'[projects.{json.dumps(str(fixture.repo))}]\ntrust_level="trusted"\n'
            '[model_providers.t167]\nname="T167 fixture"\n'
            f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
        (codex_home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                     'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
        original_cli = fixture.run_cli

        def configured_cli(*arguments):
            if arguments[0] == 'daemon_start':
                path = fixture.dir / 'launch-config.json'
                config = json.loads(path.read_text(encoding='utf-8'))
                config.update(codex_bin=args.codex, codex_home=str(codex_home))
                path.write_text(json.dumps(config), encoding='utf-8')
            return original_cli(*arguments)

        fixture.run_cli = configured_cli
        fixture.start(args.claude, {'README.md': 'T-167 fixture\n', 'check.py': 'raise SystemExit(0)\n'})
        task = 'T-X'
        card = fixture.out / 'T-X.json'
        card.write_text(json.dumps(dict(id=task, source=None, goal='确认收到回执', non_goals=['不改文件'],
            paths=dict(allow=['note.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Codex', model=MODEL, effort='high'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        for result in [fixture.request('card_save', fixture.terminal, task=task, card=str(card), expected_version=0),
                       fixture.request('create', fixture.terminal, task=task, project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)]:
            assert result.get('ok'), result
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        launch = attempt['runtime_identity']['launch']
        thread = attempt['thread_id']
        report['observed']['launch_argv'] = fixture.request('launch_show', fixture.operator, launch=launch)['launch']['argv']

        def events():
            return [event for event in fixture.request('orchestration_events', task='demo+' + task)['events'] if event['launch'] == launch]

        fixture.wait('第一回合完成并空闲', lambda: bodies and fixture.request('pane_status', thread=thread).get('state') == 'idle', 120)
        electron = Electron(fixture, 't167-' + fixture.dir.name[5:])
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        selector = '[data-agent-launch="' + launch + '"]'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        before = len(bodies)
        sent = fixture.request('pane_dispatch', fixture.operator, thread=thread, body=RECEIPT)
        assert sent.get('ok'), sent
        dispatch_id = sent['dispatch']['id']
        started = any(RECEIPT in json.dumps(body, ensure_ascii=False) for body in bodies[before:])
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not started:
            time.sleep(0.5)
            started = any(RECEIPT in json.dumps(body, ensure_ascii=False) for body in bodies[before:])
        if started:
            fixture.wait('回执回合结束', lambda: fixture.request('pane_status', thread=thread).get('state') == 'idle', 60)
        else:
            # Past the backend's 20 s start deadline; the UI polls once a second.
            time.sleep(3)
        mine = events()
        submitted = [event for event in mine if event['type'] == 'turn_submitted' and event['data'].get('dispatch') == dispatch_id]
        after = submitted[0]['seq'] if submitted else 1 << 62
        starts = [event for event in mine if event['type'] == 'turn_start_signal' and event['seq'] > after]
        missing = [event for event in mine if event['type'] == 'turn_start_missing' and event['data'].get('dispatch') == dispatch_id]
        settings = [event['data']['record']['payload']['thread_settings'] for event in mine if event['type'] == 'native_record' and
                    event['data']['record'].get('payload', {}).get('type') == 'thread_settings_applied']
        pastes = [event for event in mine if event['type'] == 'paste_intent' and event['data'].get('dispatch') == dispatch_id]
        intents = [event for event in mine if event['type'] == 'turn_submit_intent' and event['data'].get('dispatch') == dispatch_id]
        pane = fixture.request('pane_status', thread=thread)
        agent = next(row for row in fixture.request('sidebar_snapshot')['agents'] if row['id'] == launch)
        pane_selector = '.pane[data-launch-id="' + launch + '"]'
        dom = electron.evaluate(f'''(()=>{{const p=document.querySelector({json.dumps(pane_selector)});
            return {{header:p?.querySelector('.pane-header')?.textContent, notice:p?.querySelector('[data-start-missing][role=status]')?.textContent ?? null,
              sidebar:document.querySelector({json.dumps(selector)})?.innerText}}}})()''')
        screen = electron.evaluate(f'''(()=>{{const rows=[...document.querySelectorAll({json.dumps(pane_selector + ' .xterm-rows > div')})];
            return rows.map(r=>r.textContent).filter(Boolean).slice(-20)}})()''')
        shot = args.summary.with_suffix('.png')
        electron.screenshot(shot)
        report['screenshot'] = str(shot)
        report['observed'].update(started=started, receipt_submitted=submitted, starts_after=[e['seq'] for e in starts], missing=missing,
                                  thread_settings=[dict(model=s.get('model'), effort=s.get('reasoning_effort')) for s in settings],
                                  requests=[dict(model=b.get('model'), effort=(b.get('reasoning') or {}).get('effort')) for b in bodies],
                                  pastes=len(pastes), submit_intents=len(intents), pane=dict(state=pane.get('state'), start_missing=pane.get('start_missing')),
                                  sidebar=dict(state=agent.get('state'), start_missing=agent.get('start_missing')), dom=dom, screen_tail=screen)
        switched = [s for s in settings if s.get('model') != MODEL or s.get('reasoning_effort') != 'high']
        check('receipt_written_once_no_resend', len(pastes) == 1 and len(intents) == 1, dict(pastes=len(pastes), intents=len(intents)))
        if args.scenario == 'receipt':
            check('receipt_turn_started', started and bool(starts), dict(started=started, starts=len(starts)))
            check('worker_model_and_effort_unchanged', not switched, switched)
            check('no_start_missing_after_start', not missing and not pane.get('start_missing'), missing)
            # Red as in T-164: the receipt was recorded submitted, no turn started, and the model was switched.
            report['red_reproduced'] = bool(submitted and not started and not starts and switched)
        else:
            check('turn_not_started_while_dialog_open', not started and not starts, dict(started=started))
            check('start_missing_recorded', len(missing) == 1, missing)
            check('pane_status_says_not_started', pane.get('start_missing') is True, pane.get('start_missing'))
            check('sidebar_says_not_started', agent.get('start_missing') is True and '回合未开始' in (dom.get('sidebar') or ''), dom.get('sidebar'))
            check('pane_header_says_not_started', '回合未开始' in (dom.get('header') or '') and bool(dom.get('notice')), dom)
        report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['errors'].append(dict(error=str(error), traceback=traceback.format_exc()))
    finally:
        for name, resource in [('electron', electron), ('fixture', fixture)]:
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    report['status'] = 'INCOMPLETE'
                    report['errors'].append(dict(cleanup=name, error=str(error)))
        if server:
            server.shutdown()
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary),
                          failed=[c['name'] for c in report['checks'] if not c['passed']], errors=[e.get('error') for e in report['errors']]), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
