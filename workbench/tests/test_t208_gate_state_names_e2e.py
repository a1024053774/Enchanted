"""T-208：任务页底部的门禁状态在审查中显示中文状态名，不显示“未知”。
真实 Electron 窗口、真实后台与门禁，worker 与审查员是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。

预期来自需求（UAT-03 3b 发现 3，T-208）：
1. worker 交付、验收通过后门禁进入审查（reviewing），审查员还在跑时打开任务页：底部门禁状态是“审查中”，不是“未知”。
2. 门禁代码里会写给任务的每个状态，界面状态名表里都有中文名（从门禁源码里列出状态，不手抄）。

失败方式（先列再写）：
1. 状态名表缺 reviewing（修前），底部显示“未知”。
2. 只补了 reviewing，返工（rework）或以后新增的状态仍缺名字。
3. 测试在审查结束后才看页面，看到的已不是审查中。
--revision 在该版本源码上跑同一场景；--mutant 见 MUTANTS。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory

ROOT = Path(__file__).resolve().parents[2]
MUTANTS = {
    # The name for rework is dropped again; reviewing alone stays named.
    'rework-unnamed': [('src/gateReceipts.ts', " rework: '返工中',", '')],
    # A state only a ternary writes loses its name (review 1 P2: the first extraction could not see it).
    'upgraded-unnamed': [('src/gateReceipts.ts', " upgraded: '已升级',", '')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/gate/Claude Code; scripted Messages API; zero vendor model calls', checks=[])
    fixture = electron = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            # The reviewer stays busy long enough for the page to be read while the gate is in review.
            return 'review', [('Bash', dict(command='sleep 40', description='read the candidate slowly', timeout=60000))], '还在看。'
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Write', dict(file_path=f'{cwd}/answer.txt', content='accepted')),
                          ('Bash', dict(command='git add answer.txt', description='stage')),
                          ('Bash', dict(command='git commit -q -m ' + quote('T208 fixture candidate'), description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    try:
        fixture = Fixture('t208-', plan, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-208 fixture\n', 'check.py':
            'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'})
        electron = Electron(fixture, 't208-' + fixture.dir.name[5:])
        electron.until('项目可见', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        fixture.card('T-1', 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        assert dispatched.get('ok'), dispatched
        attempt = dispatched['attempt']
        status = lambda: fixture.request('status', fixture.operator, task='demo+T-1')['task']
        fixture.wait('交付', lambda: status()['state'] == 'submitted', 180)
        assert fixture.request('verify', fixture.terminal, task='T-1').get('ok')
        fixture.wait('进入审查', lambda: status()['state'] == 'reviewing', 120)

        # 1. The worker's row opens its task with the pane; the bar under it shows the gate state.
        rows = fixture.request('sidebar_snapshot')['agents']
        launch = next(row['id'] for row in rows if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        selector = '[data-agent-launch=' + json.dumps(launch) + ']'
        electron.until('worker 侧栏可见', f'!!document.querySelector({json.dumps(selector)})')
        electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
        electron.until('门禁状态条', '!!document.querySelector("section.gate [data-gate-state]")')
        bar = electron.evaluate('(e => ({state: e.dataset.gateState, text: e.innerText}))(document.querySelector("section.gate [data-gate-state]"))')
        report['bar'] = bar
        report['state_after_read'] = status()['state']
        check('still_in_review_when_read', report['state_after_read'] == 'reviewing', report['state_after_read'])
        check('review_state_named', bar['state'] == 'reviewing' and bar['text'] == '审查中', bar)
        electron.screenshot(fixture.out / 'gate-bar.png')

        # 2. Every task state the gate writes has a name. The states come from the gate's own source.
        source = fixture.source / 'workbench/src/gates/core.ts'
        # Every value `task.state = ...;` can write (a ternary's two results, not the literals its condition compares), and
        # the state a task record is created in (state, spec_rev, fence, current_attempt). Review 1 P2: the first version
        # saw only `task.state = "x"`.
        code = source.read_text(encoding='utf-8')
        written = [literal for statement in re.findall(r'task\.state = ([^;]+);', code)
                   for literal in re.findall(r'(?:^|[?:])\s*"([a-z_]+)"', statement)]
        created = re.findall(r'\bstate: "([a-z_]+)",\s*spec_rev: 1,\s*fence: 0,\s*current_attempt: null', code)
        states = sorted(set(written + created))
        names = json.loads(subprocess.run(['node', '--input-type=module', '-e',
            f'import {{ gateStateNames }} from {json.dumps(str(source.parent.parent / "gateReceipts.ts"))};'
            'console.log(JSON.stringify(gateStateNames))'], capture_output=True, text=True, check=True).stdout)
        missing = [state for state in states if state not in names]
        report['gate_states'] = states
        check('every_gate_state_named', bool(states) and not missing, dict(states=states, missing=missing))
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except BaseException as cleanup:
                    report.setdefault('cleanup_errors', []).append(str(cleanup))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
