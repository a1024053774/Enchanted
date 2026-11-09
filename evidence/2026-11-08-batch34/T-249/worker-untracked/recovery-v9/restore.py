#!/usr/bin/env python3
"""按原始字节与执行位三方恢复；先预检全部路径，冲突时不写产品。"""
import argparse, datetime, json, os, pathlib, shutil, subprocess, tempfile
B = '3577086056eb33e4a0c3bd2d16bbc3b30862778c'
C = 'd8f55c958d901d052e79eda1a04dbf0a8fbf5ed5'
BASE = '62faa87b9424e48a4739920b53920d111a057486'
OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[4]
ALLOWED = ('workbench/app/', 'workbench/tests/', 'evidence/2026-11-07-batch33/T-249/', 'evidence/2026-11-08-batch34/T-249/worker-untracked/')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
def entry(rev, path):
    line = git('ls-tree', rev, '--', path)
    if not line: return None, None
    mode = int(line.split()[0], 8) & 0o777
    return git('show', rev + ':' + path), mode
def save(name, data):
    target = OUT / name
    with target.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2); f.write('\n')
def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--apply', action='store_true'); args = parser.parse_args()
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    source = 'evidence/2026-11-09-batch35/T-249/controller-package/verify-v7.json'
    attempt = json.loads(git('show', BASE+':'+source))['result']['task']['current_attempt']
    assert attempt['attempt_id'] == 'f8b6b251-7ad4-4eb8-98da-3c91ca4a581f' and attempt['base_commit'] == B
    delta = git('diff', '--name-status', '--no-renames', B, C).decode()
    paths = [line.split('\t')[1] for line in delta.splitlines()]
    assert all(p == 'workbench/README.md' or p.startswith(ALLOWED) for p in paths)
    assert all(not p.endswith(('RecordsPage.tsx', 'records.css')) for p in paths)
    rows, writes, conflicts = [], [], []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='t249-restore-v9-', dir=os.environ['A2A_REQUEST_DIR']))
    try:
        for path in paths:
            b,bm = entry(B,path); c,cm = entry(C,path); h,hm = entry(BASE,path)
            target = ROOT/path
            if target.exists():
                assert not target.is_symlink() and target.read_bytes() == h, 'dirty path: '+path
            if h == b: merged, method = c, 'current_equals_B'
            elif c == b or h == c: merged, method = h, 'keep_current'
            elif None in (h,b,c):
                conflicts.append(path); continue
            else:
                assert path == 'workbench/README.md', 'unexpected overlap: '+path
                for name, content in [('current',h),('base',b),('candidate',c)]: (tmp/name).write_bytes(content)
                result = subprocess.run(['/usr/bin/diff3','-m',str(tmp/'current'),str(tmp/'base'),str(tmp/'candidate')],capture_output=True)
                if result.returncode:
                    (OUT/'conflict.txt').write_bytes(result.stdout+result.stderr); conflicts.append(path); continue
                merged, method = result.stdout, 'diff3_clean_merge'
            mode = cm if hm == bm else hm
            if hm != bm and cm != bm and hm != cm: conflicts.append(path); continue
            assert merged is not None and mode in (0o644,0o755)
            rows.append(dict(path=path, method=method, bytes=len(merged), mode=oct(mode), candidate_bytes_equal=merged==c, candidate_mode_equal=mode==cm))
            writes.append((target,merged,mode))
        report = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(), base=BASE, B=B, C=C,
          B_source=source, source_attempt=attempt['attempt_id'], paths=rows, conflicts=conflicts, apply=args.apply)
        report['temporary_cleanup'] = dict(directory=str(tmp), files=sum(x.is_file() for x in tmp.rglob('*')),
          bytes=sum(x.stat().st_size for x in tmp.rglob('*') if x.is_file()), removed=True)
        save('application.json' if args.apply else 'preflight.json',report)
        assert not conflicts, conflicts
        if args.apply:
            for target,content,mode in writes:
                target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(content); target.chmod(mode)
            assert all(t.read_bytes()==content and t.stat().st_mode & 0o777==mode for t,content,mode in writes)
        print(json.dumps(dict(paths=len(rows), conflicts=conflicts, candidate_differences=[r['path'] for r in rows if not r['candidate_bytes_equal']], applied=args.apply),ensure_ascii=False))
    finally:
        shutil.rmtree(tmp)
if __name__ == '__main__': main()
