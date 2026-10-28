"""T-202：项目终端里本来就不输出的命令（sleep）安静数秒后，提示不再把它说成“可能在等 macOS 的权限弹窗”；只有“如果它本该有输出”时
才指向权限弹窗。一个启动后一直没输出的 CLI（这里是名为 claude 的替身，像被“文稿”授权框挡住的 Claude Code）仍然得到提示。
真实后台、socket、Electron 窗口（CDP 驱动）、真实 zsh，零模型调用。

预期来自需求（T-202 与第 1 轮试用发现 1、4）：
- `sleep 300`：提示（若出现）明确以“如果它本该有输出”为前提，并说明本来不输出的命令可以不管。
- 名为 claude、启动后没有任何输出的程序：仍出现提示，仍提到 macOS 的权限弹窗。

失败方式（先列再写）：
1. 对 sleep 断言“它可能在等权限弹窗”（修前）。
2. 修法删掉提示，真被弹窗挡住的 CLI 也不再提示。
3. 有输出后提示不消失。
--revision 在该版本的源码上跑同一场景（修前应在第 1 条失败）。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import traceback
import uuid

from scripted_claude import Electron, Fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision,
                  runtime='real Electron/daemon/zsh; zero model calls', checks=[])
    fixture = electron = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if condition:
            report['checks'].append(name)
        else:
            report.setdefault('failed', []).append(name)

    try:
        def no_model(body):
            raise AssertionError('T-202 不调用模型')
        fixture = Fixture('t202-', no_model, revision=args.revision)
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/false', {'README.md': 'demo\n'})
        # A stand-in that, like a CLI held by a system privacy prompt, starts and writes nothing until it reads a line.
        bin_dir = fixture.dir / 'bin'
        bin_dir.mkdir()
        # Compiled, so the foreground process itself is named claude (a script would show as its interpreter).
        (bin_dir / 'claude.c').write_text('#include <stdio.h>\n#include <unistd.h>\nint main(void){char line[256];'
                                          'if(fgets(line,sizeof line,stdin))printf("claude stand-in: got %s",line);fflush(stdout);sleep(600);return 0;}\n', encoding='utf-8')
        built = subprocess.run(['/usr/bin/clang', '-o', str(bin_dir / 'claude'), str(bin_dir / 'claude.c')], capture_output=True, text=True, timeout=60)
        assert built.returncode == 0, built.stderr
        launch = fixture.terminal_launch
        window = fixture.request('window_open', fixture.operator, launch=launch, project=fixture.project)
        assert window['ok'], window
        sequence = iter(range(1, 100))

        def send(text):
            assert fixture.request('window_input', window['identity'], sequence=next(sequence), request_id=str(uuid.uuid4()), data=text)['ok']

        electron = Electron(fixture, 't202-' + uuid.uuid4().hex[:10])
        electron.until('项目', f'!!document.querySelector(\'[data-project-id="{fixture.project}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-project-id="{fixture.project}"]\').click()')
        electron.until('终端行', f'!!document.querySelector(\'[data-agent-launch="{launch}"]\')')
        electron.evaluate(f'document.querySelector(\'[data-agent-launch="{launch}"]\').click()')
        pane = f'section.pane[data-launch-id="{launch}"]'
        electron.until('终端可见', f'!!document.querySelector(\'{pane}\')?.getClientRects().length')
        hint = lambda name: f'(()=>{{const n=document.querySelector(\'{pane} [data-silent-foreground="{name}"]\');return n?n.textContent:null}})()'

        send('sleep 300\r')
        sleep_hint = electron.until('sleep 的提示', hint('sleep'), 40)
        report['sleep_hint'] = sleep_hint
        check('sleep_hint_conditional', '如果它本该有输出' in sleep_hint, sleep_hint)
        check('sleep_hint_not_asserted', '它可能在等' not in sleep_hint, sleep_hint)
        send('\x03')
        electron.until('sleep 提示消失', f'!document.querySelector(\'{pane} [data-silent-foreground]\')', 30)

        send(f'{bin_dir}/claude\r')
        cli_hint = electron.until('CLI 的提示', hint('claude'), 40)
        report['cli_hint'] = cli_hint
        check('silent_cli_still_hinted', 'macOS 的权限弹窗' in cli_hint, cli_hint)
        electron.screenshot(fixture.out / 'cli-hint.png')
        send('go\r')
        check('hint_clears_on_output', bool(electron.until('有输出后消失', f'!document.querySelector(\'{pane} [data-silent-foreground]\')', 30)))
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        for stop in (electron, fixture):
            if stop:
                try:
                    stop.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
