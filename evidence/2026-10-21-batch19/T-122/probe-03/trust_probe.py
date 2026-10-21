import os, pty, sys, time, select, re, json, uuid, signal
cwd, extra = sys.argv[1], sys.argv[2:]
os.makedirs(cwd, exist_ok=True)
argv = ['claude', '--session-id', str(uuid.uuid4()), '--model', 'claude-haiku-5-5', '--permission-mode', 'dontAsk',
        '--setting-sources', 'local', '--strict-mcp-config', *extra]
pid, fd = pty.fork()
if pid == 0:
    os.chdir(cwd); os.execvp(argv[0], argv)
out = b''; end = time.time() + 15
while time.time() < end:
    r, _, _ = select.select([fd], [], [], .3)
    if r:
        try: out += os.read(fd, 65536)
        except OSError: break
text = re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07', '', out.decode('utf8', 'replace'))
os.kill(pid, signal.SIGKILL)
print(json.dumps({'cwd': cwd, 'extra': extra, 'trust_dialog': 'trustthisfolder' in text.replace(' ','').lower(), 'tail': text[-900:]}, ensure_ascii=False))
