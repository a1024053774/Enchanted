"""T-253 门禁一侧的单元测试入口：t253_native_bind.ts 用测试运行时直接调用真实 A2AGates。

--revision 从 Git 取该版产品源码（修前没有这个绑定，应判失败）；--mutant 在当前源码副本上打 MUTANTS 里的变异；
都不给时用当前工作区源码。摘要写到 --summary，夹具目录（源码副本）通过时删除。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from scripted_claude import ROOT, source_tree

CORE = 'src/gates/core.ts'
MUTANTS = {
    # The binding writes the pane's session without the gate's identity check.
    'bind-skips-identity-check': ((CORE,
        '        if (this.bindObservedIdentity(attempt, live)) this.save(task, "runtime_bound", { attempt, by: "native_session_learned" });\n        return;',
        '        attempt.runtime_identity!.native_session = live.runtime_identity.native_session;\n'
        '        this.save(task, "runtime_bound", { attempt, by: "native_session_learned" });\n        return;'),),
    # A busy task lock ends the binding instead of waiting for it.
    'busy-not-waited': ((CORE,
        '        await new Promise((resolve) => setTimeout(resolve, 100));\n        continue;\n      }\n      try {\n'
        '        const task = this.load(taskId), attempt = this.current(task, attemptId);',
        '        return;\n      }\n      try {\n        const task = this.load(taskId), attempt = this.current(task, attemptId);'),),
    # The stop is not checked after the pane read (review 01 P2): a stop during the read or the lock wait still binds.
    'stop-not-rechecked': ((CORE,
        '      // After the read: a stop that began during it, or while this waited for the lock, ends the binding unwritten.\n'
        '      requireGate(!this.shuttingDown, "daemon_stopping");\n', ''),),
    # The pane is read while the task lock is held.
    'lock-across-read': (
        (CORE, '      const live = await this.runtime!.readThread(thread);\n'
         '      // After the read: a stop that began during it, or while this waited for the lock, ends the binding unwritten.\n'
         '      requireGate(!this.shuttingDown, "daemon_stopping");\n      let lock: DatabaseSync;\n',
         '      requireGate(!this.shuttingDown, "daemon_stopping");\n      let lock: DatabaseSync;\n'),
        (CORE, '        const task = this.load(taskId), attempt = this.current(task, attemptId);',
         '        const live = await this.runtime!.readThread(thread);\n'
         '        const task = this.load(taskId), attempt = this.current(task, attemptId);'),
    ),
}


def main():
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    summary = args.summary.resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix='t253-src-', dir='/tmp')) if args.revision or args.mutant else None
    source = source_tree(fixture, args.revision, MUTANTS.get(args.mutant, ())) if fixture else ROOT
    host = Path(__file__).resolve().parent / 't253_native_bind.ts'
    done = subprocess.run(['node', str(host), str(source), str(summary)], capture_output=True, text=True, timeout=120)
    if summary.exists():
        report = json.loads(summary.read_text(encoding='utf-8'))
    else:
        report = dict(status='FAIL', error='host wrote no summary')
    report.update(argv=sys.argv, revision=args.revision, mutant=args.mutant, source_fixture=str(fixture) if fixture else None,
                  host_exit=done.returncode, host_stdout=done.stdout[-2000:], host_stderr=done.stderr[-4000:])
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if fixture and report['status'] == 'PASS':
        shutil.rmtree(fixture, ignore_errors=True)
    print(report['status'], ','.join(report.get('failed', [])), report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
