"""T-181（L08）：真实 Haiku 主控复跑 lcu 实测里那一句请求。
隔离后台、PTY、Electron；项目终端里用户自己启动的 claude 走产品的 shim 与插件（含 SessionStart 开局说明）。
只有这个主控连接真实供应商（claude-haiku-5-5）；它派出的 worker 用本地脚本化接口，只结束回合、不交付。
真实根提示只有 1 条：L08 原句，逐字。批准由测试在界面上点“批准”，不代答任何别的提示。

期望来自 T-181 ticket 的验收：直接执行 a2a request；验收脚本无绝对路径；无长轮询。另记：没有停下来问工作分支（T-180）。
失败方式（先列再写）：
1. 先用 AskUserQuestion 代替 a2a request（L08 原样）。出现问答框时测试不代答，记失败并结束。
2. 在文件系统里找 a2a 入口：用 .app 内的绝对路径调用 a2a，或先 command -v / find 再调用。
3. 验收脚本或任务卡完成条件里写死项目主目录的绝对路径。
4. 派发后用 sleep 循环反复查 status。
5. 停下来问工作分支，没有派发。
6. 真实回合不止 1 个根提示、模型不是 haiku、登录或权限提示被当成产品结果。
以上 2、4 按工具调用里的命令原文机械核对，原文全部留档；“并行任务的共享约定写进两张卡”要读卡判断，交独立审查，不在这里宣称通过。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, quote  # noqa: E402
from test_t163_controller_e2e import credentials, native_rows, root_prompts, write  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ('请申请成为这个项目的执行主控（a2a request executor）。批准后：把 stock.csv 低于 min 的物品生成补货清单 restock.md，'
          '并另起一个任务在 README 里加一段用法说明；两件事分别派给两个 worker 并行做。')
FILES = {'README.md': '# 库存演示\n\n一次性测试仓库。\n',
         'stock.csv': 'name,qty,min\n苹果,3,5\n香蕉,10,4\n牛奶,1,4\n面包,6,2\n'}


def tool_calls(rows):
    calls = []
    for row in rows:
        if row.get('type') != 'assistant':
            continue
        for block in row.get('message', {}).get('content', []) if isinstance(row.get('message', {}).get('content'), list) else []:
            if block.get('type') == 'tool_use':
                calls.append(dict(name=block['name'], input=block.get('input', {}), timestamp=row.get('timestamp')))
    return calls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，选择新 --summary'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, prompt=PROMPT,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  real_model_turns=None, checks=[], failed=[], observed={})
    fixture = electron = controller_home = None
    secret = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    try:
        fixture = Fixture('t181r-', lambda body: ('worker', [], '本次派发观察已结束；未生成候选，等待主控。'), revision=args.revision)
        report['fixture'] = str(fixture.dir)
        report['versions'] = {name: subprocess.check_output(argv, text=True).strip() for name, argv in
                              [('node', ['node', '--version']), ('claude', [args.claude, '--version'])]}
        fixture.start(args.claude, FILES)
        assert fixture.request('role_release', fixture.terminal)['ok']
        controller_home = fixture.dir / 'controller-home'
        config = controller_home / '.claude'
        config.mkdir(parents=True, mode=0o700)
        secret = credentials(Path.home(), config / '.credentials.json')
        write(config / '.claude.json', dict(hasCompletedOnboarding=True, hasSeenAutoDefaultNudge=True, theme='dark',
              projects={str(fixture.repo): dict(hasTrustDialogAccepted=True)}))
        # Same disposable-HOME permissions as T-163, except AskUserQuestion stays available: using it is the behaviour under test.
        permissions = {'defaultMode': 'dontAsk', 'allow': ['Read', 'Write', 'Edit', 'Bash'], 'deny': ['Task', 'Agent'],
                       'additionalDirectories': ['/tmp', '/private/tmp']}
        write(config / 'settings.json', {'permissions': permissions})
        report['fixture_permissions'] = permissions
        electron = Electron(fixture, 't181r-' + uuid.uuid4().hex[:12])
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        opened = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project='demo')
        assert opened['ok'], opened
        seq = 0

        def send(data):
            nonlocal seq
            seq += 1
            answer = fixture.request('window_input', opened['identity'], sequence=seq, request_id=str(uuid.uuid4()), data=data)
            assert answer['ok'], answer

        line = ('unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY CLAUDECODE; '
                f'export HOME={quote(str(controller_home))} CLAUDE_CONFIG_DIR={quote(str(config))} '
                'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1; '
                f'claude --model claude-haiku-5-5 --session-id {uuid.uuid4()}')
        report['controller_launch'] = line
        send(line + '\r')
        raw = lambda: (fixture.state / 'traces' / fixture.terminal_launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        fixture.wait('真实 Claude 输入框（不代答登录或权限提示）', lambda: 'Claude Code' in raw() and '❯' in re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]', '', raw()), 90)
        send(PROMPT)
        time.sleep(1)
        send('\r')

        # Approve in the UI when the request card appears; stop at an AskUserQuestion without answering it.
        outcome = None
        deadline = time.time() + 900
        approved = False
        while time.time() < deadline:
            calls = tool_calls(native_rows(controller_home))
            if any(c['name'] == 'AskUserQuestion' for c in calls):
                outcome = 'asked_user_question'
                break
            if not approved:
                card = electron.evaluate('document.querySelector("[data-role-request]")?.dataset.roleRequest ?? null')
                if card:
                    electron.until('批准角色', f'(()=>{{const b=[...document.querySelectorAll(\'[data-role-request="{card}"] button\')].find(b=>b.textContent==="批准");if(!b||b.disabled)return false;b.click();return true}})()', 30)
                    approved = True
            rows = native_rows(controller_home)
            last = next((r for r in reversed(rows) if r.get('type') == 'assistant'), None)
            if approved and last and last.get('message', {}).get('stop_reason') == 'end_turn':
                time.sleep(20)  # a turn that really ended stays ended
                rows = native_rows(controller_home)
                # Rows are re-read from disk, so compare the row's identity (uuid), not the Python object.
                if (next((r for r in reversed(rows) if r.get('type') == 'assistant'), None) or {}).get('uuid') == last.get('uuid'):
                    outcome = 'turn_ended'
                    break
            time.sleep(5)
        report['observed']['outcome'] = outcome or 'timeout_900s'
        electron.screenshot(fixture.out / 'scenario-finished.png')
        rows = native_rows(controller_home)
        write(fixture.out / 'native-transcript.json', rows)
        calls = tool_calls(rows)
        write(fixture.out / 'tool-calls.json', calls)
        models = sorted({r.get('message', {}).get('model', '') for r in rows if r.get('type') == 'assistant'})
        turns = root_prompts(rows)
        report.update(real_model_turns=len(turns), assistant_models=models)
        check('one_real_haiku_root_prompt', len(turns) == 1 and bool(models) and all('haiku' in m for m in models), dict(turns=len(turns), models=models))
        commands = [c['input'].get('command', '') for c in calls if c['name'] == 'Bash']
        report['observed']['bash_commands'] = commands
        first_request = next((i for i, c in enumerate(calls) if c['name'] == 'Bash' and re.search(r'(^|[\s;&|])a2a request executor', c['input'].get('command', ''))), None)
        asked = next((i for i, c in enumerate(calls) if c['name'] == 'AskUserQuestion'), None)
        # 1
        check('a2a_request_without_question_box', first_request is not None and (asked is None or asked > first_request), dict(first_request=first_request, asked=asked))
        # 2: called as `a2a`, never by an absolute path inside the app or after searching for it.
        hunted = [c for c in commands if '/terminal/bin/a2a' in c or 'command -v a2a' in c or 'which a2a' in c or re.search(r'\bfind\b.*a2a', c)]
        check('a2a_found_without_searching', not hunted, hunted)
        # 4: no sleep loop over status.
        polling = [c for c in commands if 'sleep' in c and ('status' in c or 'for ' in c or 'while ' in c)]
        check('no_sleep_polling', not polling, polling)
        # 3 and 5: the cards the gate holds.
        tasks = [t['task_id'] for t in fixture.request('tasks_list', fixture.operator, project='demo').get('tasks', [])]
        report['observed']['tasks'] = tasks
        cards = {}
        for task in tasks:
            status = fixture.request('status', fixture.operator, task=task)
            card = fixture.request('card_show', fixture.operator, task=task, card_version=status['task']['card_version'])
            cards[task] = dict(status=status['task'], card=card)
        write(fixture.out / 'cards.json', cards)
        repo = str(fixture.repo)
        scripts = {}
        for task, entry in cards.items():
            for condition in entry['card'].get('card', {}).get('completion_conditions', []):
                for arg in condition.get('argv', []):
                    path = Path(arg)
                    if path.is_absolute() and path.is_file() and path.stat().st_size < 200_000:
                        scripts[arg] = path.read_text(encoding='utf-8', errors='replace')
        write(fixture.out / 'acceptance-scripts.json', scripts)
        absolute = [name for name, text in scripts.items() if repo in text or repo.replace('/private', '', 1) in text] + \
                   [task for task, entry in cards.items() if repo in json.dumps(entry['card'].get('card', {}).get('completion_conditions', []))]
        check('acceptance_without_repo_absolute_path', bool(scripts) and not absolute, dict(scripts=list(scripts), absolute=absolute))
        dispatched = [task for task, entry in cards.items() if (entry['status'].get('current_attempt') or {}).get('thread_id')]
        report['observed']['work_branches'] = {task: entry['status'].get('integration_ref') for task, entry in cards.items()}
        check('two_dispatched_without_branch_question', len(dispatched) == 2, dict(dispatched=dispatched, outcome=report['observed']['outcome']))
        report['semantic_review_required'] = ['两张卡是否把共用约定（文件名、格式、README 示例与 restock.md 格式一致）写进各自目标与完成条件',
                                              '最终回复是否告诉用户工作分支与当前状态，是否如实']
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        detail = traceback.format_exc()
        report['error'] = detail.replace(secret, '[REDACTED]') if secret else f'{type(error).__name__}: {error}'
    finally:
        for name, resource in [('electron', electron), ('fixture', fixture)]:
            if resource:
                try:
                    resource.stop()
                except Exception:
                    report.setdefault('cleanup_errors', []).append(name + ': stop failed; preserve instance')
                    report['status'] = 'INCOMPLETE'
        if controller_home:
            rows = native_rows(controller_home)
            report['real_model_turns'] = len(root_prompts(rows))
            if fixture and not (fixture.out / 'native-transcript.json').exists():
                write(fixture.out / 'native-transcript.json', rows)
            shutil.rmtree(controller_home)
        if fixture:
            report['out'] = str(fixture.out)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        write(args.summary, report)
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], outcome=report['observed'].get('outcome'),
                          real_model_turns=report.get('real_model_turns'), error=(report.get('error') or '')[-300:] or None), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
