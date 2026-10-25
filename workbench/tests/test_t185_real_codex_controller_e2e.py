"""T-185：真实 Codex 主控开局拿到 Enchanted 的开局说明，对一句“你来当执行主控，派两个 worker…”直接执行 a2a request。
隔离后台、PTY、Electron；项目终端里用户自己敲 codex，走产品的包装脚本（含 -c hooks.SessionStart）。Codex 用 /tmp 下的隔离
CODEX_HOME：只复制用户的 auth.json，结束后删除整个 home，不进证据与 Git（AGENTS.md 的真实 Codex 验收做法；构思主控
2026-10-25 同意不用用户的 ~/.codex）。模型 gpt-6.1-sol、强度 high、普通速度。钩子信任框由夹具用户在这个隔离 home 里明确
选第 2 项“Trust all and continue”，不按回车当默认。真实根提示只有 1 条。

批准后再看 20 秒就结束：本票只看申请这一步；不让它派出 worker（产品里 Codex worker 跑在用户自己的 ~/.codex）。
期望来自 T-185 ticket 的验收与 T-181 的开局说明要点。失败方式（先列再写）：
1. 开局说明没进 Codex 的会话上下文。
2. 先用问答工具（request_user_input / request_user_input_async）问用户是否批准，而不是运行 a2a request。
3. 在文件系统里找 a2a：.app 或 terminal/bin 的绝对路径、command -v / which / find。
4. 没有发起角色申请就结束回合。
5. 真实回合不止 1 个根提示、模型不是 gpt-6.1-sol、登录或权限提示被当成产品结果。
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
from scripted_claude import Electron, Fixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROMPT = '你来当执行主控，派两个 worker 并行做：一个把 stock.csv 里低于 min 的物品生成补货清单 restock.md，另一个在 README 里加一段用法说明。'
FILES = {'README.md': '# 库存演示\n\n一次性测试仓库。\n',
         'stock.csv': 'name,qty,min\n苹果,3,5\n香蕉,10,4\n牛奶,1,4\n面包,6,2\n'}
MODEL = 'gpt-6.1-sol'
ORIENTATION = ('a2a help', 'a2a request executor', 'Enchanted 工作台的项目终端')


def rollout(home):
    rows = []
    for path in sorted((home / 'sessions').rglob('rollout-*.jsonl')):
        rows += [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return rows


def calls_of(rows):
    """Function and custom tool calls in order, with the command text where there is one."""
    calls = []
    for row in rows:
        item = row.get('payload') or {}
        if row.get('type') == 'response_item' and item.get('type') in ('function_call', 'custom_tool_call'):
            raw = item.get('arguments') or item.get('input') or ''
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError):
                parsed = raw
            command = parsed.get('cmd') or parsed.get('command') if isinstance(parsed, dict) else parsed
            calls.append(dict(name=item.get('name'), command=' '.join(command) if isinstance(command, list) else str(command or ''),
                              timestamp=row.get('timestamp')))
    return calls


def score(report, rows):
    """The checks, from the Codex rollout alone, so a saved rollout can be scored again (--rescore) without a new model run."""
    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))
    calls = calls_of(rows)
    # One root prompt is one turn Codex started.
    turns = [r for r in rows if r.get('type') == 'event_msg' and (r.get('payload') or {}).get('type') == 'task_started']
    models = sorted({(r.get('payload') or {}).get('model') for r in rows if r.get('type') == 'turn_context'} - {None})
    report.update(real_model_turns=len(turns), models=models)
    check('one_real_root_prompt_on_gpt_6_1_sol', len(turns) == 1 and models == [MODEL], dict(turns=len(turns), models=models))
    context = json.dumps([r for r in rows if r.get('type') == 'response_item' and (r.get('payload') or {}).get('type') == 'message'
                          and (r.get('payload') or {}).get('role') in ('developer', 'user')], ensure_ascii=False)
    report['observed']['orientation'] = {k: k in context for k in ORIENTATION}
    check('orientation_in_codex_context', all(report['observed']['orientation'].values()), report['observed']['orientation'])
    report['observed']['commands'] = [c['command'] for c in calls]
    # Codex's code-mode tool carries the shell command inside script text (exec_command({cmd:"a2a request executor"})).
    first_request = next((i for i, c in enumerate(calls) if re.search(r'(^|[\s;&|"\'])a2a request executor', c['command'])), None)
    asked = next((i for i, c in enumerate(calls) if c['name'] in ('request_user_input', 'request_user_input_async')
                  or re.search(r'request_user_input', c['command'])), None)
    check('a2a_request_without_question_tool', first_request is not None and (asked is None or asked > first_request),
          dict(first_request=first_request, asked=asked))
    hunted = [c['command'] for c in calls if '/terminal/bin/a2a' in c['command'] or 'command -v a2a' in c['command']
              or 'which a2a' in c['command'] or re.search(r'\bfind\b.*a2a', c['command'])]
    check('a2a_found_without_searching', not hunted, hunted)
    check('role_approved_in_ui', report.get('approved'), report['observed'].get('outcome'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--revision')
    parser.add_argument('--rescore', type=Path, help='score a saved run again: its summary.json; the rollout is in its out directory')
    args = parser.parse_args()
    if args.rescore:
        assert not args.summary.exists(), '保留旧证据，选择新 --summary'
        old = json.loads(args.rescore.read_text(encoding='utf-8'))
        rows = json.loads((Path(old['out']) / 'codex-rollout.json').read_text(encoding='utf-8'))
        report = dict(status='INCOMPLETE', argv=sys.argv, rescored_from=str(args.rescore), out=old['out'], prompt=old['prompt'],
                      product_head=old['product_head'], approved=bool(old.get('approved', any(c['name'] == 'role_approved_in_ui' for c in old['checks']))),
                      checks=[], failed=[], observed=dict(outcome=old['observed'].get('outcome')))
        score(report, rows)
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']]), ensure_ascii=False))
        return 0 if report['status'] == 'PASS' else 1
    assert not args.summary.exists(), '保留旧证据，选择新 --summary'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, prompt=PROMPT,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  checks=[], failed=[], observed={})
    fixture = electron = codex_home = None

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    try:
        fixture = Fixture('t185r-', lambda body: ('worker', [], '未派发。'), revision=args.revision)
        report['fixture'] = str(fixture.dir)
        report['versions'] = {'codex': subprocess.check_output(['codex', '--version'], text=True).strip()}
        fixture.start(args.claude, FILES)
        assert fixture.request('role_release', fixture.terminal)['ok']
        codex_home = Path('/tmp') / ('t185r-codex-' + uuid.uuid4().hex[:8])
        codex_home.mkdir(mode=0o700)
        shutil.copy2(Path.home() / '.codex/auth.json', codex_home / 'auth.json')
        (codex_home / 'config.toml').write_text(
            f'model = "{MODEL}"\nmodel_reasoning_effort = "high"\ncli_auth_credentials_store = "file"\ncheck_for_update_on_startup = false\n'
            f'[projects.{json.dumps(str(fixture.repo))}]\ntrust_level = "trusted"\n', encoding='utf-8')
        electron = Electron(fixture, 't185r-' + uuid.uuid4().hex[:12])
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

        def screen():
            raw = (fixture.state / 'traces' / fixture.terminal_launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')
            return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

        line = f'export CODEX_HOME={codex_home}; codex --sandbox danger-full-access -a never'
        report['controller_launch'] = line
        send(line + '\r')
        fixture.wait('钩子信任框（隔离 home）', lambda: '2.Trustallandcontinue' in screen(), 90)
        send('2')
        fixture.wait('选中 Trust all and continue', lambda: '›2.Trustallandcontinue' in screen(), 20)
        send('\r')
        fixture.wait('Codex 输入框', lambda: 'AskCodextodoanything' in screen().split('Continuewithouttrusting')[-1], 90)
        time.sleep(3)
        send(PROMPT)
        time.sleep(1)
        send('\r')

        outcome, approved_at = None, None
        deadline = time.time() + 600
        while time.time() < deadline:
            rows = rollout(codex_home)
            if any(c['name'] in ('request_user_input', 'request_user_input_async') for c in calls_of(rows)):
                outcome = 'asked_user'
                break
            if approved_at is None:
                card = electron.evaluate('document.querySelector("[data-role-request]")?.dataset.roleRequest ?? null')
                if card:
                    electron.until('批准角色', f'(()=>{{const b=[...document.querySelectorAll(\'[data-role-request="{card}"] button\')].find(b=>b.textContent==="批准");if(!b||b.disabled)return false;b.click();return true}})()', 30)
                    approved_at = time.time()
            elif time.time() - approved_at > 20:
                outcome = 'approved_then_stopped'
                break
            if any(r.get('type') == 'event_msg' and (r.get('payload') or {}).get('type') == 'task_complete' for r in rows) and approved_at is None:
                outcome = 'turn_ended_without_request'
                break
            time.sleep(3)
        report['observed']['outcome'] = outcome or 'timeout_600s'
        electron.screenshot(fixture.out / 'scenario-finished.png')
        rows = rollout(codex_home)
        (fixture.out / 'codex-rollout.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
        (fixture.out / 'tool-calls.json').write_text(json.dumps(calls_of(rows), ensure_ascii=False, indent=2), encoding='utf-8')
        report['approved'] = approved_at is not None
        score(report, rows)
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception:
        report['error'] = traceback.format_exc()[-2000:]
    finally:
        for name, resource in [('electron', electron), ('fixture', fixture)]:
            if resource:
                try:
                    resource.stop()
                except Exception:
                    report.setdefault('cleanup_errors', []).append(name + ': stop failed; preserve instance')
                    report['status'] = 'INCOMPLETE'
        if codex_home and codex_home.exists():
            shutil.rmtree(codex_home)
            report['codex_home_removed'] = not codex_home.exists()
        if fixture:
            report['out'] = str(fixture.out)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], outcome=report['observed'].get('outcome'),
                          real_model_turns=report.get('real_model_turns'), error=(report.get('error') or '')[-300:] or None), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
