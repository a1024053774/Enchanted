"""T-163：真实 Haiku 执行主控、隔离后台/PTY/Electron。

失败方式（写代码前列出）：
1. C5 的 A 卡遗漏“首版故意漏总计，真实打回后修复”，或 B 卡把先上报/等待答复写成可选。
2. 只看模型自报自检成功，不读取实际保存、实际派发的卡。
3. 生成的验收只匹配字串，接受错数字、反向语义、漏总计、非零库存或分组。
4. 把正确但排版不同的中文文档误拒；原始数据变化后仍接受旧答案。
5. 沙箱、登录、权限或启动失败被算成产品红态；未读原生日志却声称真实模型/回合数。
6. 重用用户配置或向其全局目录写入；重复运行覆盖旧证据；诊断或凭据进入报告。
7. 夹具的有限 Bash 前缀阻断正常多行派发，导致未实际派发却被误判为模型遗漏。

期望来源：T-163、T-155 C5 与用户答复“保持平铺列表，不按类别分组”。
C5 卡的语义须由主控独立阅读 cards/native-transcript.json；脚本不以字串推断语义通过。
oracle 场景独立运行模型生成的脚本，用原始数据和未提供给模型的正确/错误输入作判断。
受管 worker 用本地脚本化 Messages 接口，仅结束回合，不产生候选或验收结论；
只有项目终端主控连接真实供应商，使用 claude-haiku-5-5。没有 reviewer/集成/push。
每次运行仅提交 2 个真实根提示；--revision 与 --mutant 只改变产品源码。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid

from scripted_claude import Electron, Fixture, quote, source_tree


ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'e83a8a04e'
INSTRUCTIONS = 'workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md'
PANTRY = [dict(name='苹果', category='水果', quantity=3), dict(name='香蕉', category='水果', quantity=0),
          dict(name='大米', category='主食', quantity=2), dict(name='面条', category='主食', quantity=0),
          dict(name='牛奶', category='乳品', quantity=1)]


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def native_rows(home):
    return [json.loads(line) for path in sorted((home / '.claude/projects').rglob('*.jsonl'))
            if 'subagents' not in path.parts for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def root_prompts(rows):
    result = []
    for row in rows:
        if row.get('type') != 'user' or row.get('isMeta') or row.get('interruptedMessageId'):
            continue
        content = row.get('message', {}).get('content', '')
        text = content if isinstance(content, str) else '\n'.join(b.get('text', '') for b in content if b.get('type') == 'text')
        if text.strip():
            result.append(dict(uuid=row.get('uuid'), timestamp=row.get('timestamp'), text=text))
    return result


def credentials(real_home, destination):
    """Only read the exact Claude login; keep the copy private and remove it after the run."""
    source = real_home / '.claude/.credentials.json'
    if source.is_file() and not source.is_symlink():
        payload = json.loads(source.read_text(encoding='utf-8'))
    else:
        keychain = real_home / 'Library/Keychains/login.keychain-db'
        if not keychain.is_file() or keychain.is_symlink():
            raise RuntimeError('登录凭据不可核对；不启动模型')
        run = subprocess.run(['/usr/bin/security', 'find-generic-password', '-s', 'Claude Code-credentials',
                              '-w', str(keychain)], capture_output=True, timeout=10)
        if run.returncode:
            raise RuntimeError('无法读取精确 Claude 登录项；不启动模型')
        payload = json.loads(run.stdout)
    oauth = payload['claudeAiOauth']
    if oauth['expiresAt'] <= (time.time() + 600) * 1000:
        raise RuntimeError('登录即将过期；不自动刷新或启动模型')
    # No refresh token: this run cannot rotate the user's shared login.
    oauth = {k: v for k, v in oauth.items() if k != 'refreshToken'}
    write(destination, {'claudeAiOauth': oauth})
    destination.chmod(0o600)
    return oauth['accessToken']


def oracle_probe(fixture, report):
    # Inputs come from the raw pantry fixture, not from the generated scripts.
    good = '水果：2 种，库存 3 件\n主食：2 种，库存 2 件\n乳品：1 种，库存 1 件\n总计：5 种，库存 6 件\n'
    good_alt = '水果：种类 2，件数 3\n主食：种类 2，件数 2\n乳品：种类 1，件数 1\n总计：种类 5，件数 6\n'
    shopping = '# 补货单\n\n- 香蕉\n- 面条\n'
    cases = [
        ('summary-good', 'check_pantry.py', 'pantry-summary.md', good, True, PANTRY),
        ('summary-good-other-layout', 'check_pantry.py', 'pantry-summary.md', good_alt, True, PANTRY),
        ('summary-wrong-numbers', 'check_pantry.py', 'pantry-summary.md', good.replace('水果：2 种，库存 3 件', '水果：3 种，库存 2 件'), False, PANTRY),
        ('summary-missing-total', 'check_pantry.py', 'pantry-summary.md', good.rsplit('总计', 1)[0], False, PANTRY),
        ('summary-inverted', 'check_pantry.py', 'pantry-summary.md', '以下数字均为错误示例，不是实际库存：\n' + good, False, PANTRY),
        ('shopping-good', 'check_shopping.py', 'shopping-list.md', shopping, True, PANTRY),
        ('shopping-inverted', 'check_shopping.py', 'shopping-list.md', '# 无需购买\n\n- 香蕉\n- 面条\n', False, PANTRY),
        ('shopping-nonzero', 'check_shopping.py', 'shopping-list.md', shopping + '- 苹果\n', False, PANTRY),
        ('shopping-grouped', 'check_shopping.py', 'shopping-list.md', '# 补货单\n\n## 水果\n- 香蕉\n## 主食\n- 面条\n', False, PANTRY),
        ('shopping-stale-source', 'check_shopping.py', 'shopping-list.md', shopping, False,
         [dict(row, quantity=1) if row['name'] == '香蕉' else dict(row, quantity=0) if row['name'] == '牛奶' else row for row in PANTRY]),
        ('shopping-changed-source-good', 'check_shopping.py', 'shopping-list.md', '# 补货单\n\n- 牛奶\n- 面条\n', True,
         [dict(row, quantity=1) if row['name'] == '香蕉' else dict(row, quantity=0) if row['name'] == '牛奶' else row for row in PANTRY]),
    ]
    for name, script, output, content, expected, data in cases:
        case = fixture.out / name
        case.mkdir()
        write(case / 'pantry.json', data)
        (case / output).write_text(content, encoding='utf-8')
        run = subprocess.run(['python3', '-I', str(fixture.out / script)], cwd=case,
                             capture_output=True, text=True, timeout=20,
                             env={k: v for k, v in fixture.env.items() if not k.startswith(('ANTHROPIC_', 'A2A_'))})
        write(case / 'run.json', dict(returncode=run.returncode, stdout=run.stdout, stderr=run.stderr))
        # An interpreter/import error is not a meaningful rejection of a bad document.
        valid_rejection = run.returncode != 0 and 'Traceback (most recent call last)' not in run.stderr
        passed = run.returncode == 0 if expected else valid_rejection
        report['checks'].append(dict(name=name, passed=passed, expected_accept=expected, returncode=run.returncode))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--scenario', required=True, choices=['c5', 'oracle'])
    parser.add_argument('--budget', required=True, type=Path, help='本票共享的追加式预算账本；每次预留 2 回合，不自动释放失败预留')
    parser.add_argument('--budget-limit', type=int, choices=[16, 20], default=16,
                        help='默认累计 16；主控 #55 转述用户追加授权后，第五、六轮显式使用 20')
    parser.add_argument('--claude', default=shutil.which('claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['parent-instructions'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，选择新 --summary'
    report = dict(status='INCOMPLETE', argv=sys.argv, scenario=args.scenario, revision=args.revision,
                  mutant=args.mutant, product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  real_model_turns=None, submitted_prompts=0, budget_limit=args.budget_limit, checks=[])
    report['product_revision'] = subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip()
    fixture = electron = credential = controller_home = None
    secret = None
    try:
        args.budget.parent.mkdir(parents=True, exist_ok=True)
        # Controller runs are sequential. Preserve a reservation even on setup/interruption failure.
        import fcntl
        with args.budget.open('a+', encoding='utf-8') as budget:
            fcntl.flock(budget, fcntl.LOCK_EX)
            budget.seek(0)
            reserved = sum(json.loads(line)['reserved_turns'] for line in budget if line.strip())
            if reserved + 2 > args.budget_limit:
                raise RuntimeError(f'真实模型总预算预留将超出 {args.budget_limit}；停止，不重试')
            budget.write(json.dumps(dict(summary=str(args.summary.resolve()), scenario=args.scenario,
                                        reserved_turns=2, reserved_before=reserved, budget_limit=args.budget_limit)) + '\n')
            budget.flush()
        # The helper's local endpoint is exclusively for managed workers. A real controller gets its own HOME and login.
        fixture = Fixture('t163-', lambda body: ('worker', [], '本次派发观察已结束；未生成候选，等待主控。'), revision=args.revision)
        if args.mutant:
            fixture.source = source_tree(fixture.dir, revision=report['product_head'])
            for name in [INSTRUCTIONS, 'workbench/src/terminalCli.ts']:
                (fixture.source / name).write_bytes(subprocess.check_output(['git', 'show', f'{BASELINE}:{name}'], cwd=ROOT))
            fixture.cli = fixture.source / 'workbench/src/gates/cli.ts'
        report['fixture'] = str(fixture.dir)
        report['versions'] = {name: subprocess.check_output(argv, text=True).strip() for name, argv in
                              [('node', ['node', '--version']), ('claude', [args.claude, '--version'])]}
        fixture.start(args.claude, {'README.md': '# 一次性食材清单\n单位：件。数量为零表示需要补货。\n',
                                   'pantry.json': json.dumps(PANTRY, ensure_ascii=False) + '\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        controller_home = fixture.dir / 'controller-home'
        config = controller_home / '.claude'
        config.mkdir(parents=True, mode=0o700)
        credential = config / '.credentials.json'
        secret = credentials(Path.home(), credential)
        write(config / '.claude.json', dict(hasCompletedOnboarding=True, hasSeenAutoDefaultNudge=True,
              theme='dark', projects={str(fixture.repo): dict(hasTrustDialogAccepted=True)}))
        # RUN-OUTSIDE-01: our prefix-only fixture rejected the controller's set -e/for loop.
        # Allow Bash only in this disposable controller HOME; production shell launch adds no such settings.
        # The same fixture authorization applies to current, --revision and --mutant runs.
        permissions = {'defaultMode': 'dontAsk',
              'allow': ['Read', 'Write', 'Edit', 'Bash'],
              'deny': ['Task', 'Agent', 'AskUserQuestion'], 'additionalDirectories': [str(fixture.out)]}
        write(config / 'settings.json', {'permissions': permissions})
        report['fixture_permissions'] = permissions
        electron = Electron(fixture, 't163-' + uuid.uuid4().hex[:12])
        electron.until('项目出现', '!!document.querySelector(\'[data-project-id="demo"]\')')
        electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
        opened = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project='demo')
        assert opened['ok'], opened
        seq = 0

        def send(data):
            nonlocal seq
            seq += 1
            answer = fixture.request('window_input', opened['identity'], sequence=seq,
                                     request_id=str(uuid.uuid4()), data=data)
            assert answer['ok'], answer

        # Keep the real CLI inside the product's terminal shim/plugin. No credential in PTY commands or logs.
        line = ('unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY CLAUDECODE; '
                f'export HOME={quote(str(controller_home))} CLAUDE_CONFIG_DIR={quote(str(config))} '
                'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1; '
                f'claude --model claude-haiku-5-5 --effort medium --session-id {uuid.uuid4()}')
        report['controller_launch'] = line
        send(line + '\r')

        def ready():
            raw = (fixture.state / 'traces' / fixture.terminal_launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')
            screen = re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]', '', raw)
            return 'Claude Code' in screen and '❯' in screen

        fixture.wait('真实 Claude 输入框（不代答登录或权限提示）', ready, 90)

        def submit(text):
            report['submitted_prompts'] += 1
            if report['submitted_prompts'] > 2:
                raise RuntimeError('本次运行真实提示预算超限')
            send(text)
            time.sleep(1)
            send('\r')

        submit('请担任这个一次性项目的执行主控。先读 Enchanted 的 a2a 使用说明，申请执行主控，等界面批准；本轮不要派发任务。不 push、不删除文件，不操作其他项目。')
        request = electron.until('主控角色申请', 'document.querySelector("[data-role-request]")?.dataset.roleRequest ?? null', 120)
        electron.until('批准角色', f'(()=>{{const b=[...document.querySelectorAll(\'[data-role-request="{request}"] button\')].find(b=>b.textContent==="批准");if(!b||b.disabled)return false;b.click();return true}})()', 30)
        fixture.wait('主控确认身份', lambda: fixture.request('terminal_whoami', fixture.terminal).get('role') == 'executor', 60)
        state = f'document.querySelector(\'.agent-row[data-agent-launch="{fixture.terminal_launch}"]\')?.dataset.agentState'
        electron.until('身份回合结束', state + ' === "idle"', 120)
        common = (f'只操作当前测试 repo。脚本和任务卡 JSON 放 {fixture.out}，不要放进 repo。'
                  '不要改 pantry.json。所有 worker/reviewer 用 Claude Code、claude-haiku-5-5、medium。'
                  '禁止 push、删除文件、改后台数据、绕过门禁；派发失败立即原样报错并停下，不轮询。')
        if args.scenario == 'c5':
            prompt = ('在 main 工作分支并行派两个受管任务，任务号 T-101、T-102。A 从 pantry.json 生成 pantry-summary.md，'
                      '按类别统计食材种类数和库存件数，文末总计全部种类和件数。为演练真实打回，A 首版故意漏掉总计，'
                      '必须等真实验收打回后再补齐，不能提前补。B 生成 shopping-list.md，只列零库存食材；'
                      '分组方式尚未决定，B 必须先通过问题上报问分组方式，等回答后再写文件和交付。'
                      '两个 worker 启动后结束本回合，让我检查和人工介入；不要 verify、集成或替我回答 B。' + common)
        else:
            prompt = (f'为两个文档写验收脚本，保存为 {fixture.out}/check_pantry.py 和 {fixture.out}/check_shopping.py。'
                      '均从运行时当前目录读取 pantry.json 与对应文档，成功退出 0，不满足条件正常退出非零，不能异常崩溃。'
                      'pantry-summary.md 要按类别给出种类数与库存件数，文末给出全部种类和库存总计；'
                      '排版没有指定，中文里数字语义正确即可。shopping-list.md 只列所有零库存食材，是需要购买的平铺列表，'
                      '不按类别分组（这是用户已经给出的答复）。不要创建任务、派 worker 或修改文档，写完结束本回合。' + common)
        write(fixture.out / 'prompts.json', dict(role=root_prompts(native_rows(controller_home)), scenario=prompt))
        before = len(root_prompts(native_rows(controller_home)))
        def stops():
            return [event for event in fixture.request('orchestration_events')['events']
                    if event['type'] == 'terminal_turn' and event['data'].get('hook_event_name') == 'Stop']
        stop_count = len(stops())
        submit(prompt)
        fixture.wait('场景提示写入原生日志', lambda: len(root_prompts(native_rows(controller_home))) > before, 60)
        # Wait for the real Stop hook, rather than a completion marker authored by the model.
        fixture.wait('新场景 Stop hook', lambda: len(stops()) > stop_count, 600)
        electron.until('场景完成', state + ' === "idle"', 600)
        rows = native_rows(controller_home)
        write(fixture.out / 'native-transcript.json', rows)
        models = sorted({row.get('message', {}).get('model', '') for row in rows if row.get('type') == 'assistant'})
        turns = root_prompts(rows)
        report.update(real_model_turns=len(turns), assistant_models=models)
        report['checks'].append(dict(name='real-haiku-two-root-prompts', passed=len(turns) == 2 and bool(models) and all('haiku' in m for m in models)))
        # Retain actual tool calls and cards, including any rejected drafts, for independent semantic review.
        report['cards'] = {}
        for task in ('T-101', 'T-102'):
            status = fixture.request('status', fixture.terminal, task=task)
            version = status.get('task', {}).get('card_version', 1)
            card = fixture.request('card_show', fixture.terminal, task=task, card_version=version)
            write(fixture.out / (task + '-registered.json'), dict(status=status, card=card))
            report['cards'][task] = dict(status=status, card=card)
        report['snapshot'] = fixture.request('sidebar_snapshot')
        electron.screenshot(fixture.out / 'scenario-finished.png')
        if args.scenario == 'oracle':
            oracle_probe(fixture, report)
            report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'NO_GO'
        else:
            report['checks'].append(dict(name='two-managed-workers-dispatched', passed=all(
                entry['status'].get('ok') and (entry['status'].get('task', {}).get('current_attempt') or {}).get('thread_id')
                for entry in report['cards'].values())))
            report['semantic_review_required'] = [
                '实际 A 卡含首版漏总计、真实验收拒绝后才修复；最终完成条件仍要求总计',
                '实际 B 卡含先上报、等待答复、然后写文件与交付的必需顺序',
                '原生工具记录或最终说明显示派发前主动逐项核对；有漏项须先纠正，无漏项列出核对结果',
                '两个真实 dispatch 成功；未 verify/集成、未替用户回答 B、未无新事实反复轮询',
            ]
            report['status'] = 'INCOMPLETE'
    except Exception as error:
        # Do not serialize arbitrary credential-bearing exceptions.
        detail = traceback.format_exc()
        report['error'] = detail.replace(secret, '[REDACTED]') if secret else f'{type(error).__name__}: setup failed before credential loaded'
    finally:
        for name, resource in [('electron', electron), ('fixture', fixture)]:
            if resource:
                try:
                    resource.stop()
                except Exception:
                    report.setdefault('cleanup_errors', []).append(name + ': stop failed; preserve instance')
                    report['status'] = 'INCOMPLETE'
        if controller_home:
            # Preserve the native transcript even when a scene fails before reaching its normal checkpoint.
            rows = native_rows(controller_home)
            report['real_model_turns'] = len(root_prompts(rows))
            if fixture and not (fixture.out / 'native-transcript.json').exists():
                write(fixture.out / 'native-transcript.json', rows)
            if report['real_model_turns'] > 2:
                report['status'] = 'INCOMPLETE'
                report['budget_error'] = '实际根回合超过本次预留；禁止继续运行'
            # The entire disposable native HOME may contain login backups; keep only the transcript above.
            shutil.rmtree(controller_home)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        write(args.summary, report)
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), fixture=report.get('fixture'),
                          real_model_turns=report.get('real_model_turns')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
