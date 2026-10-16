"""Read-only: every external-disk path referenced from batch13-15 evidence exists, reads fully, size matches recorded bytes when a pointer states it, gzip streams decompress."""
import json, os, re, sys, gzip, subprocess
from pathlib import Path
repo = Path('/Users/luckye/Documents/Code/a2a')
roots = ['evidence/2026-10-11-batch13', 'evidence/2026-10-14-batch14', 'evidence/2026-10-15-batch15']
pat = re.compile(r'/Volumes/WD-Elements/a2a-evidence/2026-10-1[145]-batch1[345]/[^\s"\'`)<>,\]（），。、；：\\]+')
refs = {}; sizes = {}
for r in roots:
    out = subprocess.run(['git', '-C', str(repo), 'grep', '-lI', 'WD-Elements/a2a-evidence', 'HEAD', '--', r], capture_output=True, text=True).stdout.split()
    for spec in out:
        f = spec.split(':', 1)[1]
        text = subprocess.run(['git', '-C', str(repo), 'show', spec], capture_output=True, text=True).stdout
        for m in pat.finditer(text):
            p = m.group(0).rstrip('.;:')
            refs.setdefault(p, set()).add(f)
        try:
            d = json.loads(text)
        except Exception:
            continue
        def walk(o):
            if isinstance(o, dict):
                a = o.get('archive') or o.get('external_archive') or o.get('archive_path')
                b = o.get('bytes') or o.get('archive_bytes') or o.get('size')
                if isinstance(a, str) and a.startswith('/Volumes/WD-Elements') and isinstance(b, int):
                    sizes.setdefault(a, set()).add(b)
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(d)
pass
# second pass for sizes (walk defined after use above is fine because sizes is global at call time)
for r in roots:
    for spec in subprocess.run(['git', '-C', str(repo), 'grep', '-lI', 'WD-Elements/a2a-evidence', 'HEAD', '--', r], capture_output=True, text=True).stdout.split():
        text = subprocess.run(['git', '-C', str(repo), 'show', spec], capture_output=True, text=True).stdout
        try: d = json.loads(text)
        except Exception: continue
        def walk(o):
            if isinstance(o, dict):
                a = o.get('archive') or o.get('external_archive') or o.get('archive_path')
                b = o.get('bytes') or o.get('archive_bytes') or o.get('size')
                if isinstance(a, str) and a.startswith('/Volumes/WD-Elements') and isinstance(b, int):
                    sizes.setdefault(a, set()).add(b)
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(d)
res = {'referenced': 0, 'files_ok': 0, 'dirs_ok': 0, 'missing': [], 'read_error': [], 'size_mismatch': [], 'gzip_bad': [], 'size_checked': 0}
for p in sorted(refs):
    res['referenced'] += 1
    P = Path(p)
    if not P.exists():
        res['missing'].append({'path': p, 'from': sorted(refs[p])[:3]}); continue
    if P.is_dir():
        res['dirs_ok'] += 1; continue
    try:
        n = 0
        with open(P, 'rb') as fh:
            while True:
                c = fh.read(1 << 20)
                if not c: break
                n += len(c)
    except OSError as e:
        res['read_error'].append({'path': p, 'error': repr(e)}); continue
    if p in sizes:
        res['size_checked'] += 1
        if n not in sizes[p]: res['size_mismatch'].append({'path': p, 'read': n, 'recorded': sorted(sizes[p])})
    if p.endswith('.gz'):
        try:
            with gzip.open(P, 'rb') as g:
                while g.read(1 << 20): pass
        except Exception as e:
            res['gzip_bad'].append({'path': p, 'error': repr(e)})
    res['files_ok'] += 1
# disk files not referenced from the repo
on_disk = []
for b in ['2026-10-11-batch13', '2026-10-14-batch14', '2026-10-15-batch15']:
    base = Path('/Volumes/WD-Elements/a2a-evidence') / b
    if base.exists():
        for dp, dn, fn in os.walk(base):
            for f in fn: on_disk.append(os.path.join(dp, f))
ref_set = set(refs)
unref = [f for f in on_disk if f not in ref_set and not any(f.startswith(r.rstrip('/') + '/') for r in ref_set)]
res['disk_files'] = len(on_disk); res['unreferenced_disk_files'] = unref[:20]; res['unreferenced_count'] = len(unref)
res['status'] = 'PASS' if not (res['missing'] or res['read_error'] or res['size_mismatch'] or res['gzip_bad']) else 'NO_GO'
print(json.dumps(res, ensure_ascii=False, indent=1))
