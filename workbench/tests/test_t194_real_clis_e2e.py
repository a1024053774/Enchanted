"""T-194：真实的 Codex、opencode 经 Enchanted 包装脚本带上 a2a 的 MCP 服务器，在项目终端里经 MCP 工具申请主控。
真实后台、socket、项目终端（zsh 与包装脚本），两家都是用户本机安装的真实 CLI 与真实模型（交互模式）。agy 不挂 MCP（交互模式下模型拿不到工具，见
findings/2026-10-27-mcp-per-session.zh-CN.md），继续用 a2a 命令；--clis agy 可复现这一点（应在第 1 条超时）。
Codex 按项目规则用 /tmp 下的隔离 CODEX_HOME：只复制 auth.json，只信任本夹具的仓库根目录；Enchanted 钩子的信任提示出现时，
由本测试在这个隔离 home 里逐次批准（记入摘要）；副本不入证据，结束后整个删除，不写用户的 ~/.codex。
opencode、agy 用用户自己的 HOME 与登录（T-187），本测试不往里写任何东西；agy 首次进入夹具目录时的信任框照常确认
（写入 ~/.gemini 的 trustedWorkspaces，是用户批准的例外）。

失败方式（先列再写）：
1. CLI 看不到 Enchanted 的 MCP 工具（包装脚本没传上配置、服务器起不来或拿不到终端身份），申请不会出现。
2. 申请没记在这个终端上，或记错 CLI。
3. Codex 的申请没带会话号，或带的不是这次 Codex 自己的线程号（独立来源：隔离 CODEX_HOME 里 rollout 首行 session_meta）。
4. 用户拒绝后 CLI 收不到结果（工具一直挂着），或没有角色的终端被当成主控。
--clis 选择要跑的 CLI；--revision 在该版本源码上跑（修前没有 MCP 服务器，应在第 1 条失败）。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture  # noqa: E402

PROMPT = 'T-194 实测：我本人要求你现在调用 enchanted MCP 服务器的 request_role 工具，参数 role 为 executor。只调用这一个工具，不要运行任何 shell 命令；工具返回后把结果原样告诉我。'
NAMES = {'codex': 'Codex', 'opencode': 'opencode', 'agy': 'agy'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--clis', default='codex,opencode')
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    clis = args.clis.split(',')
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, checks=[], observed={}, hook_trust_approvals=[])
    # The model is never the scripted one here: every CLI talks to its own provider.
    fixture = Fixture('t194-real-', lambda body: ('none', [], 'unused'), revision=args.revision, home=Path.home())
    codex_home = Path(tempfile.mkdtemp(prefix='t194-codex-home-', dir='/private/tmp')).resolve()

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def database(query, *values):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, values)]

    def screen(term):
        # agy (and possibly others) print the signed-in account's email; it never enters the summary.
        raw = (fixture.state / 'traces' / term['launch'] / 'pty.raw').read_text(encoding='utf-8', errors='replace')
        raw = re.sub(r'[\w.+-]+@[\w-]+(\.[\w-]+)+', '<email>', raw)
        return re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw)

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def submit(term, text):
        type_in(term, text)
        time.sleep(1.5)
        type_in(term, '\r')

    def terminal():
        launch = fixture.run_cli('shell_start', '--project', fixture.project, '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=fixture.project)
        assert window['ok'], window
        return dict(launch=launch, identity=window['identity'], sequence=0)

    def requested(term):
        return [json.loads(row['data']) for row in database("SELECT data FROM orchestration_events WHERE type='role_requested' AND launch=?", term['launch'])]

    def codex_threads():
        # Codex's own record of its threads in this run's home: the first line of each rollout file.
        threads = []
        for path in (codex_home / 'sessions').rglob('rollout-*.jsonl'):
            first = json.loads(path.read_text(encoding='utf-8').splitlines()[0])
            if first.get('type') == 'session_meta' and first['payload'].get('cwd') == str(fixture.repo):
                threads.append(first['payload']['id'])
        return threads

    try:
        shutil.copyfile(Path.home() / '.codex/auth.json', codex_home / 'auth.json')
        (codex_home / 'auth.json').chmod(0o600)
        config = dict(claude_bin=shutil.which('claude') or str(Path.home() / '.local/bin/claude'), role_card=str(fixture.source / 'workbench/roles/worker.md'),
                      role_card_revision='fixture', reviewer_role_card=str(fixture.source / 'workbench/roles/reviewer.md'),
                      reviewer_role_card_revision='fixture', code_revision='fixture', hook_authorization='fixture: hooks only through launch arguments', turn_limit=6)
        (fixture.dir / 'launch-config.json').write_text(json.dumps(config), encoding='utf-8')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.running = True
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 10)
        fixture.operator = json.loads((fixture.dir / 'operator.json').read_text(encoding='utf-8'))
        fixture.git('init', '-q', '-b', 'main')
        (fixture.repo / 'README.md').write_text('demo\n', encoding='utf-8')
        fixture.git('add', '.')
        fixture.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-q', '-m', 'init')
        (codex_home / 'config.toml').write_text(f'[projects."{fixture.repo}"]\ntrust_level = "trusted"\n', encoding='utf-8')
        report['codex_home'] = dict(files=['auth.json (copy)', 'config.toml (trusts the fixture repo only)'])
        assert fixture.request('project_open', fixture.operator, repo=str(fixture.repo))['ok']

        for cli in clis:
            term = terminal()
            started = time.monotonic()
            if cli == 'codex':
                type_in(term, f'CODEX_HOME={codex_home} codex -m gpt-6.1-sol -c model_reasoning_effort=high\r')
            elif cli == 'opencode':
                type_in(term, 'opencode\r')
            else:
                type_in(term, 'agy\r')
            sent = False
            while not requested(term):
                text = screen(term)
                tail = text[-1500:]
                # Codex asks once per home to trust Enchanted's hooks (shim comment, T-133); agy asks to trust a new folder.
                if cli == 'codex' and re.search(r'Trust\s*all\s*and\s*continue', tail) and not term.get('hooks_trusted'):
                    term['hooks_trusted'] = True
                    report['hook_trust_approvals'].append(dict(cli=cli, at=time.strftime('%H:%M:%S'), screen_tail=tail[-300:], choice='2 Trust all and continue',
                                                               reason='isolated CODEX_HOME of this run; the hooks are the Enchanted shim\'s own'))
                    type_in(term, '2')
                    time.sleep(1)
                    type_in(term, '\r')
                    time.sleep(2)
                    continue
                if cli == 'agy' and re.search(r'[Tt]rust (this )?(folder|workspace)', tail) and not term.get('trusted'):
                    term['trusted'] = True
                    report['observed'].setdefault('agy_trust', tail[-300:])
                    type_in(term, '\r')
                    time.sleep(2)
                    continue
                if not sent and time.monotonic() - started > 20:
                    submit(term, PROMPT)
                    sent = True
                assert time.monotonic() - started < 300, f'{cli}：超时，没有出现经 MCP 的角色申请；屏幕末尾：{tail[-800:]}'
                time.sleep(1)
            asked = requested(term)
            pending = fixture.wait(f'{cli} 的申请进待批', lambda: [row for row in fixture.request('sidebar_snapshot').get('role_requests', [])
                                                                   if row.get('launch') == term['launch']], 30)
            assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=False)['ok']
            seen = dict(cli=asked[0].get('cli'), native_session=asked[0].get('native_session'), requests=len(asked))
            if cli == 'codex':
                seen['codex_threads'] = fixture.wait('Codex 写出线程记录', codex_threads, 60)
            # The CLI gets the refusal back: the denial reaches its screen.
            fixture.wait(f'{cli} 收到拒绝', lambda: any(word in screen(term)[-6000:] for word in ('role_request_denied', 'denied', '拒绝', 'rejected')), 120)
            report['observed'][cli] = seen
            check(f'{cli}_mcp_reaches_this_terminal', len(asked) == 1 and seen['cli'] == cli, seen)
            if cli == 'codex':
                check('codex_session_is_its_thread', seen['codex_threads'] == [seen['native_session']], seen)
            else:
                check(f'{cli}_no_made_up_session', not seen['native_session'], seen)
            roles = database("SELECT data FROM orchestration_events WHERE type='role_request_confirmed' AND launch=?", term['launch'])
            check(f'{cli}_denied_terminal_has_no_role', not roles, roles)
            type_in(term, '\x03')
            time.sleep(1)
            type_in(term, '\x03')
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        try:
            fixture.stop()
        finally:
            shutil.rmtree(codex_home, ignore_errors=True)
            report['codex_home_removed'] = not codex_home.exists()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
