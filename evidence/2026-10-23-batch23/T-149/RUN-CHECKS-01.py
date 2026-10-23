"""复跑 T-149 注释变更相关的离线检查；不启动 Electron、后台或 CLI。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
commands = []


def run(name, argv):
    result = subprocess.run(list(map(str, argv)), cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=30)
    (out / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (out / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    commands.append(dict(name=name, argv=list(map(str, argv)), exit=result.returncode))
    return result.returncode


report = dict(status='INCOMPLETE', commands=commands,
              source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              source_changes=subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines(),
              scope='离线 import/解析、实际捕获请求回放、旧 host 的 VM 检查；无原生运行时证明')
try:
    # 稀疏工作树缺少两个历史捕获输入。只在私有临时副本补齐，不改历史证据目录。
    with tempfile.TemporaryDirectory(prefix='t149-replay-', dir='/private/tmp') as raw:
        tree = Path(raw)
        tests = tree / 'workbench/tests'
        tests.mkdir(parents=True)
        for name in ('test_t112_request_replay.py', 'diagnose_t112_reviewer.py',
                     't112_archive.py', 't108_cleanup.py', 't112_native_api.py'):
            shutil.copyfile(ROOT / 'workbench/tests' / name, tests / name)
        for name in ('request-capture-02.json', 'code-mode-protocol-01.json'):
            relative = 'evidence/2026-10-20-batch18/T-112/' + name
            path = tree / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + relative], cwd=ROOT))
        replay = run('request-replay', [sys.executable, '-B', tests / 'test_t112_request_replay.py',
                                       '--summary', out / 'request-replay.json'])
    controlled = run('controlled-pty-import', ['node', '--input-type=module', '-e',
        "import assert from 'node:assert/strict'; "
        "const m = await import('./workbench/tests/controlled_quality_pty.ts'); "
        "assert.equal(typeof m.installControlledPTY, 'function'); console.log('PASS: installControlledPTY imported');"])
    host = run('reviewer-host-parse', ['node', '--check', ROOT / 'workbench/tests/t112_reviewer_record.mjs'])
    # 该现有测试仍假定 host 显式调用 release()；保存结果，不能将它改绿或静默跳过。
    startup = run('reviewer-startup', ['node', '--experimental-vm-modules',
        ROOT / 'workbench/tests/test_t112_reviewer_startup.mjs', out / 'reviewer-startup.json'])
    report.update(request_replay_exit=replay, controlled_pty_import_exit=controlled,
                  reviewer_host_parse_exit=host, reviewer_startup_exit=startup)
    report['import_checks_status'] = 'PASS' if (replay, controlled, host) == (0, 0, 0) else 'INCOMPLETE'
    report['status'] = 'PASS' if report['import_checks_status'] == 'PASS' and startup == 0 else 'INCOMPLETE'
finally:
    (out / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
sys.exit(0 if report['status'] == 'PASS' else 1)
