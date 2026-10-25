"""T-174: a CLI started in a project terminal that writes nothing gets a hint in its pane.

Real Electron/daemon/node-pty/zsh; the CLI is t174_cli.c compiled as `claude` (zero model calls).
Failure modes (listed before implementation):
1. The foreground CLI stays silent and neither the pane status nor the pane shows anything (L01 red).
2. The hint stays after the CLI writes output.
3. A CLI that writes its screen at once and then idles (a normal start) gets the hint.
4. A shell idle at its prompt gets the hint.
5. The hint states a cause as fact or the daemon types anything for the user.
--revision runs the same assertions on that tree; --mutant drops the "started after the last output" condition.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, ROOT, quote  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['no-start-check'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/node-pty/zsh; stand-in CLI, zero model calls', checks=[], observed={})
    patches = {'no-start-check': [('src/panes.ts', 'leader.started * 1000 <= outputAt', 'false')]}.get(args.mutant, [])
    fixture = electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def no_model(body):
        raise AssertionError('stand-in CLI must not call a model')

    try:
        fixture = Fixture('t174-', no_model, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        bin_dir = fixture.dir / 'bin'
        bin_dir.mkdir()
        built = subprocess.run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11', str(ROOT / 'workbench/tests/t174_cli.c'),
                                '-o', str(bin_dir / 'claude')], capture_output=True, text=True, timeout=60)
        assert built.returncode == 0, built.stderr
        fixture.start(str(bin_dir / 'claude'), {'README.md': 'T-174 fixture\n'})
        launch = fixture.terminal_launch
        opened = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert opened['ok'], opened
        term = dict(identity=opened['identity'], sequence=0)

        def type_in(data):
            term['sequence'] += 1
            sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def silent():
            value = fixture.request('workbench_snapshot', project='demo', launch=launch)
            assert value.get('ok'), value
            return value['pane'].get('silent_foreground')

        def stays_quiet(label, seconds):
            seen = []
            for _ in range(int(seconds / .5)):
                value = silent()
                if value:
                    seen.append(value)
                time.sleep(.5)
            report['observed'][label] = seen
            return not seen

        electron = Electron(fixture, 't174-' + fixture.dir.name[5:])
        row = f'.agent-row[data-agent-launch="{launch}"]'
        electron.until('项目终端出现', f'!!document.querySelector({json.dumps(row)})', 30)
        electron.evaluate(f'document.querySelector({json.dumps(row)}).click()')
        electron.until('终端窗格出现', '!!document.querySelector(".xterm")', 30)

        check('idle_prompt_no_hint', stays_quiet('idle_prompt', 9))

        flag = fixture.out / 'flag'
        type_in(f'PATH={quote(str(bin_dir))}:$PATH; claude silent {quote(str(flag))}\r')
        started = time.monotonic()
        value = fixture.wait('后台标出无输出的前台程序', silent, 25)
        report['observed']['silent_foreground'] = value
        report['observed']['seconds_to_hint'] = round(time.monotonic() - started, 1)
        check('silent_cli_marked', value.get('command') == 'claude', value)
        text = electron.until('窗格出现提示', 'document.querySelector("[data-silent-foreground=\\"claude\\"]")?.textContent ?? null', 15)
        report['observed']['hint_text'] = text
        check('hint_names_program_and_prompt', 'claude' in text and '权限弹窗' in text and '可能' in text, text)
        electron.screenshot(fixture.out / 'silent-hint.png')

        flag.write_text('go\n', encoding='utf-8')
        fixture.wait('有输出后后台撤掉', lambda: silent() is None, 15)
        electron.until('有输出后窗格撤掉提示', '!document.querySelector("[data-silent-foreground]")', 15)
        check('hint_cleared_by_output', True)
        electron.screenshot(fixture.out / 'after-output.png')

        type_in('\x03')
        time.sleep(1)
        type_in('claude normal\r')
        check('normal_start_no_hint', stays_quiet('normal_start', 12), report['observed'].get('normal_start'))
        type_in('\x03')
        time.sleep(1)
        check('idle_after_cli_no_hint', stays_quiet('idle_after_cli', 9))
        trace = (fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        report['observed']['trace_tail'] = trace[-400:]
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
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
    print(json.dumps({k: report.get(k) for k in ('status', 'checks', 'error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
