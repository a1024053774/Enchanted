"""由执行主控运行：绑定提交复验 T-156-2，并把原始现场归档到外置盘。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
VOLUME = Path('/Volumes/WD-Elements')
PATTERN = r'^[[:space:]]*(import[[:space:]]+run_t082_boundary|from[[:space:]]+run_t082_boundary|import[[:space:]]+test_t078_quality_host_bootstrap|from[[:space:]]+test_t078_quality_host_bootstrap)'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def inventory(root):
    entries = [path for path in root.rglob('*') if path.is_symlink() or path.is_file()]
    return {'files': len(entries), 'bytes': sum(path.lstat().st_size for path in entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True, help='完整候选提交号')
    args = parser.parse_args()
    if not VOLUME.is_mount():
        raise RuntimeError('外置盘未挂载，不回退内置盘。')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != args.revision:
        raise RuntimeError('HEAD 与指定候选不符。')
    dirty = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all', '--',
        'workbench', str(BASE / 'run_credentials_suite.py'), str(Path(__file__).resolve())], cwd=ROOT, text=True)
    if dirty:
        raise RuntimeError('候选代码或运行脚本未提交：' + dirty)
    raw = Path(tempfile.mkdtemp(prefix='t156-2-outside-02-', dir='/private/tmp')).resolve()
    steps = []

    def run(name, command):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
        (raw / (name + '.stdout.txt')).write_bytes(result.stdout)
        (raw / (name + '.stderr.txt')).write_bytes(result.stderr)
        steps.append({'name': name, 'command': command, 'exit_code': result.returncode})
        return result

    suite = run('credentials-suite', [sys.executable, '-B', str(BASE / 'run_credentials_suite.py'),
                                     '--source', str(ROOT), '--output', str(raw / 'suite')])
    imported = run('affected-imports', [sys.executable, '-B', '-c', '''import importlib, json, runpy, sys
from pathlib import Path
sys.path.insert(0, str(Path('workbench/tests').resolve()))
names=['test_quality_chain_e2e','test_t082_review_boundary_e2e','test_t156_quality_host_credentials']
for name in names: importlib.import_module(name)
runpy.run_path('evidence/2026-10-23-batch23/T-152/run_suite.py',run_name='t156_import_probe')
print(json.dumps({'status':'PASS','modules':names,'runner':'T-152/run_suite.py'}))'''])
    current = run('current-import-scan', ['git', 'grep', '-n', '-E', PATTERN, '--',
                                        'workbench', 'scripts', 'acceptance'])
    historical = run('all-import-scan', ['git', 'grep', '-n', '-E', PATTERN, '--',
                                        '*.py', '*.ts', '*.mjs', '*.js'])
    status = run('project-map-status', [sys.executable,
        '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
    suite_report = json.loads((raw / 'suite/SUMMARY.json').read_text(encoding='utf-8')) if (raw / 'suite/SUMMARY.json').exists() else None
    focused_pass = (suite.returncode == imported.returncode == status.returncode == 0
                    and current.returncode == 1 and suite_report is not None and suite_report['status'] == 'PASS')
    # Controller #42: the dated T-090 evidence script is outside current-entry
    # acceptance; replay it at its own revision. Refuse any other residual import.
    allowed_historical = ['evidence/2026-10-16-batch16/T-090/run-host.py']
    historical_output = historical.stdout.decode('utf-8')
    historical_scope_pass = historical.returncode in (0, 1) and all(
        line.split(':', 1)[0] in allowed_historical for line in historical_output.splitlines())
    record = {'task': 'T-156-2', 'attempt': 'a1', 'revision': head,
              'status': 'PASS' if focused_pass and historical_scope_pass else 'INCOMPLETE',
              'focused_status': 'PASS' if focused_pass else 'INCOMPLETE', 'steps': steps,
              'suite': suite_report, 'residual_imports': historical_output,
              'allowed_historical_imports': allowed_historical, 'controller_decision': '#42',
              'real_model_turns': 0, 'daemon_starts': 0}
    save(raw / 'SUMMARY.json', record)
    archive = VOLUME / 'a2a-evidence/2026-10-23-batch24/T-156' / raw.name
    before = inventory(raw)
    archived_raw = archive / 'raw'
    shutil.copytree(raw, archived_raw, symlinks=True)
    if before != inventory(archived_raw):
        raise RuntimeError('归档文件数或字节数不符，保留原始现场。')
    replay = [sys.executable, str(Path(__file__).resolve()), '--revision', head]
    manifest = {'original': str(raw), 'archive': str(archived_raw), **before, 'replay': replay,
                'retained_local_runs': []}
    for name in ['t156-2-green-01', 't156-2-suite-01', 't156-2-post-delete-01']:
        local = Path('/private/tmp') / name
        if not local.exists():
            continue
        target = archive / 'local-runs' / name
        counts = inventory(local)
        shutil.copytree(local, target, symlinks=True)
        if counts != inventory(target):
            raise RuntimeError('本地证据归档文件数或字节数不符，保留原始现场。')
        manifest['retained_local_runs'].append({'original': str(local), 'archive': str(target),
                                                **counts, 'replay': replay})
    save(BASE / 'OUTSIDE-02.archive.json', manifest)
    save(BASE / 'OUTSIDE-02.json', record)
    # Keep originals for controller inspection; no credentials outlive the test
    # fixture, and no archive or old evidence is overwritten by this command.
    print(json.dumps({'status': record['status'], 'focused_status': record['focused_status'],
                      'archive': str(archive), 'summary': str(BASE / 'OUTSIDE-02.json')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
