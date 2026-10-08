import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from datetime import datetime, timezone

here = Path(__file__).resolve().parent
label = sys.argv[1]
assert os.environ.get('HERDR_ENV') == '1'
assert not (here / (label + '.json')).exists()
user = Path('/Users/luckye')

def metadata(path):
    if not path.exists() and not path.is_symlink():
        return {'path': str(path), 'exists': False}
    s = path.lstat()
    return dict(path=str(path), exists=True, size=s.st_size, mtime_ns=s.st_mtime_ns,
                directory=stat.S_ISDIR(s.st_mode), symlink=stat.S_ISLNK(s.st_mode))

config = [metadata(user / '.codex/config.toml'), metadata(user / '.codex/rules')]
rules = user / '.codex/rules'
if rules.is_dir() and not rules.is_symlink():
    config.extend(metadata(p) for p in sorted(rules.rglob('*')))
synara_paths = {user / name for name in ('.synara', '.synara-beta', '.synara-canary', '.synara-dev', '.synara-cua')}
synara_paths.update(user.glob('.synara*'))
support = user / 'Library/Application Support'
if support.is_dir():
    synara_paths.update(support.glob('Synara*'))
    synara_paths.update(support.glob('synara*'))
for name in ('SYNARA_HOME', 'SYNARA_BETA_HOME'):
    if os.environ.get(name):
        synara_paths.add(Path(os.environ[name]).expanduser())
synara = []
for p in sorted(synara_paths):
    entry = metadata(p)
    entry['top_level'] = [metadata(child) for child in sorted(p.iterdir())] if p.is_dir() else []
    synara.append(entry)
p = subprocess.run(['herdr', 'status'], text=True, capture_output=True, timeout=15)
value = dict(time=datetime.now(timezone.utc).isoformat(), codex_config_and_rules=config,
             synara_data=synara, herdr=dict(argv=p.args, exit=p.returncode, stdout=p.stdout, stderr=p.stderr),
             credential_content_read=False, kind='只读元数据与 status；未复制 config/rules 内容或凭据')
with (here / (label + '.json')).open('x', encoding='utf-8') as out:
    json.dump(value, out, ensure_ascii=False, indent=2)
    out.write('\n')
print(json.dumps({'label':label,'codex_entries':len(config),'synara_paths':len(synara),'herdr_exit':p.returncode}))
sys.exit(p.returncode)
