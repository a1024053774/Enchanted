"""T-142 Claude Code Bash 权限探针，不作产品验收。
失败方式：CLI 未运行、脚本化接口未发出指定命令、后台身份失效、print 模式未报告权限拒绝、
两个输入除重定向外还存在差异。以上均为 INCOMPLETE，不能证明重定向是原因。
同一隔离 home/settings 和项目终端角色，比较同一个 a2a call 的裸命令与向 out/ 重定向版本。
仅记录结构化 permission_denials、工具返回、后台新终端和目标文件；不发送确认按键。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture, prompt_text, quote  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, cases={})
    fixture = None
    commands = {}

    def plan(body):
        keys = [key for key in commands if prompt_text(body).rstrip().endswith(key)]
        assert len(keys) == 1, prompt_text(body)
        key = keys[0]
        return key, [('Bash', dict(command=commands[key], description='T-142 permission probe'))], '探针结束。'

    try:
        fixture = Fixture('t142-probe-', plan)
        report['fixture'] = str(fixture.dir)
        report['cli_version'] = subprocess.check_output([args.claude, '--version'], text=True).strip()
        fixture.start(args.claude, {'README.md': 'T-142 permission probe\n'})
        config = {'hasCompletedOnboarding': True, 'hasSeenAutoDefaultNudge': True, 'theme': 'dark',
                  'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}
        permissions = {'defaultMode': 'default', 'allow': ['Bash(a2a request:*)', 'Bash(a2a call:*)'],
                       'additionalDirectories': [str(fixture.out.resolve())]}
        (fixture.home / '.claude.json').write_text(json.dumps(config), encoding='utf-8')
        (fixture.home / '.claude').mkdir(exist_ok=True)
        (fixture.home / '.claude/settings.json').write_text(json.dumps({'permissions': permissions}), encoding='utf-8')
        report['permissions'] = permissions
        bare = 'a2a call ' + quote(json.dumps(dict(command='terminal_open', cwd=str(fixture.repo))))
        redirected = fixture.out / 'main.json'
        commands.update(T142_PROBE_A=bare, T142_PROBE_B=bare + ' > ' + quote(str(redirected)))
        report['inputs'] = commands
        window = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project='demo')
        assert window['ok'], window
        for sequence, key in enumerate(commands, 1):
            before = {t['id'] for t in fixture.request('sidebar_snapshot')['terminals']}
            stdout, stderr, code = (fixture.out / f'{key}.{suffix}' for suffix in ('json', 'stderr.log', 'exit'))
            # These captures belong to the fixture's parent zsh, outside Claude's Bash tool.
            # Only commands[key] is emitted by the scripted model and subject to the measured permission check.
            line = (f'claude -p --model claude-haiku-5-5 --output-format json {quote(key)} '
                    f'> {quote(str(stdout))} 2> {quote(str(stderr))}; print $? > {quote(str(code))}\r')
            sent = fixture.request('window_input', window['identity'], sequence=sequence,
                                   request_id=str(uuid.uuid4()), data=line)
            assert sent['ok'], sent
            fixture.wait(key + ' print CLI 退出', lambda: code.exists() and code.stat().st_size, 120)
            raw = stdout.read_text(encoding='utf-8')
            response = json.loads(raw)
            denials = response.get('permission_denials') if isinstance(response, dict) else None
            after = fixture.request('sidebar_snapshot')['terminals']
            created = [t for t in after if t['id'] not in before]
            case = dict(command=commands[key], exit=int(code.read_text().strip()), response=response,
                        permission_denials=denials, created_terminals=created,
                        redirected_file_exists=redirected.exists(), stdout=str(stdout), stderr=str(stderr))
            report['cases'][key] = case
            # A changed CLI output schema is unknown evidence, rather than an implicit permission grant.
            assert isinstance(denials, list), 'print JSON 未提供 permission_denials，须检查原始输出'
            assert any(b['key'] == key for b in fixture.api.bodies), '脚本化模型未收到该探针请求'
        a, b = (report['cases'][key] for key in commands)
        report['scripted_api'] = fixture.api.snapshot()
        if not a['permission_denials'] and len(a['created_terminals']) == 1 and b['permission_denials'] and not b['created_terminals'] and not redirected.exists():
            denied_commands = [d.get('tool_input', {}).get('command') for d in b['permission_denials'] if isinstance(d, dict)]
            assert commands['T142_PROBE_B'] in denied_commands, '拒绝的不是指定重定向命令'
            report.update(status='PASS', finding='print 模式下，只有加入 out/ 输出重定向的同一命令要求权限；裸命令已真实开出一个终端。')
        elif not a['permission_denials'] and not b['permission_denials'] and len(a['created_terminals']) == len(b['created_terminals']) == 1 and redirected.exists():
            report.update(status='PASS', finding='print 模式下两种命令均获准并真实开终端；否定“该模式下仅重定向导致拒绝”，交互模式原因仍未知。')
        else:
            report['finding'] = '结果未形成单变量归因，保留原始输出，继续核对。'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if fixture:
            try:
                fixture.stop()
            except Exception as error:
                report.update(status='INCOMPLETE', cleanup_error=str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
