"""T-161：真实 Electron、后台、门禁及受控 PTY；不调用模型。

失败方式（期望来自 T-161 与 F02/F07）：
1. 查看 reviewer 或失效 attempt 的 worker，回放焦点模式后出现输入错误或申请输入焦点。
2. 把所有输入错误一起吞掉，可写 worker 的真实输入拒绝不再显示。
3. 已确认主控的窗格头只有普通终端；隐藏侧栏、重命名后丢失角色或载体。
4. 未确认/已释放角色的普通终端被误标主控，或影响 T-159 的普通终端标签。
--revision 在指定源码版本上运行；--mutant 在隔离副本中注入已知坏实现。
--summary 必须是新路径；夹具保留，交主控按 T-088 归档。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripted_claude import Electron, Fixture, ROOT


PEER = r'''import json, os, re, subprocess, sys, uuid
from pathlib import Path
settings = json.loads(os.environ['T093_FIXTURE_SETTINGS'])
prompt_id = str(uuid.uuid4())
def hook(name, **extra):
    command = settings['hooks'][name][0]['hooks'][0]['command']
    payload = dict(hook_event_name=name, session_id=os.environ['A2A_NATIVE_SESSION'],
                   cwd=os.getcwd(), prompt_id=prompt_id, **extra)
    result = subprocess.run(command, shell=True, input=json.dumps(payload), text=True, capture_output=True)
    print(result.stdout, result.stderr, flush=True)
    assert result.returncode == 0, (name, result.returncode)
if sys.argv[2] == '0':
    hook('SessionStart', source='startup')
    print('\x1b[?1004hT161_FOCUS_OUTPUT', flush=True)
else:
    text = sys.argv[1]
    hook('UserPromptSubmit', prompt=text)
    if os.environ['A2A_ROLE'] == 'worker' and os.environ['A2A_TASK'].endswith('+T-review'):
        Path('T-review.txt').write_text('candidate\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'T-review.txt'], check=True)
        subprocess.run(['git', 'commit', '-m', 'T161 controlled candidate'], check=True)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        submit = submit.replace('FULL_COMMIT_SHA', commit)
        subprocess.run(submit, shell=True, check=True)
    if os.environ['A2A_ROLE'] != 'reviewer':
        hook('Stop', stop_hook_active=False)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['readonly-observation', 'missing-role', 'suppress-input-errors'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请换新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], observed={}, model_calls=0,
                  code_version=subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip())
    fixture = electron = None

    def check(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        patches = [('app/renderer.tsx', 'term.open(mount.current!);',
                    'term.open(mount.current!); (mount.current as any).__t161Terminal = term;')]
        if args.mutant == 'readonly-observation':
            patches.append(('app/renderer.tsx', "type === 'focus-mode-intercept' && writable", "type === 'focus-mode-intercept'"))
        elif args.mutant == 'missing-role':
            patches.append(('app/renderer.tsx', "shell && confirmedRole ? '普通终端 · ' + confirmedRole : role", 'role'))
        elif args.mutant == 'suppress-input-errors':
            patches.append(('app/renderer.tsx', 'setInputError(`输入尚未确认，已停止发送：${String(failure)}`);', 'setInputError(null);'))
        fixture = Fixture('t161-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')),
                          revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        fake = fixture.dir / 'controlled-claude'
        subprocess.run(['cc', str(ROOT / 'workbench/tests/t093_fake_claude.c'), '-o', str(fake)], check=True, capture_output=True)
        (fixture.dir / 'fake-login-peer.py').write_text(PEER, encoding='utf-8')
        fixture.start(str(fake), {'README.md': 'T161 controlled PTY\n', 'check.py': 'raise SystemExit(0)\n'})
        workers = {}
        for task in ('T-review', 'T-history', 'T-input'):
            fixture.card(task, task + '.txt', 'check.py')
            dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            assert dispatched.get('ok'), dispatched
            workers[task] = dispatched['attempt']['runtime_identity']['launch']
            fixture.wait(task + ' 回合完成', lambda task=task: fixture.request('workbench_snapshot', task='demo+'+task,
                         launch=workers[task]).get('pane', {}).get('state') == 'idle', 40)
        fixture.wait('候选完成 Stop 交付', lambda: fixture.request('status', fixture.operator, task='demo+T-review')['task']['state'] == 'submitted', 30)
        verified = fixture.request('verify', fixture.terminal, task='T-review')
        assert verified.get('ok'), verified
        reviewer = fixture.wait('门禁启动审查员', lambda: next((a['id'] for a in fixture.request('sidebar_snapshot')['agents']
                               if a['role'] == 'reviewer'), None), 40)
        revoked = fixture.request('revoke', fixture.terminal, task='T-history', reason='T161 historical-view fixture')
        assert revoked.get('ok'), revoked
        report['observed']['launches'] = dict(workers=workers, reviewer=reviewer)
        electron = Electron(fixture, fixture.dir.name)
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')

        def click(selector):
            electron.until('可点击 ' + selector, f'!!document.querySelector({json.dumps(selector)})')
            electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')

        def ready(launch):
            return electron.until('窗格恢复 ' + launch, f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');
                return p&&p.getClientRects().length&&p.querySelector('[data-restoring=false]')&&p.dataset.paneKey}})()''')

        def facts(launch):
            return electron.evaluate(f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');
                return {{header:p.querySelector('.pane-header').textContent, input:p.dataset.inputEnabled,
                errors:[...p.querySelectorAll('[role=alert]')].map(e=>e.textContent), focused:p.contains(document.activeElement),
                text:p.querySelector('.terminal-mount').__t161Terminal.buffer.active.getLine(0)?.translateToString(true)}}}})()''')

        def shot(name):
            path = args.summary.parent / (args.summary.stem + '-' + name + '.png')
            electron.screenshot(path)
            report.setdefault('screenshots', []).append(str(path))

        click('[data-project-id="demo"]')
        # Both output histories contain a real PTY 1004 mode sequence before selecting them.
        for kind, launch in [('reviewer', reviewer), ('history', workers['T-history'])]:
            raw = fixture.request('pane_output', launch=launch, offset=0, max_bytes=65536)
            import base64
            check(kind + '_fixture_has_focus_mode', b'\x1b[?1004h' in base64.b64decode(raw['data_base64']))
            click('[data-agent-launch="' + launch + '"]')
            key = ready(launch)
            observed = facts(launch)
            report['observed'][kind] = observed
            shot(kind)
            check(kind + '_readonly', observed['input'] == 'false', observed)
            check(kind + '_view_has_no_input_error', not observed['errors'], observed)
            check(kind + '_no_requested_input_focus', not observed['focused'], observed)
            check(kind + '_no_input_credential', not electron.evaluate(f'window.a2a.snapshot({json.dumps(key)})').get('window_id'))

        controller = fixture.terminal_launch
        click('[data-agent-launch="' + controller + '"]')
        controller_key = ready(controller)
        click('[aria-label="隐藏侧栏"]')
        initial = facts(controller)
        check('confirmed_executor_header_with_sidebar_hidden', '普通终端' in initial['header'] and '执行主控' in initial['header'], initial)
        shot('controller-sidebar-hidden')
        # Renaming is a real pane operation; it must leave both identity labels visible.
        click(f'.pane[data-launch-id="{controller}"] [aria-label="窗格菜单"]')
        electron.evaluate('[...document.querySelectorAll(".pane-menu button")].find(b=>b.textContent==="重命名窗格").click()')
        electron.evaluate('(()=>{const i=document.querySelector(".pane-rename input");const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;setter.call(i,"本地调度");i.dispatchEvent(new Event("input",{bubbles:true}));})()')
        electron.evaluate('[...document.querySelectorAll("button")].find(b=>b.textContent==="保存名称").click()')
        electron.until('名称已保存', f'document.querySelector(\'.pane[data-launch-id="{controller}"] .pane-header strong\')?.textContent==="本地调度"')
        renamed = facts(controller)
        check('renamed_controller_keeps_carrier_and_role', all(s in renamed['header'] for s in ('本地调度', '普通终端', '执行主控')), renamed)
        released = fixture.request('role_release', fixture.terminal)
        assert released.get('ok'), released
        electron.until('侧栏角色释放', '(async()=>!(await window.a2a.sidebar()).agents.some(a=>a.id===' + json.dumps(controller) + '))()')
        # Wait for the normal catalog polling to show the terminal as ordinary.
        electron.until('普通终端目录更新', f'!!document.querySelector(\'.project-terminals [data-agent-launch="{controller}"]\')')
        ordinary = facts(controller)
        check('released_role_not_shown', '执行主控' not in ordinary['header'] and '普通终端' in ordinary['header'], ordinary)
        click('[aria-label="显示侧栏"]')

        # A real IPC input rejection, without replacing the bridge or hiding the error.
        launch = workers['T-input']
        click('[data-agent-launch="' + launch + '"]')
        key = ready(launch)
        electron.until('可写输入已启用', f'document.querySelector(\'.pane[data-launch-id="{launch}"]\')?.dataset.inputEnabled==="true"')
        outcome = electron.evaluate(f'(async()=>(await window.a2a.snapshot({json.dumps(key)})).input_enabled)()')
        assert outcome, '输入失败正例必须先可写'
        electron.evaluate(f'''(()=>{{const t=document.querySelector('.pane[data-launch-id="{launch}"] .terminal-mount').__t161Terminal;
            t.input('x'.repeat(1024*1024+1),true)}})()''')
        electron.until('真实输入失败提示', f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');
            return p.querySelector('[role=alert]')||p.dataset.inputEnabled==='false'}})()''')
        rejected = facts(launch)
        check('real_input_failure_still_visible', any('输入尚未确认' in e for e in rejected['errors']), rejected)
        shot('real-input-rejected')
        check('zero_model_requests', fixture.api.snapshot()['requests'] == 0, fixture.api.snapshot())
        report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
                    report['status'] = 'INCOMPLETE'
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
