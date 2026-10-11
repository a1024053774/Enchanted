#!/usr/bin/env python3
"""Record rule matching only. This script does not execute the tested commands."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
home = Path(tempfile.mkdtemp(prefix='a2a-policy-', dir='/tmp')).resolve()
records = []
try:
    # Preserved from the exact source snapshot used for outside-b-05.
    rules_text = (Path(__file__).parent / 'execpolicy-06/default.rules').read_text(encoding='utf-8')
    (home / 'rules').mkdir()
    rules = home / 'rules/default.rules'
    rules.write_text(rules_text, encoding='utf-8')
    (args.output / 'default.rules').write_text(rules_text, encoding='utf-8')
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_'))}
    env['CODEX_HOME'] = str(home)
    codex = str(Path(shutil.which('codex')).resolve())
    chain = "git add -- src/normalize.py src/report.py && git commit -m 'Implement normalized time report and validation' && git rev-parse HEAD && git status --short"
    cases = [('add-tokens', ['git', 'add', 'src/x']),
             ('actual-add-tokens', ['git', 'add', '--', 'src/normalize.py', 'src/report.py']),
             ('commit-tokens', ['git', 'commit', '-m', 'fixture']),
             ('add-shell', ['/bin/zsh', '-lc', 'git add src/x']),
             ('commit-shell', ['/bin/zsh', '-lc', "git commit -m 'fixture'"]),
             ('actual-compound', ['/bin/zsh', '-lc', chain]),
             ('two-allowed', ['/bin/zsh', '-lc', "git add src/x && git commit -m 'fixture'"]),
             ('unmatched-rev-parse', ['git', 'rev-parse', 'HEAD']),
             ('unmatched-status', ['git', 'status', '--short'])]
    commands = [('version', [codex, '--version']), ('help', [codex, 'execpolicy', 'check', '--help'])]
    commands += [(label, [codex, 'execpolicy', 'check', '-c', 'approval_policy="never"', '--pretty', '--rules', str(rules), '--', *tokens]) for label, tokens in cases]
    for label, argv in commands:
        result = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=20)
        records.append(dict(label=label, argv=argv, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
        print(label, result.stdout.strip())
finally:
    shutil.rmtree(home)
    report = dict(commands=records, isolated_home_removed=True, real_model_turns=0,
                  scope='Only rule matching is observed; this does not test shell splitting or sandbox selection during tool execution.')
    (args.output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
