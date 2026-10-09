"""Run unchanged 18+17 cases sequentially on the final frozen commit."""
import os, subprocess, sys
from pathlib import Path
root=Path('/Users/luckye/Documents/Code/a2a')
here=Path(__file__).resolve().parent
runner=here/'run-acceptance.py'
cases=[('last-orchestration',root/'evidence/2026-10-07-synara-batch2/T-037/test_run_native_e2e.py',
    {'COOP_SCRIPT':str(root/'evidence/2026-10-07-synara-batch2/T-037/native-entry.py')}),
  ('last-delivery-recovery',root/'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py',
    {'COOP_NATIVE_ENTRY':'/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts'})]
failed=False
for label,suite,extra in cases:
    env={**os.environ,'PYTHONPATH':str(root/'acceptance'),**extra}
    result=subprocess.run([sys.executable,'-B',str(runner),label,str(suite)],cwd=root,env=env)
    failed=failed or result.returncode!=0
raise SystemExit(1 if failed else 0)
