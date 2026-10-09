"""Preserve command, environment, versions and full output; refuse reused labels."""
import datetime, json, os, subprocess, sys
from pathlib import Path
out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label, *command = sys.argv[1:]
argv = ['./a2a/scripts/bun', *command]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = {**os.environ, 'A2A_SYNARA_SLOT': 't044'}
with (out / (label + '.log')).open('x', encoding='utf-8') as log:
    result = subprocess.run(argv, cwd=fork, env=env, stdout=log, stderr=subprocess.STDOUT)
with (out / (label + '.command.json')).open('x', encoding='utf-8') as stream:
    json.dump({'argv': argv, 'cwd': str(fork), 'start': start,
       'end': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit': result.returncode,
       'fork': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip(),
       'environment': {'A2A_SYNARA_SLOT': 't044'}}, stream, indent=2)
    stream.write('\n')
print(label, result.returncode)
raise SystemExit(result.returncode)
