"""T-194 审查 F1：MCP 客户端关闭服务器输入（MCP stdio 的正常关闭方式）时，在途的角色申请随之撤回，之后用户批准也不生效。
真实后台、真实项目终端身份、真实 `a2a mcp codex` 进程（terminalCli.ts），客户端是本测试按 MCP 协议写 JSON-RPC；不调用模型。

失败方式（先列再写）：
1. 关闭输入后申请仍在待批，用户批准后服务器照样确认，终端拿到角色（审查 F1）。
2. 发 notifications/cancelled 取消调用后申请没撤回（既有正例，不能被修坏）。
3. 正常申请、批准后角色不生效（修坏了确认）。
5. 关闭输入后服务器仍写出被中止调用的回包（第 2 轮 F2）；客户端不再读输出时，调用结束写回包触发未处理的 EPIPE，服务器以
   非零退出码崩溃（F2）。
4. 批准已回来、确认还没发出时客户端关闭：确认仍发出去（窗口太窄，端到端卡不准；单独检查 requestAt 收到已中止的信号时
   不建连接、不发送，用一个只记连接的 Unix socket 作对端）。
预期来自契约：调用方停止等待即撤回（T-121 起 `a2a request` 的语义）、MCP 规范的 stdio 关闭顺序（先关输入）。
--revision 在该版本源码上跑（494d859 应在第 1 条失败）；--mutant 跑已知坏实现。
"""
import argparse
import json
from pathlib import Path
import selectors
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture  # noqa: E402

