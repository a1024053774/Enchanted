"""T-107 验收第 4 条后半句：经界面的“打开项目目录”（macOS 系统对话框）新增项目，结果与后台登记一致。

真实后台、真实 Electron 窗口、真实 NSOpenPanel。对话框由一个 Codex 会话经 Computer Use 操作（用户 2026-10-22 选定），
它只操作这个测试窗口和它弹出的对话框；脚本不碰对话框，只在 Codex 每一步之后核对界面与后台。Codex 在用户自己的
~/.codex 下运行，因为 Computer Use 的插件与授权装在那里；它在这里只是操作者，不是被测对象。

期望来自 ticket 与 git：取消对话框不登记任何项目、界面不报错；选中目录并打开后，后台登记的就是这个目录
（realpath），侧栏出现它的项目行并被选中，第二行的分支与领先、落后数与 `git rev-list --left-right --count` 一致。

失败方式（先列再写）：
1. 取消也登记了项目，或界面报错；或对话框根本没弹出，“取消”一步空过。
2. 打开后登记的不是选中的目录（例如默认目录）。
3. 后台登记了，侧栏没有出现或没选中这一行，或主区域没有切到这个项目。
4. 分支行与 git 不一致。
5. Codex 没走完步骤：按 INCOMPLETE 报告，不算通过。
"""
import argparse
import json
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

CODEX_ARGV = ['codex', 'exec', '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="high"', '--sandbox', 'workspace-write', '--skip-git-repo-check']


