"""在当前 worker 证据目录中运行隔离模块检查；只读已有依赖，保存状态后清理副本。

不启动 hc、后台或原生 CLI，不触碰 /private/tmp 或共享构建输出。不是业务验收。
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependencies', type=Path, required=True, help='已有 workbench/node_modules，仅作为读取来源')
parser.add_argument('--summary', type=Path, required=True, help='新的 JSON 文件')
args = parser.parse_args()
summary = args.summary.resolve()
with summary.open('x', encoding='utf-8') as out:
    out.write('{"status":"INCOMPLETE"}\n')
fixture = Path(tempfile.mkdtemp(prefix='t257-source-', dir=summary.parent))
report = dict(status='INCOMPLETE', head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              diff=subprocess.check_output(['git', 'diff', '--', 'workbench/src/panes.ts'], cwd=ROOT, text=True),
              node=subprocess.check_output(['node', '--version'], text=True).strip(), source_fixture=str(fixture),
              scope='Panes 真实模块与 SQLite；不是后台/门禁/CLI 验收')
try:
    shutil.copytree(ROOT / 'workbench/src', fixture / 'workbench/src')
    (fixture / 'workbench/node_modules').symlink_to(args.dependencies.resolve(), target_is_directory=True)
    checks = summary.with_name(summary.stem + '-schedules.json')
    command = ['node', str(ROOT / 'workbench/tests/test_t257_codex_stop_continuation.ts'), str(fixture), str(checks)]
    result = subprocess.run(command, capture_output=True, text=True)
    schedule_report = json.loads(checks.read_text(encoding='utf-8')) if checks.exists() else {}
    report.update(command=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr, schedules=str(checks),
                  status=schedule_report.get('status', 'INCOMPLETE'))
finally:
    files = [p for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()]
    report['cleanup'] = dict(path=str(fixture), files=len(files), bytes=sum(p.stat().st_size for p in files),
                             at=datetime.now(timezone.utc).isoformat(), removed=False)
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # shutil.rmtree unlinks node_modules itself and does not traverse the dependency target.
    shutil.rmtree(fixture)
    report['cleanup']['removed'] = True
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(report['status'], report.get('exit'), report.get('stdout', ''), 'SUMMARY=' + str(summary))
raise SystemExit(report.get('exit', 2))
