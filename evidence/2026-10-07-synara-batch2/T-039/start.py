import json
import os
from pathlib import Path
import secrets
import subprocess
from datetime import datetime, timezone

here = Path(__file__).resolve().parent
r = json.loads((here / 'runtime.json').read_text(encoding='utf-8'))
token = Path(r['root'], 'bootstrap-token')
token.write_text(secrets.token_urlsafe(32), encoding='utf-8')
token.chmod(0o600)
argv = ['./a2a/scripts/bun', 'run', str(here / 'launch.mjs'), '--home-dir', r['synara_home'],
        '--port', str(r['port']), '--host', '127.0.0.1', '--no-browser']
env = dict(os.environ, A2A_SYNARA_SLOT=r['slot'], CODEX_HOME=r['codex_home'])
for name in ('SYNARA_CLAUDE_KEEPALIVE', 'SYNARA_BETA_HOME', 'SYNARA_DESKTOP_BUNDLE_ID',
             'SYNARA_DESKTOP_PARENT_PID', 'SYNARA_MODE', 'SYNARA_DEV_URL',
             'VITE_DEV_SERVER_URL', 'SYNARA_AUTH_TOKEN'):
    env.pop(name, None)
with (here / 'server.log').open('x', encoding='utf-8') as stream:
    child = subprocess.Popen(argv, cwd='/Users/luckye/Documents/Code/synara', env=env,
                             stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                             start_new_session=True)
record = dict(time=datetime.now(timezone.utc).isoformat(), argv=argv, cwd='/Users/luckye/Documents/Code/synara',
              pid=child.pid, pgid=child.pid, start_new_session=True,
              runtime_env=dict(CODEX_HOME=r['codex_home'], SYNARA_HOME=r['synara_home'], A2A_SYNARA_SLOT=r['slot']))
with (here / 'server-start.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
