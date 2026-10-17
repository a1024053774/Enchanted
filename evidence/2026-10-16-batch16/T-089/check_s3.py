#!/usr/bin/env python3
"""在一次性 checkout 运行未改断言的 S3 CAS 套件；由主控在沙箱外运行。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = 'c544b29049861998e11eeb7344b457103fab3c98'
ROOT = Path(__file__).resolve().parents[3]
PRIMARY = Path('/Users/luckye/Documents/Code/a2a')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['baseline', 'candidate'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rebased', action='store_true', help='须主控同意：用现有 merged-revision runner')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_'))}
    sandbox = Path(tempfile.mkdtemp(prefix='t089-s3-', dir='/tmp'))
    checkout = sandbox / 'repo'
    subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(ROOT), str(checkout)], env=env, check=True, capture_output=True)
    subprocess.run(['git', '-C', str(checkout), 'config', 'core.sparseCheckout', 'true'], env=env, check=True)
    (checkout / '.git/info/sparse-checkout').write_text('/workbench/\n/acceptance/\n/scripts/\n/.project-map/\n/fixtures/\n/evidence/2026-10-11-batch13/T-077/PLAN.md\n/evidence/2026-10-11-batch13/T-077/controller-decision-01.md\n/evidence/2026-10-11-batch13/T-077/controller-decision-02.md\n/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh\n', encoding='utf-8')
    subprocess.run(['git', '-C', str(checkout), 'checkout', '--detach', BASE], env=env, check=True, capture_output=True)
    if args.phase == 'candidate':
        for name in ['workbench/tests/run_s3_regression.py', 'workbench/tests/archive_evidence.py']:
            shutil.copy2(ROOT / name, checkout / name)
    dependencies = PRIMARY / 'workbench/node_modules'
    if not dependencies.is_dir():
        raise RuntimeError('主仓库现有 node_modules 不可用；不安装依赖')
    (checkout / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
    # Only output placement changes. The original main(), assertions and archival
    # call run intact. CAS produces small files; an external archive is a failure.
    driver = "import sys; from pathlib import Path; sys.path.insert(0, 'workbench/tests'); import run_s3_regression as r; r.EVIDENCE=Path(sys.argv[1]); sys.argv=['workbench/tests/run_s3_regression.py','--suite','cas','--output',str(r.EVIDENCE/'cas')]; raise SystemExit(r.main())"
    argv = ([sys.executable, '-B', 'workbench/tests/run_s3_rebased_regression.py', '--suite', 'cas',
             '--revision', BASE, '--output', str(out / 'cas')] if args.rebased
            else [sys.executable, '-B', '-c', driver, str(out)])
    p = subprocess.run(argv, cwd=checkout, env=env, capture_output=True, text=True, timeout=300)
    summary = {'phase': args.phase, 'rebased': args.rebased, 'base': BASE, 'checkout': str(checkout), 'argv': argv, 'cwd': str(checkout), 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    result = out / 'cas/run.json'
    if result.is_file():
        summary['run'] = json.loads(result.read_text(encoding='utf-8'))
        if summary['run'].get('external_archives'):
            raise RuntimeError('CAS unexpectedly archived outside the T-089 test area')
    (out / 'check.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('phase', 'exit_code', 'stdout', 'stderr')}, ensure_ascii=False))
    return p.returncode


if __name__ == '__main__':
    raise SystemExit(main())
