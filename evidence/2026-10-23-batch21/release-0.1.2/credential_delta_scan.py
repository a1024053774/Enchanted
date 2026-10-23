"""Before pushing: scan every blob, commit and tag reachable from main but not origin/main with T-101's TOKEN_RULES; hits not in the
exemption list (T-114's plus the fixture strings read in credential-scan-01) (object + offset) block the push. Also refuse credential file names anywhere in the delta."""
import json, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'evidence/2026-10-19-batch17/T-101'))
from slim_history import scan_bytes, credential_exemptions  # noqa: E402
out = Path(sys.argv[1]); assert not out.exists()
exempt = credential_exemptions(root / 'evidence/2026-10-23-batch21/release-0.1.2/credential-exemptions-03.json')
git = lambda *a: subprocess.run(['git', '-C', str(root), *a], capture_output=True, check=True).stdout
rows = [line.split(' ', 1) for line in git('rev-list', '--objects', 'origin/main..main').decode().splitlines()]
blobs, names, hits = 0, [], []
for oid, *path in rows:
    kind = git('cat-file', '-t', oid).strip()
    # Commit messages and annotated tags can carry a token too (review-01 P0); trees only hold names, checked below.
    if kind in (b'commit', b'tag'):
        hits += [dict(object=oid, path='(' + kind.decode() + ')', **hit) for hit in scan_bytes(git('cat-file', kind.decode(), oid))
                 if (oid, hit['offset']) not in exempt]
        continue
    if kind != b'blob': continue
    blobs += 1
    name = path[0] if path else ''
    if Path(name).name in ('auth.json', 'operator.json', '.credentials.json', 'credentials.json', '.netrc') or name.endswith('.pem'):
        names.append(name)
    for hit in scan_bytes(git('cat-file', 'blob', oid)):
        if (oid, hit['offset']) not in exempt: hits.append(dict(object=oid, path=name, **hit))
report = dict(range='origin/main..main', head=git('rev-parse', 'main').decode().strip(), origin=git('rev-parse', 'origin/main').decode().strip(),
              commits=int(git('rev-list', '--count', 'origin/main..main')), blobs=blobs, credential_file_names=names, unexempted_hits=hits,
              status='PASS' if not hits and not names else 'NO_GO')
out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'unexempted_hits'} | {'hits': len(hits)}, ensure_ascii=False))
