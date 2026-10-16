# -*- coding: utf-8 -*-
"""Executor-written /private/tmp fixture cleanup. Default is a dry run; --delete removes the listed entries.
Selection: owner is the current user, name matches an a2a test-fixture prefix, not in the keep list,
not modified in the last 30 minutes, not referenced by any running process command line."""
import argparse, json, os, re, shutil, subprocess, time
from pathlib import Path

TMP = Path('/private/tmp')
PREFIX = re.compile(r'^(a2a-|t78|t078|t073|q76|q81obs|t081|t81|t084|t077|t77p|t80|s3f-|s3-|s76|a4r-|a76|m76-|r77-)')
KEEP_EXACT = {'t078-2-09b-run-jyat2h5s', 't078-2-09b-executable-h12u7zgs', 'claude-501', 'cc-socks'}
KEEP_PREFIX = ('t081-capability-recheck-', 't081-capability-01', 't081-commit-scope')
RECENT_SECONDS = 30 * 60


def tree_stats(path):
    size, newest, creds = 0, path.lstat().st_mtime, []
    for root, dirs, files in os.walk(path, followlinks=False):
        for name in files + dirs:
            p = Path(root) / name
            try:
                st = p.lstat()
            except FileNotFoundError:
                continue
            size += st.st_size
            newest = max(newest, st.st_mtime)
            if name in ('auth.json', '.credentials.json'):
                creds.append(str(p))
    return size, newest, creds


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--manifest', required=True); ap.add_argument('--delete', action='store_true')
    a = ap.parse_args()
    cmdlines = subprocess.run(['/bin/ps', '-axww', '-o', 'command='], capture_output=True, text=True).stdout
    uid, now = os.getuid(), time.time()
    rows, skipped = [], {'recent': [], 'in_use': [], 'keep': []}
    for entry in sorted(TMP.iterdir()):
        name = entry.name
        if not PREFIX.match(name):
            continue
        if name in KEEP_EXACT or name.startswith(KEEP_PREFIX):
            skipped['keep'].append(name); continue
        try:
            if entry.lstat().st_uid != uid:
                continue
        except FileNotFoundError:
            continue
        if f'/tmp/{name}' in cmdlines or f'/private/tmp/{name}' in cmdlines:
            skipped['in_use'].append(name); continue
        size, newest, creds = tree_stats(entry) if entry.is_dir() and not entry.is_symlink() else (entry.lstat().st_size, entry.lstat().st_mtime, [])
        if now - newest < RECENT_SECONDS:
            skipped['recent'].append(name); continue
        rows.append({'name': name, 'bytes': size, 'newest_mtime': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(newest)), 'credential_files': creds})
    report = {'mode': 'delete' if a.delete else 'dry-run', 'candidates': len(rows), 'bytes': sum(r['bytes'] for r in rows),
              'with_credentials': [r['name'] for r in rows if r['credential_files']], 'skipped': skipped, 'entries': rows}
    if a.delete:
        failed = []
        for r in rows:
            p = TMP / r['name']
            try:
                shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
            except Exception as error:
                failed.append({'name': r['name'], 'error': repr(error)})
        report['failed'] = failed
        report['remaining'] = [r['name'] for r in rows if (TMP / r['name']).exists() or (TMP / r['name']).is_symlink()]
    Path(a.manifest).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('mode', 'candidates', 'bytes', 'with_credentials')}, ensure_ascii=False),
          {k: len(v) for k, v in skipped.items()}, report.get('failed'), report.get('remaining'))


if __name__ == '__main__':
    main()
