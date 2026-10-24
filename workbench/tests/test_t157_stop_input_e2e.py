"""T-157 修前探针：真实 Electron / 后台 / PTY / Claude CLI，本地脚本化 Messages 接口。

失败方式（先列再写）：
1. Stop 批次的 submit 正在核对身份时，人工 Enter 换掉 prompt，旧请求被拒。
2. 拒绝仅排入终端反馈，侧栏与窗格头没有原因、最后确定事实或恢复入口。
3. 探针把未命中竞态、启动失败或脚本化模型错误算成产品红态。
4. 复跑覆盖旧证据，或把本地脚本化 API 回合冒称为真实供应商模型回合。

期望来自 T-157 Acceptance：原因与可操作恢复须在真实界面可见，绑定原 attempt。
目前只调查红态；恢复的具体动作须等 DESIGN-QUESTION.md 裁定，尚无恢复验收。
--revision 只选择产品源码；--mutant submit-never-active 是始终拒绝 worker 的已知坏实现。
不修补时序、不暂停进程、不修改产品状态；只读观察 relay journal 后经 Electron 输入桥提交说明。
若未命中 worker_not_active 则为 INCOMPLETE，保留该次现场，不自动重试。
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

from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory


ROOT = Path(__file__).resolve().parents[2]
NOTE = '补充说明：保持任务范围不变，完成原任务即可。'
# A persistent CDP connection avoids starting a client after the narrow race begins.
# SQLite is read-only; all input uses the same Electron bridge as xterm.onData.
WATCHER = r"""
import { DatabaseSync } from 'node:sqlite';
import { writeFileSync } from 'node:fs';
const [port, database, launch, paneKey, ready, output, note] = process.argv.slice(1);
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
if (!page) throw new Error('Electron page absent');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve,reject) => {ws.onopen=resolve;ws.onerror=reject;});
let next=0; const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);pending.get(m.id)?.(m);pending.delete(m.id);};
const send=(method,params)=>new Promise((resolve,reject)=>{
  const id=++next, timer=setTimeout(()=>reject(new Error('CDP timeout')),10000);
  pending.set(id,m=>{clearTimeout(timer);m.error?reject(new Error(JSON.stringify(m.error))):resolve(m.result);});
  ws.send(JSON.stringify({id,method,params}));
});
const db=new DatabaseSync(database,{readOnly:true});
const query=db.prepare("SELECT key,input FROM relay_requests WHERE launch=? AND json_extract(input,'$.command')='submit' ORDER BY rowid LIMIT 1");
writeFileSync(ready,'ready\n',{flag:'wx'});
const deadline=Date.now()+20000;
let row;
while (!(row=query.get(launch))) {
  if(Date.now()>deadline)throw new Error('submit relay intent not observed');
  await new Promise(resolve=>setTimeout(resolve,1));
}
const sentAt=new Date().toISOString();
const result=await send('Runtime.evaluate',{expression:`window.a2a.input(${JSON.stringify(paneKey)},${JSON.stringify(note+'\r')})`,awaitPromise:true,returnByValue:true});
writeFileSync(output,JSON.stringify({relay:row,sent_at:sentAt,result},null,2)+'\n',{flag:'wx'});
db.close();ws.close();
if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['submit-never-active'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  vendor_model_turns=0, model_backend='local scripted Messages endpoint',
                  red_reproduced=False, checks=[], observed={}, errors=[])
    fixture = electron = watcher = watcher_log = None
    finish_ready, allow_finish = threading.Event(), threading.Event()

    def plan(body):
        text, cwd = prompt_text(body), working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1)
        submit = submit.replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        steps = [('Write', dict(file_path=f'{cwd}/answer.txt', content='原任务草稿\n')),
                 ('Bash', dict(command='git add answer.txt', description='stage candidate')),
                 ('Bash', dict(command='git commit -q -m ' + quote('T-157 isolated draft'), description='commit candidate')),
                 ('Bash', dict(command=submit, description='queue explicit submit'))]
        count = sum(1 for message in body['messages'] if message['role'] == 'assistant' and isinstance(message['content'], list)
                    and any(isinstance(part, dict) and part.get('type') == 'tool_use' for part in message['content']))
        if count >= len(steps) and not allow_finish.is_set():
            finish_ready.set()
            assert allow_finish.wait(60), '未在期限内准备好 Electron 输入观察器'
        return cwd, steps, '已完成原任务。'

    def record(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        patches = [] if not args.mutant else [('src/panes.ts',
            'info.leader && !info.failed && pane.state === "busy" && pane.claudePromptId === turn', 'false')]
        fixture = Fixture('t157-stop-input-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-157 一次性仓库\n',
            'check.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == "原任务草稿\\n"\n'})
        electron = Electron(fixture, 't157-' + fixture.dir.name)
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        task = 'T-157-probe'
        fixture.card(task, 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write',
                                     model='claude-haiku-5-5', effort='low')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        report['observed']['attempt'] = attempt
        fixture.wait('worker 请求已排队、尚未结束回合', finish_ready.is_set, 150)
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        pane_selector = '.pane[data-launch-id=' + json.dumps(launch) + ']'
        expression = f'document.querySelector({json.dumps(pane_selector)})'
        pane_key = electron.until('worker 窗格可输入', f'{expression}?.dataset.inputEnabled === "true" && {expression}.dataset.paneKey')
        ready, outcome = fixture.out / 'watcher-ready', fixture.out / 'watcher.json'
        watcher_log = (fixture.out / 'watcher.log').open('x', encoding='utf-8')
        watcher = subprocess.Popen(['node', '--input-type=module', '-e', WATCHER, str(electron.port),
            str(fixture.state / 'state.sqlite3'), launch, pane_key, str(ready), str(outcome), NOTE],
            stdout=watcher_log, stderr=subprocess.STDOUT, start_new_session=True)
        fixture.wait('CDP 观察器准备好', ready.exists, 15)
        allow_finish.set()
        assert watcher.wait(30) == 0, (fixture.out / 'watcher.log').read_text(encoding='utf-8')
        report['observed']['input_watcher'] = json.loads(outcome.read_text(encoding='utf-8'))

        def events():
            return fixture.request('orchestration_events', task='demo+' + task)['events']

        def result_seen():
            return [event for event in events() if event['launch'] == launch and event['type'] in ('relay_processed', 'relay_rejected')]

        results = fixture.wait('submit 有明确回执', result_seen, 30)
        rejected = [event for event in results if event['type'] == 'relay_rejected' and
                    event['data'].get('result', {}).get('error') == 'worker_not_active']
        trace = events()
        report['observed']['timeline'] = [event for event in trace if event['launch'] == launch and event['type'] in (
            'turn_end_signal', 'relay_received', 'relay_processed', 'relay_rejected', 'stop_not_matched',
            'turn_submit_intent', 'turn_start_signal', 'terminal_input_written', 'pane_idle', 'stop_transfer_failed')]
        report['observed']['gate_events'] = fixture.request('events', fixture.operator, task='demo+' + task)['events']
        record('submit_rejected_worker_not_active', bool(rejected), results)
        if not rejected:
            raise RuntimeError('未命中指定竞态；本次不是 T-157 缺陷红态，不自动重试')
        # Let the renderer consume its normal snapshot/side-bar refresh once. This is observation, not a retry.
        time.sleep(2)
        report['observed']['pane'] = fixture.request('pane_status', thread=attempt['thread_id'])
        report['observed']['task'] = fixture.request('status', fixture.operator, task='demo+' + task)['task']
        report['observed']['sidebar'] = fixture.request('sidebar_snapshot')
        report['observed']['dom'] = electron.evaluate(f'''(() => {{const p={expression};
            return {{pane:p?.innerText, header:p?.querySelector('.pane-state')?.textContent,
            sidebar:document.querySelector({json.dumps(selector)})?.innerText,
            actions:[...(p?.querySelectorAll('button')??[])].map(b=>b.textContent)}};}})()''')
        screenshot = args.summary.with_suffix('.png')
        assert not screenshot.exists(), '保留既有截图'
        electron.screenshot(screenshot)
        report['screenshot'] = str(screenshot)
        menu = pane_selector + ' .pane-menu-trigger'
        electron.evaluate(f'document.querySelector({json.dumps(menu)}).click()')
        report['observed']['menu'] = electron.evaluate('[...document.querySelectorAll("[role=menuitem]")].map(b=>b.textContent)')
        menu_shot = args.summary.with_name(args.summary.stem + '-menu.png')
        assert not menu_shot.exists(), '保留既有菜单截图'
        electron.screenshot(menu_shot)
        report['menu_screenshot'] = str(menu_shot)
        human = [event for event in report['observed']['gate_events'] if event['type'] == 'human_intervention']
        record('human_intervention_bound_original_attempt', any(event['attempt'] == attempt['attempt_id'] for event in human))
        received = next(event for event in trace if event['type'] == 'relay_received' and
                        event['data'].get('key') == rejected[0]['data']['key'])
        record('input_intersects_original_stop_batch', any(received['seq'] < event['seq'] < rejected[0]['seq'] and
               event['type'] == 'turn_submit_intent' and event['data'].get('source') == 'user'
               for event in trace))
        record('same_attempt_no_candidate', report['observed']['task']['current_attempt']['attempt_id'] == attempt['attempt_id'] and
               report['observed']['task']['candidate_commit'] is None)
        agent = next(row for row in report['observed']['sidebar']['agents'] if row['id'] == launch)
        record('sidebar_unknown_header_busy', agent['state'] == 'unknown' and report['observed']['dom']['header'] == '忙',
               dict(sidebar=agent['state'], header=report['observed']['dom']['header']))
        report['red_reproduced'] = all(check['passed'] for check in report['checks'])
        # Terminal scrollback can contain raw feedback; it does not prove persistent UI explanation/recovery.
        dom = report['observed']['dom']
        record('persistent_ui_explains_rejection', any(word in (dom.get('header') or '') + (dom.get('sidebar') or '')
               for word in ['交付被拒', '交付暂停', 'worker_not_active']))
        record('ui_has_explicit_recovery_action', any('交付' in (label or '') and any(word in label for word in ['恢复', '核对', '重新'])
               for label in dom['actions'] + report['observed']['menu']))
        report['status'] = 'PASS' if all(check['passed'] for check in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['errors'].append(dict(error=str(error), traceback=traceback.format_exc()))
    finally:
        allow_finish.set()
        if watcher and watcher.poll() is None:
            watcher.terminate()
            watcher.wait(10)
        if watcher_log:
            watcher_log.close()
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