MUTANTS = {
    # Closing the input leaves the calls in flight running.
    'close-keeps-calls': [('src/terminalMcp.ts', ' for (const controller of calls.values()) controller.abort();', '')],
    # A request whose caller already stopped is still sent.
    'aborted-still-sent': [('src/transport.ts', '    if (signal?.aborted) return reject(new Error("cancelled by the caller before sending; not sent"));\n', '')],
    # The answer of a call stopped by the close is still written.
    'writes-after-close': [('src/terminalMcp.ts', '{ if (open) process.stdout.write(', '{ process.stdout.write(')],
    # A client that stops reading the output leaves the write error unhandled.
    'stdout-error-unhandled': [('src/terminalMcp.ts', '  process.stdout.on("error", error => {', '  process.stdout.on("unused", error => {')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], observed={})
    fixture = Fixture('t194-life-', lambda body: ('unused', [], ''), revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
    children = []

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def whoami():
        return fixture.request('terminal_whoami', fixture.terminal)

    def send(child, message):
        child.stdin.write(json.dumps({'jsonrpc': '2.0', **message}) + '\n')
        child.stdin.flush()

    def read(child, timeout=10):
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(timeout), 'MCP 服务器没有按时回复'
        return json.loads(child.stdout.readline())

    def start():
        # The daemon puts the terminal socket under TMPDIR, which this test points at the fixture.
        env = {**fixture.env, 'A2A_TERMINAL_SOCKET': str(next(fixture.dir.glob('enchanted-*/terminal.sock'))),
               'A2A_TERMINAL': fixture.terminal_launch, 'A2A_TERMINAL_TOKEN': fixture.terminal['token']}
        child = subprocess.Popen(['node', str(fixture.source / 'workbench/src/terminalCli.ts'), 'mcp', 'codex'], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
        children.append(child)
        send(child, {'id': 0, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {},
                                                                 'clientInfo': {'name': 't194-lifecycle', 'version': '1'}}})
        assert read(child)['result']['serverInfo']['name'] == 'enchanted'
        send(child, {'method': 'notifications/initialized'})
        return child

    def ask(child, ident):
        send(child, {'id': ident, 'method': 'tools/call', 'params': {'name': 'request_role', 'arguments': {'role': 'executor'},
                                                                     '_meta': {'threadId': f'thread-{ident}'}}})
        return fixture.wait('申请进待批', lambda: next((row for row in whoami()['role_requests'] if row['state'] == 'pending'), None), 15)

    def state_of(request_id):
        return next((row for row in whoami()['role_requests'] if row['id'] == request_id), None)

    try:
        fixture.env['TMPDIR'] = str(fixture.dir)
        fixture.start('/usr/bin/true', {'README.md': 't194 lifecycle\n'})
        # start() approves the terminal once; this test asks again through MCP.
        assert fixture.request('role_release', fixture.terminal)['ok']

        # 1: the client closes the server's input while the request waits; a later approval must not take effect.
        child = start()
        pending = ask(child, 1)
        child.stdin.close()
        ended = fixture.wait('关闭输入后申请撤回', lambda: (lambda row: row if row and row['state'] != 'pending' else None)(state_of(pending['id'])), 10)
        decision = fixture.request('role_request_decide', fixture.operator, role_request=pending['id'], approved=True)
        child.wait(timeout=10)
        time.sleep(1)
        after = whoami()
        report['observed']['eof'] = dict(request=ended, late_decision=decision, role=after.get('role'), exit=child.returncode,
                                         stdout_after_close=child.stdout.read(), stderr=child.stderr.read())
        check('eof_withdraws_pending_request', ended['state'] == 'ended' and decision.get('ok') is False and not after.get('role'),
              report['observed']['eof'])
        check('eof_ends_quietly', report['observed']['eof']['stdout_after_close'] == '' and child.returncode == 0 and
              not report['observed']['eof']['stderr'], report['observed']['eof'])

        # 5: the client stops reading the output while the request waits; the user's answer then has nowhere to go.
        child = start()
        pending = ask(child, 5)
        child.stdout.close()
        denied = fixture.request('role_request_decide', fixture.operator, role_request=pending['id'], approved=False)
        child.wait(timeout=10)
        report['observed']['output_closed'] = dict(decision=denied, request=state_of(pending['id']), role=whoami().get('role'),
                                                   exit=child.returncode, stderr=child.stderr.read())
        check('output_closed_ends_quietly', denied.get('ok') and not report['observed']['output_closed']['role'] and child.returncode == 0 and
              'Unhandled' not in report['observed']['output_closed']['stderr'], report['observed']['output_closed'])

        # 2: an explicit cancellation still withdraws.
        child = start()
        pending = ask(child, 2)
        send(child, {'method': 'notifications/cancelled', 'params': {'requestId': 2}})
        answer = json.loads(read(child)['result']['content'][0]['text'])
        cancelled = fixture.wait('取消后申请撤回', lambda: (lambda row: row if row and row['state'] == 'ended' else None)(state_of(pending['id'])), 10)
        report['observed']['cancel'] = dict(answer=answer, request=cancelled)
        check('cancel_withdraws_pending_request', answer.get('error') == 'outcome_unknown' and cancelled['state'] == 'ended', report['observed']['cancel'])

        # 3: a request the user approves while the client waits takes effect, with the session the call named.
        pending = ask(child, 3)
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending['id'], approved=True)['ok']
        granted = json.loads(read(child, 30)['result']['content'][0]['text'])
        after = whoami()
        report['observed']['approved'] = dict(answer=granted, role=after.get('role'))
        check('approved_request_takes_effect', granted.get('ok') is True and after.get('role') == 'executor', report['observed']['approved'])
        child.stdin.close()
        child.wait(timeout=10)

        # 4: a request whose caller has already stopped is not sent at all.
        import socket as sockets
        import threading
        path = fixture.dir / 'peer.sock'
        peer = sockets.socket(sockets.AF_UNIX)
        peer.bind(str(path)); peer.listen(1); peer.settimeout(3)
        connected = []
        def accept():
            try:
                connection = peer.accept()[0]
                connected.append(connection.recv(65536))
                connection.close()
            except OSError:
                pass  # no connection before the socket closed: what the check expects
        threading.Thread(target=accept, daemon=True).start()
        script = ("import { requestAt } from %s; const c = new AbortController(); c.abort();"
                  "requestAt(%s, { command: 'role_request_confirm' }, undefined, undefined, c.signal)"
                  ".then(() => console.log('sent'), e => console.log('refused: ' + e.message));") % (
                      json.dumps(str(fixture.source / 'workbench/src/transport.ts')), json.dumps(str(path)))
        ran = subprocess.run(['node', '--input-type=module', '-e', script], capture_output=True, text=True, timeout=20, env=fixture.env)
        time.sleep(1)
        peer.close()
        report['observed']['aborted_request'] = dict(stdout=ran.stdout.strip(), connections=len(connected))
        check('aborted_request_not_sent', ran.stdout.startswith('refused') and not connected, report['observed']['aborted_request'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=5)
        fixture.stop()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