def brief(out, pick):
    return f"""你在做一次界面验证，只能用 Computer Use 操作一个窗口：应用名为 Electron 的测试窗口（Enchanted 工作台，左侧栏顶部有一个“+”按钮，提示是“打开项目目录”），以及它弹出的 macOS 系统对话框。不要操作任何别的应用或窗口，不要改系统设置，不要登录，不要删除文件。遇到权限请求或别的意外，停下并在最后的回复里如实说明。

步骤：
1. 点侧栏顶部的“+”（打开项目目录）。会弹出标题为“打开项目目录”的系统对话框。在对话框里点“取消”。确认对话框已关闭后，运行：touch {shlex.quote(str(out / 'cancelled'))}
2. 运行：for i in $(seq 1 120); do [ -f {shlex.quote(str(out / 'go'))} ] && break; sleep 1; done
3. 再点一次“+”。对话框出现后按 Command+Shift+G，输入下面这个路径，按回车跳转，然后点对话框的“打开”按钮：
{pick}
确认对话框已关闭后，运行：touch {shlex.quote(str(out / 'opened'))}
4. 不要再点任何东西。最后用几句话说明每一步实际看到了什么。"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--mutant', choices=['pick-ignored', 'cancel-registers-default'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, mutant=args.mutant, checks=[], observed={}, model_calls='Codex 操作者，见 codex.jsonl')
    patches = {
        # The main process registers the dialog's default directory instead of the one the user picked.
        'pick-ignored': [('app/main.ts', "{ command: 'project_open', repo: picked.filePaths[0] }", "{ command: 'project_open', repo: homedir() }")],
        # Cancelling the dialog registers its default directory.
        'cancel-registers-default': [('app/main.ts', 'if (picked.canceled) return null;', 'if (picked.canceled) picked.filePaths = [homedir()];')],
    }.get(args.mutant, [])
    fixture = Fixture('t107o-', lambda body: (_ for _ in ()).throw(AssertionError('no model expected')), patches=patches)
    report['fixture'] = str(fixture.dir)
    electron = codex = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def git(repo, *arguments):
        return subprocess.check_output(['git', '-C', str(repo), *arguments], text=True, env=fixture.env).strip()

    def opening():
        # While the dialog is up the renderer is navigating and the "+" button is disabled.
        return electron.evaluate("document.querySelector('button.create-project')?.disabled === true")

    def marker(name, timeout, watch=None):
        """Wait for Codex's marker. Codex may stop on its own when the window shows something unexpected; that is
        recorded and the checks below still run, so the verdict never rests on its judgement."""
        path = fixture.out / name
        deadline = time.monotonic() + timeout
        seen = False
        while not path.exists():
            if codex.poll() is not None:
                report['observed'].setdefault('codex_stopped', f'Codex 在 {name} 之前结束（exit {codex.returncode}）')
                break
            assert time.monotonic() < deadline, f'超时：Codex 没有写 {name}'
            seen = seen or bool(watch and watch())
            time.sleep(.3)
        return seen

    def projects():
        return {row['repo']: row for row in fixture.request('sidebar_snapshot')['projects']}

    try:
        fixture.run_cli('daemon_start')
        fixture.running = True
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 10)
        fixture.operator = json.loads((fixture.dir / 'operator.json').read_text(encoding='utf-8'))
        # The directory to pick: a repository one commit ahead of its upstream.
        pick, remote = fixture.dir / 'pick-me', fixture.dir / 'pick-me.git'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(pick)], check=True, env=fixture.env)
        (pick / 'README.md').write_text('pick me\n', encoding='utf-8')
        git(pick, 'add', '.')
        git(pick, 'commit', '-q', '-m', 'init')
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(remote)], check=True, env=fixture.env)
        git(pick, 'remote', 'add', 'origin', str(remote))
        git(pick, 'push', '-q', '-u', 'origin', 'main')
        (pick / 'NOTES.md').write_text('notes\n', encoding='utf-8')
        git(pick, 'add', 'NOTES.md')
        git(pick, 'commit', '-q', '-m', 'local change')
        ahead, behind = git(pick, 'rev-list', '--left-right', '--count', 'HEAD...@{u}').split()
        expected = dict(repo=str(pick.resolve()), branch=git(pick, 'rev-parse', '--abbrev-ref', 'HEAD'), ahead=int(ahead), behind=int(behind))
        report['observed']['expected'] = expected

        electron = Electron(fixture, 't107o-' + fixture.dir.name[6:])
        electron.until('侧栏出现“打开项目目录”', "!!document.querySelector('button.create-project:not(:disabled)')", 60)
        check('starts_without_projects', projects() == {}, projects())
        electron.screenshot(fixture.out / '01-before.png')

        argv = [*CODEX_ARGV, '-C', str(fixture.out), '--json', '-o', str(fixture.out / 'codex-last.txt'), brief(fixture.out, pick)]
        report['codex_argv'] = argv
        report['codex_version'] = subprocess.check_output(['codex', '--version'], text=True).strip()
        codex = subprocess.Popen(argv, stdout=(fixture.out / 'codex.jsonl').open('w'), stderr=(fixture.out / 'codex.stderr').open('w'),
                                 stdin=subprocess.DEVNULL, start_new_session=True)

        check('dialog_opened_before_cancel', marker('cancelled', 600, opening), 'the "+" button never went busy')
        electron.until('取消后界面回到可操作', "document.querySelector('button.create-project')?.disabled === false", 20)
        alerts = electron.evaluate("[...document.querySelectorAll('[role=alert]')].map(n=>n.textContent)")
        report['observed']['after_cancel'] = dict(projects=list(projects()), alerts=alerts)
        electron.screenshot(fixture.out / '02-after-cancel.png')
        check('cancel_registers_nothing', projects() == {}, projects())
        check('cancel_shows_no_error', alerts == [], alerts)
        (fixture.out / 'go').touch()

        marker('opened', 600)
        # Once Codex has stopped nothing more will come; read the registration as it is.
        registered = projects() if 'codex_stopped' in report['observed'] else fixture.wait('后台登记', projects, 20)
        report['observed']['registered'] = registered
        check('registers_the_picked_directory', list(registered) == [expected['repo']], registered)
        project = registered[expected['repo']]['project_id']
        row = electron.until('项目行出现并选中', f"""(()=>{{const n=document.querySelector('[data-project-id={json.dumps(project)}]');
            return n && n.getAttribute('aria-current')==='page' && {{text:n.innerText,title:n.title,git:n.querySelector('.project-git').textContent}}}})()""", 20)
        report['observed']['row'] = row
        electron.screenshot(fixture.out / '03-opened.png')
        check('sidebar_row_selected', expected['repo'] in row['title'], row)
        header = electron.until('主区域切到这个项目', f"""(()=>{{const h=document.querySelector('.task-header');
            const e=h?.querySelector('.eyebrow'); return e?.title==={json.dumps(expected['repo'])} && {{title:h.querySelector('h1').textContent,eyebrow:e.textContent}}}})()""", 20)
        report['observed']['header'] = header
        check('main_area_shows_the_project', header['title'] == project, header)
        check('branch_line_matches_git', row['git'] == f"{expected['branch']} · ↑{expected['ahead']} ↓{expected['behind']}", (row, expected))
        codex.wait(300)
        report['codex_exit'] = codex.returncode
        check('codex_finished_the_steps', (fixture.out / 'opened').exists(), report['observed'].get('codex_stopped'))
        report['codex_last_message'] = (fixture.out / 'codex-last.txt').read_text(encoding='utf-8') if (fixture.out / 'codex-last.txt').exists() else None
        report['status'] = 'PASS'
    except Exception as error:  # noqa: BLE001 - the summary keeps every failure
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if codex and codex.poll() is None:
            os.killpg(codex.pid, signal.SIGTERM)
            codex.wait(30)
        if codex:
            report.setdefault('codex_exit', codex.returncode)
            last = fixture.out / 'codex-last.txt'
            report.setdefault('codex_last_message', last.read_text(encoding='utf-8') if last.exists() else None)
        if electron:
            electron.stop()
        fixture.stop()
        (fixture.dir / 'operator.json').unlink(missing_ok=True)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], checks=report['checks'], error=report.get('error')), ensure_ascii=False))
    sys.exit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
