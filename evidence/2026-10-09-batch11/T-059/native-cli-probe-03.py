"""Run only version/help on the installed native CLI with an empty private home."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

out = Path(__file__).resolve().parent / sys.argv[1]
out.mkdir()
root = Path(tempfile.mkdtemp(prefix='a2a-t059-cli-probe-', dir='/tmp')).resolve()
for name in ('home', 'config', 'secure-storage', 'workspace'):
    (root / name).mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
env.update(HOME=str(root / 'home'), CLAUDE_CONFIG_DIR=str(root / 'config'),
           CLAUDE_SECURESTORAGE_CONFIG_DIR=str(root / 'secure-storage'),
           DISABLE_AUTOUPDATER='1', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
binary = '/Users/luckye/.local/bin/claude'
for name, args in [('version', ['--version']), ('help', ['--help'])]:
    proc = subprocess.run([binary, *args], cwd=root / 'workspace', env=env,
                          stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=30)
    with (out / (name + '-command.json')).open('x', encoding='utf-8') as stream:
        json.dump(dict(argv=proc.args, cwd=str(root / 'workspace'), environment=env,
                       exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr,
                       model_prompts=0), stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    proc.check_returncode()
with (out / 'owned-files.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(root=str(root), created_files=[str(path.relative_to(root))
              for path in root.rglob('*') if path.is_file()], model_prompts=0,
              user_credentials_read=False, scope='Version/help only; no query, login, or auth status'), stream, indent=2)
    stream.write('\n')
print('PASS: isolated native CLI version/help; model prompts = 0')
