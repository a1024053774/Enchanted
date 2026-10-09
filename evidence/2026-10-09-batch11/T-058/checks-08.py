from pathlib import Path
import datetime as dt
import json
import os
import subprocess
import sys

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
checks = [
    ('fmt', ['./a2a/scripts/bun', 'run', 'fmt:check']),
    ('lint', ['./a2a/scripts/bun', 'run', 'lint']),
    ('typecheck', ['./a2a/scripts/bun', 'run', 'typecheck']),
    ('migrations', ['./a2a/scripts/bun', 'run', 'migrations:check']),
    ('gates', ['./a2a/scripts/bun', 'run', '--cwd', 'packages/a2a-gates', 'test']),
    ('server', ['./a2a/scripts/bun', 'run', '--cwd', 'apps/server', 'test', 'src/a2a/service.test.ts', 'src/a2a/layer-sharing.test.ts', 'src/a2a/project-title.test.ts', 'src/a2a/raise-permission.test.ts', 'src/a2a/capabilities.test.ts', 'src/agentGateway/Layers/AgentGatewaySessionRegistry.test.ts']),
]
failed = False
for name, argv in checks:
    version = subprocess.check_output(['git','rev-parse','HEAD'], cwd=fork, text=True).strip()
    log = out/(label+'-'+name+'.log')
    with log.open('x', encoding='utf-8') as stream:
        run = subprocess.run(argv, cwd=fork, env={**os.environ, 'A2A_SYNARA_SLOT':'s11-t058-checks'}, stdout=stream, stderr=subprocess.STDOUT)
    with (out/(label+'-'+name+'.json')).open('x', encoding='utf-8') as stream:
        json.dump(dict(argv=argv,cwd=str(fork),fork=version,exit_code=run.returncode,log=log.name,
            tracked_status=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=fork,text=True),
            finished=dt.datetime.now(dt.timezone.utc).isoformat()), stream, ensure_ascii=False, indent=2)
    print(name, run.returncode, flush=True)
    failed |= run.returncode != 0
raise SystemExit(int(failed))
