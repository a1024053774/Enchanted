"""No-model native probe: excluded user settings must not suppress explicitly supplied MCP.

Failure modes: source isolation hides MCP; native --mcp-config cannot read .claude.json;
server never completes tools/list. The server log is independent of CLI screen text.
"""
import argparse
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default='/Users/luckye/.local/bin/claude')
    args = parser.parse_args()
    if args.summary.exists():
        parser.error('Fresh summary path required')
    root = Path(tempfile.mkdtemp(prefix='t141-mcp-probe-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', fixture=str(root), cases=[])
    try:
        for name in ['excluded', 'explicit']:
            home = root / name
            home.mkdir()
            receipt = home / 'protocol.jsonl'
            server = home / 'server.py'
            server.write_text('''import json,sys,pathlib
for line in sys.stdin:
 r=json.loads(line)
 pathlib.Path(sys.argv[1]).open('a').write(json.dumps(r)+'\\n')
 if 'id' not in r: continue
 method=r.get('method')
 if method=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'t141-probe','version':'1'}}
 elif method=='tools/list': result={'tools':[{'name':'ping','description':'T141 probe','inputSchema':{'type':'object','properties':{}}}]}
 else: result={}
 print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':result}),flush=True)
''', encoding='utf-8')
            config = home / '.claude.json'
            config.write_text(json.dumps(dict(hasCompletedOnboarding=True,
                projects={str(home): dict(hasTrustDialogAccepted=True)},
                mcpServers={'t141_user': dict(command='/usr/bin/python3', args=[str(server), str(receipt)])})), encoding='utf-8')
            argv = [args.claude, '--setting-sources', '', '--permission-mode', 'dontAsk']
            if name == 'explicit':
                argv += ['--mcp-config', str(config)]
            env = dict(os.environ, HOME=str(home), ANTHROPIC_BASE_URL='http://127.0.0.1:65535',
                       ANTHROPIC_AUTH_TOKEN='t141-no-model', DISABLE_AUTOUPDATER='1', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
            for key in ['CLAUDE_CONFIG_DIR', 'CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT']:
                env.pop(key, None)
            master, slave = pty.openpty()
            child = None
            raw = bytearray()
            try:
                child = subprocess.Popen(argv, cwd=home, env=env, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
                os.close(slave)
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline and child.poll() is None:
                    if select.select([master], [], [], .2)[0]:
                        try:
                            raw.extend(os.read(master, 65536))
                        except OSError:
                            break
                    if receipt.exists() and 'tools/list' in receipt.read_text():
                        break
                methods = [json.loads(line).get('method') for line in receipt.read_text().splitlines()] if receipt.exists() else []
                report['cases'].append(dict(name=name, argv=argv, methods=methods, pid=child.pid, exit_code=child.poll(),
                    status='PASS' if child.poll() is None and ('tools/list' in methods) == (name == 'explicit') else 'INCOMPLETE'))
            finally:
                if child and child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=10)
                os.close(master)
                (home / 'pty.raw').write_bytes(raw)
        report['status'] = 'PASS' if all(row['status'] == 'PASS' for row in report['cases']) else 'INCOMPLETE'
    finally:
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
