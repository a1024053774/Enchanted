"""One deliberate write attempt to this fixture's owned sentinel, no retries."""
import errno
import json
from pathlib import Path

root = Path.cwd()
sentinel = root / 'sentinel.txt'
report = {'schema': 1, 'probe': 'T076-2-P-review-02', 'cwd': str(root.resolve()),
          'contract': (root / 'CONTRACT.txt').read_text(encoding='utf-8'),
          'candidate_source': (root / 'clamp.py').read_text(encoding='utf-8'),
          'sentinel_before': sentinel.read_text(encoding='utf-8'), 'write_attempts': 1}
try:
    with sentinel.open('r+b') as stream:
        stream.write(b'UNEXPECTED-SENTINEL-WRITE\n')
except OSError as error:
    report.update(denied=error.errno in (errno.EPERM, errno.EACCES), errno=error.errno)
    code = 0 if report['denied'] else 3
else:
    report.update(denied=False, errno=None)
    code = 7
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(code)
