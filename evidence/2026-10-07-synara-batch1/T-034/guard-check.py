#!/usr/bin/env python3
"""Check the external-volume contract through the executable entry."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path('/Users/luckye/Documents/Code/synara')
entry = repo / 'a2a/scripts/bun'
evidence = Path(__file__).resolve().parent
scratch = Path(tempfile.mkdtemp(prefix='t034-guards-'))
marker = scratch / 'bun-started'
fake_bun = scratch / 'bun'
fake_bun.write_text('#!/bin/sh\nprintf started > "$T034_MARKER"\n', encoding='utf-8')
fake_bun.chmod(0o755)
ordinary = scratch / 'ordinary-directory'
ordinary.mkdir()
env = dict(os.environ, PATH=str(scratch) + os.pathsep + os.environ['PATH'],
           T034_MARKER=str(marker), A2A_SYNARA_SLOT='t034')
cases = []
for volume in [scratch / 'missing', ordinary, Path('/')]:
    for args in [['install', '--frozen-lockfile'], ['run', 'build'], ['run', 'dev'],
                 ['run', 'start:desktop'], ['setup-node']]:
        before = sorted(str(p.relative_to(scratch)) for p in scratch.rglob('*'))
        command = [str(entry), *args]
        result = subprocess.run(command, cwd=repo, env=dict(env, SYNARA_BUILD_VOLUME=str(volume)),
                                capture_output=True, text=True)
        after = sorted(str(p.relative_to(scratch)) for p in scratch.rglob('*'))
        passed = result.returncode == 2 and 'a2a synara: external volume' in result.stderr
        passed = passed and before == after and not marker.exists()
        cases.append({'argv': command, 'volume': str(volume), 'exit_code': result.returncode,
                      'stdout': result.stdout, 'stderr': result.stderr,
                      'directory_unchanged': before == after, 'bun_started': marker.exists(),
                      'pass': passed})

# Known-bad counterfactual: ignore the requested volume and silently use the mounted disk.
# The temporary sibling keeps the same repo resolution; the production entry is untouched.
mutant = entry.with_name('bun-t034-mutant')
assert not mutant.exists()
source = entry.read_text(encoding='utf-8')
bad = source.replace('Path(os.environ.get("SYNARA_BUILD_VOLUME", "/Volumes/WD-Elements")).resolve()',
                     'Path("/Volumes/WD-Elements").resolve()', 1)
assert source != bad
mutant.write_text(bad, encoding='utf-8')
mutant.chmod(0o755)
try:
    bad_result = subprocess.run([str(mutant), '--version'], cwd=repo,
                                env=dict(env, SYNARA_BUILD_VOLUME=str(scratch / 'missing')),
                                capture_output=True, text=True)
    rejected_mutant = bad_result.returncode != 2 and marker.exists()
finally:
    mutant.unlink()
record = {'scratch_preserved': str(scratch), 'cases': cases,
          'counterfactual': {'mutation': 'ignore SYNARA_BUILD_VOLUME',
                            'exit_code': bad_result.returncode, 'stdout': bad_result.stdout,
                            'stderr': bad_result.stderr, 'bun_started': marker.exists(),
                            'detected': rejected_mutant},
          'pass': all(case['pass'] for case in cases) and rejected_mutant}
record['candidate'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo,
                                            text=True).strip()
with (evidence / (sys.argv[1] if len(sys.argv) > 1 else 'guard-result.json')).open('x', encoding='utf-8') as output:
    json.dump(record, output, indent=2)
    output.write('\n')
print(json.dumps({'pass': record['pass'], 'cases': len(cases),
                  'counterfactual_detected': rejected_mutant, 'scratch': str(scratch)}))
raise SystemExit(0 if record['pass'] else 1)
