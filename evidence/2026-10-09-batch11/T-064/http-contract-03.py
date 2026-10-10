import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

out = Path(__file__).resolve().parent
label = sys.argv[1]
launch = json.loads((out / ('server-' + label + '-launch.json')).read_text(encoding='utf-8'))
origin = json.loads((Path(launch['root']) / 'ready.json').read_text(encoding='utf-8'))['origin']
url = origin + '/api/a2a/role-permissions'
try:
    response = urllib.request.urlopen(url, timeout=20)
except urllib.error.HTTPError as error:
    response = error
with response:
    status = response.status
    body = response.read().decode('utf-8')
record = dict(url=url, status=status, body=body,
    expected={'status': 200, 'roles': ['executor', 'ideation', 'worker', 'reviewer', 'monitor']},
    replay='python3 evidence/2026-10-09-batch11/T-064/http-contract-03.py NEW_LABEL')
with (out / ('http-contract-' + label + '.json')).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
assert status == 200, 'T-064 requires a readable role permission settings endpoint'
assert [row['role'] for row in json.loads(body)['roles']] == record['expected']['roles']
