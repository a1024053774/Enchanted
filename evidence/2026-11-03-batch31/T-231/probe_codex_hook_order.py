"""T-231 probe: with the real Codex CLI in a terminal and a worker's UserPromptSubmit hook argument, does the rollout
file name the session (session_meta) before the hook fires, and does terminal output arrive in between? The product
binds a Codex worker's session by scanning on terminal output (panes.ts onData), so the hook is refused only if it
arrives before any such scan. No vendor calls: the model provider is a closed local port; CODEX_HOME is a fresh
directory under /private/tmp with no credentials, deleted afterwards. Usage: probe_codex_hook_order.py OUTPUT.json"""
import json, os, pty, select, shutil, subprocess, sys, tempfile, time
from pathlib import Path

out = Path(sys.argv[1]); assert not out.exists()
root = Path(tempfile.mkdtemp(prefix='t231-codex-', dir='/private/tmp')).resolve()
home, ws, log = root / 'codex-home', root / 'ws', root / 'hook.jsonl'
home.mkdir(mode=0o700); ws.mkdir()
subprocess.run(['git', 'init', '-q', str(ws)], check=True)
(home / 'config.toml').write_text(f'[projects.{json.dumps(str(ws))}]\ntrust_level="trusted"\n'
    '[model_providers.probe]\nname="closed port"\nbase_url="http://127.0.0.1:9/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
hook_script = root / 'hook.py'
hook_script.write_text(f'''import json,sys,time,pathlib
t=time.time(); raw=sys.stdin.read(); v=json.loads(raw)
files=[str(p) for p in pathlib.Path({str(home)!r},'sessions').rglob('*.jsonl')]
meta=any('"session_meta"' in pathlib.Path(f).read_text() for f in files)
with open({str(log)!r},'a') as s: s.write(json.dumps(dict(t=t,event=v.get('hook_event_name'),session_id=v.get('session_id'),files=files,session_meta_present=meta))+"\\n")
''', encoding='utf-8')
hook = f'[{{hooks=[{{type="command",command={json.dumps(sys.executable + " " + str(hook_script))},timeout=10}}]}}]'
argv = ['codex', '--no-alt-screen', '-C', str(ws), '-a', 'never', '--sandbox', 'workspace-write', '-c', 'model_provider="probe"',
        '-c', 'check_for_update_on_startup=false', '-c', f'hooks.UserPromptSubmit={hook}', '--dangerously-bypass-hook-trust']
env = {k: os.environ[k] for k in ('PATH', 'LANG', 'TERM', 'TMPDIR') if k in os.environ}
env.update(CODEX_HOME=str(home), HOME=str(root), TERM='xterm-256color')
report = dict(argv=argv, version=subprocess.check_output(['codex', '--version'], text=True).strip(), output=[], meta_seen_at=None)
pid, fd = pty.fork()
if pid == 0:
    os.chdir(ws); os.execvpe('codex', argv, env)
start = time.time(); typed = None
def meta_present():
    return any('"session_meta"' in p.read_text() for p in (home / 'sessions').rglob('*.jsonl')) if (home / 'sessions').exists() else False
try:
    while time.time() - start < 40:
        ready, _, _ = select.select([fd], [], [], .02)
        now = time.time()
        if ready:
            try: data = os.read(fd, 65536)
            except OSError: break
            report['output'].append(dict(t=round(now - start, 3), bytes=len(data)))
            if b'\x1b[6n' in data: os.write(fd, b'\x1b[1;1R')  # answer the cursor position query a terminal answers
        if report['meta_seen_at'] is None and meta_present(): report['meta_seen_at'] = round(now - start, 3)
        if typed is None and now - start > 8:
            os.write(fd, 'reply hi'.encode()); time.sleep(.3); os.write(fd, b'\r'); typed = round(time.time() - start, 3)
        if typed and log.exists() and now - start > typed + 5: break
finally:
    os.kill(pid, 9); os.waitpid(pid, 0)
report['typed_at'] = typed
report['hooks'] = [dict(json.loads(l), t=round(json.loads(l)['t'] - start, 3)) for l in log.read_text().splitlines()] if log.exists() else []
first_hook = report['hooks'][0]['t'] if report['hooks'] else None
meta = report['meta_seen_at']
report['output_between_meta_and_hook'] = None if first_hook is None or meta is None else \
    [o for o in report['output'] if meta <= o['t'] <= first_hook]
report['summary'] = dict(meta_seen_at=meta, first_hook_at=first_hook, session_meta_present_in_hook=report['hooks'][0]['session_meta_present'] if report['hooks'] else None,
                         output_chunks_between=len(report['output_between_meta_and_hook'] or []))
out.write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
print(json.dumps(report['summary']))
shutil.rmtree(root)
