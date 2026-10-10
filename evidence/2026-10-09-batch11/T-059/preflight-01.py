"""Capture a read-only baseline and a no-model environment probe in a fresh label."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
assert label.replace('-', '').replace('_', '').isalnum()
result = out / label
result.mkdir()
probe_root = Path(tempfile.mkdtemp(prefix='a2a-t059-auth-probe-', dir='/tmp')).resolve()
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
env.update(HOME=str(probe_root / 'os-home'), CODEX_HOME=str(probe_root / 'codex-empty'),
           CLAUDE_CONFIG_DIR=str(probe_root / 'config'), A2A_SYNARA_SLOT='s11-t059-' + label,
           T059_FORK=str(fork), T059_PROBE_ROOT=str(probe_root),
           T059_PROBE_OUTPUT=str(result / 'environment.json'))

def save(name, value):
    with (result / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def run(name, argv):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=fork, env=env, text=True, capture_output=True)
    save(name, dict(argv=argv, cwd=str(fork), started=started, exit_code=proc.returncode,
                    stdout=proc.stdout, stderr=proc.stderr))
    return proc

run('fork-baseline.json', ['git', 'rev-parse', 'HEAD'])
run('fork-status.json', ['git', 'status', '--short'])
sources = {
    'apps/server/src/provider/claudeEnvironment.ts': [(93, 195)],
    'apps/server/src/provider/claudeProcessEnv.ts': [(170, 202), (236, 280)],
    'apps/server/src/provider/Layers/ClaudeAdapter.ts': [(1366, 1371), (2187, 2203), (6186, 6230)],
    'apps/server/src/a2a/service.ts': [(145, 182)],
    'packages/a2a-gates/src/core.ts': [(736, 751), (1863, 1894)],
    'apps/web/src/a2a/TaskWindow.tsx': [(315, 323)],
    'apps/web/src/a2a/IssuePanel.tsx': [(19, 24)],
}
records = []
for relative, ranges in sources.items():
    lines = (fork / relative).read_text(encoding='utf-8').splitlines()
    records.append(dict(file=relative, excerpts=[dict(first=a, last=b,
        text='\n'.join(f'{n}: {lines[n-1]}' for n in range(a, min(b, len(lines))+1))) for a, b in ranges]))
save('source-excerpts.json', records)
sdk = json.loads((fork / 'apps/server/node_modules/@anthropic-ai/claude-agent-sdk/package.json').read_text(encoding='utf-8'))
save('versions.json', dict(sdk_version=sdk['version'], probe_root=str(probe_root),
                         real_model_turns=0, auth_files_copied=0))
proc = run('environment-command.json', ['./a2a/scripts/bun', 'run', str(out / 'auth-env-probe-01.ts')])
if proc.returncode:
    raise SystemExit(proc.returncode)
print(json.dumps(dict(status='PASS', evidence=str(result), real_model_turns=0), ensure_ascii=False))
