"""Record controller command evidence without replacing any earlier output."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    argv = sys.argv[1:]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(argv, text=True, capture_output=True)
    row = {'started_at': start, 'finished_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    with (Path(__file__).parent / 'commands.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(p.stdout, end='')
    print(p.stderr, end='', file=sys.stderr)
    sys.exit(p.returncode)
