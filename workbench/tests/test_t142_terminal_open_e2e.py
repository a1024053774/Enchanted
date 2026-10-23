"""T-142：批准的项目主控开普通终端，期望来自任务卡。
失败方式（先列再写）：
1. terminal_open 仍被 role_command_not_scoped 拒绝，或 CLI 不识别命名参数。
2. 未批准的会话能开终端，或已批准角色能指定另一个项目。
3. cwd 越界、同前缀的兄弟目录、符号链接逃逸被放行。
4. 主目录、子目录或额外目录不能开，返回 id 不对应真实 shell/cwd。
5. 新终端没有出现在界面项目层，混进任务层，或点开后的 pwd 不对。
6. 真实 Claude 的 a2a request 没有经过界面批准，或其调用并未执行。
7. Claude Code 2.1.309 默认进入 auto mode，计费说明挡住 Bash；设 defaultMode="default" 后又会弹
   “Make auto mode your default permission mode?” 并吃掉任务输入。夹具须同时设置 default 权限模式和
   .claude.json 的 hasSeenAutoDefaultNudge=true，不发 Enter/Esc 关闭这些对话框。
--backend-only 是沙箱内的真实后台/PTY/CLI 契约探针，不替代默认 Electron + Claude 验收。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, quote  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--backend-only', action='store_true')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['cwd-unchecked'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], observed={}, revision=args.revision, mutant=args.mutant,
                  coverage='后台/PTY/CLI' if args.backend_only else '后台/PTY/CLI/Claude/Electron')
    fixture = None
    electron = None
    commands = []

    def plan(body):
        return 'controller', [('Bash', dict(command='a2a request executor', timeout=600000, description='request role')),
                              *[('Bash', dict(command=line, description='open project terminal')) for line in commands]], 'T-142 完成。'

    patches = [('src/daemon.ts', 'if (!withinProject) throw new Refusal("terminal_cwd_outside_project");', '')] if args.mutant else []

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def result(path):
        return json.loads(path.read_text(encoding='utf-8'))

    def open_input(launch, project='demo'):
        opened = fixture.request('window_open', fixture.operator, launch=launch, project=project)
        assert opened['ok'], opened
        return dict(launch=launch, identity=opened['identity'], sequence=0)

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def cli_call(term, line, path):
        type_in(term, f'{line} > {quote(str(path))}\r')
        fixture.wait('CLI 回执', lambda: path.exists() and path.stat().st_size, 30)
        return result(path)

    try:
        fixture = Fixture('t142-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        fixture.start(args.claude, {'README.md': 'T-142 fixture\n', 'check.py': 'pass\n'})
        extra, outside, child = fixture.dir / 'extra', fixture.dir / 'demo-sibling', fixture.repo / 'child'
        for path in (extra, outside, child):
            path.mkdir()
        escape = fixture.repo / 'escape'
        escape.symlink_to(outside, target_is_directory=True)
        assert fixture.request('project_settings_save', fixture.operator, project='demo', extra_directories=[str(extra)])['ok']
        fixture.card('T-1', 'a.txt', 'check.py')
        controller = open_input(fixture.terminal_launch)
        destinations = [('main', fixture.repo), ('extra', extra), ('child', child)]
        paths = {name: fixture.out / f'{name}.json' for name, _ in destinations}
        commands.extend(f'a2a call {quote(json.dumps(dict(command="terminal_open", cwd=str(cwd))))} > {quote(str(paths[name]))}' if name == 'main' else
                        f'a2a call terminal_open --cwd {quote(str(cwd))} > {quote(str(paths[name]))}' for name, cwd in destinations)
        if args.backend_only:
            for line in commands:
                type_in(controller, line + '\r')
        else:
            assert fixture.request('role_release', fixture.terminal)['ok']
            config = fixture.home / '.claude.json'
            config.write_text(json.dumps({'hasCompletedOnboarding': True, 'hasSeenAutoDefaultNudge': True, 'theme': 'dark',
                                          'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
            (fixture.home / '.claude').mkdir(exist_ok=True)
            permissions = {'defaultMode': 'default', 'allow': ['Bash(a2a request:*)', 'Bash(a2a call:*)']}
            (fixture.home / '.claude/settings.json').write_text(json.dumps({'permissions': permissions}), encoding='utf-8')
            report['observed']['fixture_permissions'] = permissions
            electron = Electron(fixture, 't142-' + fixture.dir.name[5:])
            electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
            type_in(controller, 'claude --model claude-haiku-5-5\r')

            def ready():
                raw = (fixture.state / 'traces' / controller['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')
                screen = re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))
                return 'ClaudeCodev' in screen and '❯' in screen[screen.index('ClaudeCodev'):]

            fixture.wait('真实 Claude 输入框', ready, 90)
            type_in(controller, 'T-142 请申请执行主控并按要求开项目终端')
            time.sleep(1)
            type_in(controller, '\r')
            card = electron.until('执行主控申请', 'document.querySelector("[data-role-request]")?.dataset.roleRequest ?? null', 90)
            electron.until('批准', f'(()=>{{const b=[...document.querySelectorAll(\'[data-role-request="{card}"] button\')].find(b=>b.textContent==="批准");if(!b||b.disabled)return false;b.click();return true}})()', 30)
            fixture.wait('主控已批准', lambda: fixture.request('terminal_whoami', fixture.terminal).get('role') == 'executor', 30)
            check('real_claude_requested_and_ui_approved', True)
        for name, cwd in destinations:
            path = paths[name]
            fixture.wait(name + ' 开终端回执', lambda: path.exists() and path.stat().st_size, 120)
            value = result(path)
            report['observed'][name] = value
            check(name + '_opened', value.get('ok') is True, value)
            launch = value['launch']
            check(name + '_ordinary_project_terminal', launch['project'] == 'demo' and launch['role'] == 'shell' and
                  all(launch[key] is None for key in ('task', 'attempt', 'session', 'fence')) and launch['worktree'] == str(cwd), launch)
            shell = open_input(launch['id'])
            pwd = fixture.out / f'{name}-pwd.txt'
            type_in(shell, f'pwd > {quote(str(pwd))}\r')
            fixture.wait(name + ' pwd', lambda: pwd.exists() and pwd.stat().st_size, 30)
            check(name + '_actual_pwd', pwd.read_text(encoding='utf-8').strip() == str(cwd))
            catalog = fixture.request('sidebar_snapshot')
            check(name + '_project_catalog_only', any(t['id'] == launch['id'] and t['project'] == 'demo' for t in catalog['terminals']) and
                  not any(t['id'] == launch['id'] for t in catalog['agents']), catalog['terminals'])
            task_layout = fixture.request('pane_layout', task='demo+T-1')
            check(name + '_not_in_task_layout', not any(t['launch'] == launch['id'] for t in task_layout['panes']))
            if electron:
                selector = f'.project-terminals .agent-row[data-agent-launch="{launch["id"]}"]'
                electron.until(name + ' 项目层终端出现', f'!!document.querySelector({json.dumps(selector)})', 30)
                electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
                electron.until(name + ' 界面标识一致', f'(async()=>Object.values((await window.a2a.selection()).launches).includes({json.dumps(launch["id"])}))()', 30)
                ui_pwd = fixture.out / f'{name}-ui-pwd.txt'
                electron.evaluate(f'(async()=>{{var s=await window.a2a.selection(); var k=Object.keys(s.launches).find(k=>s.launches[k]==={json.dumps(launch["id"])}); await window.a2a.input(k,{json.dumps("pwd > " + quote(str(ui_pwd)) + chr(13))});}})()')
                fixture.wait(name + ' 界面终端 pwd', lambda: ui_pwd.exists() and ui_pwd.stat().st_size, 30)
                check(name + '_ui_pwd', ui_pwd.read_text(encoding='utf-8').strip() == str(cwd))
                electron.screenshot(fixture.out / f'{name}-terminal.png')
        for label, cwd in [('sibling', outside), ('symlink', escape)]:
            value = fixture.request('terminal_open', fixture.terminal, cwd=str(cwd))
            report['observed'][label] = value
            check(label + '_refused', value.get('error') == 'terminal_cwd_outside_project', value)
        # An unapproved terminal uses the real CLI and carries its own terminal identity.
        anonymous = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        value = cli_call(open_input(anonymous), f'a2a call terminal_open --cwd {quote(str(fixture.repo))}', fixture.out / 'unapproved.json')
        check('unapproved_refused', value.get('error') == 'approved_role_required', value)
        # This controller belongs to demo. another is a real opened project with its own directory.
        assert fixture.request('project_open', fixture.operator, repo=str(outside))['ok']
        other = fixture.request('terminal_open', fixture.terminal, project='demo-sibling', cwd=str(outside))
        check('approved_foreign_project_refused', other.get('error') == 'role_project_mismatch', other)
        report['observed']['foreign_project'] = other
        foreign = fixture.run_cli('shell_start', '--project', 'demo-sibling', '--cwd', str(outside))['launch']['id']
        foreign_term = open_input(foreign, 'demo-sibling')
        granted = fixture.out / 'foreign-role.json'
        type_in(foreign_term, f'a2a request executor > {quote(str(granted))}\r')
        pending = fixture.wait('其他项目主控申请', lambda: [r for r in fixture.request('sidebar_snapshot')['role_requests'] if r['launch'] == foreign], 30)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        fixture.wait('其他项目角色已批准', lambda: granted.exists() and granted.stat().st_size, 30)
        assert result(granted)['ok'], result(granted)
        line = 'a2a call ' + quote(json.dumps(dict(command='terminal_open', project='demo', cwd=str(fixture.repo))))
        other_to_demo = cli_call(foreign_term, line, fixture.out / 'foreign-to-demo.json')
        check('other_approved_controller_cannot_open_this_project', other_to_demo.get('error') == 'role_project_mismatch', other_to_demo)
        report['observed']['other_to_demo'] = other_to_demo
        if electron:
            report['observed']['scripted_api'] = fixture.api.snapshot()
            check('real_claude_executed_open_calls', len(fixture.api.results.get('controller', [])) >= 3, fixture.api.snapshot())
        report['status'] = 'PASS'
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
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
