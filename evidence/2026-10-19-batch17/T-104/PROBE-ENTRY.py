"""只检查真实 CLI 是否接纳普通终端命令；不启动后台或模型。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
with tempfile.TemporaryDirectory(prefix='t104-entry-') as state:
    argv = ['node', str(root / 'workbench/src/gates/cli.ts'), '--state', state,
            'shell_start', '--project', 't104', '--cwd', str(root)]
    run = subprocess.run(argv, env=env, capture_output=True, text=True)
    # An absent daemon must be reached through transport. Usage rejection means
    # the requested shell entry has not been implemented. This is not PTY proof.
    admitted = run.returncode == 1 and '"error":"daemon_call_failed"' in run.stdout
    report = dict(status='PASS' if admitted else 'INCOMPLETE', scope='CLI admission only',
                  argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr,
                  admitted=admitted)
    with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if admitted else 1)
