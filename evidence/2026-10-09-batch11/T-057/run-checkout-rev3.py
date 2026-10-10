import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
label, checkout, *args = sys.argv[1:]
checkout = Path(checkout).resolve()
assert checkout == Path('/Users/luckye/Documents/Code/synara-t057-notify')
assert Path('/Volumes/WD-Elements').is_mount()
argv = ['./a2a/scripts/bun', *args]
record = dict(argv=argv, cwd=str(checkout), started=dt.datetime.now(dt.timezone.utc).isoformat(),
    revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip(),
    space_before=subprocess.check_output(['df', '-h', '/', '/Volumes/WD-Elements'], text=True))
env = {**os.environ, 'A2A_SYNARA_SLOT': 't057-notify-rev3'}
with (out / (label + '.log')).open('x', encoding='utf-8') as log:
    result = subprocess.run(argv, cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT)
record.update(exit=result.returncode, ended=dt.datetime.now(dt.timezone.utc).isoformat(),
    space_after=subprocess.check_output(['df', '-h', '/', '/Volumes/WD-Elements'], text=True))
with (out / (label + '.command.json')).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(label, result.returncode)
sys.exit(result.returncode)
