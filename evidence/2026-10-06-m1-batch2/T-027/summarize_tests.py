#!/usr/bin/env python3
"""Reconcile each listed test with the preserved raw harness output."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('folder', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
assert not args.output.exists(), 'use a new output file'
listed = {line.split(': test')[0] for line in (args.folder / 'test-list.txt').read_text().splitlines()
          if line.endswith(': test')}
ansi = re.compile(r'\x1b\][^\x1b\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[()][A-Za-z]')
states = {}
for log in args.folder.glob('*.log'):
    text = ansi.sub('', log.read_text())
    matches = list(re.finditer(r'^test ([A-Za-z0-9_:]+) \.\.\. ', text, re.M))
    for index, match in enumerate(matches):
        name = match.group(1)
        if name not in listed:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment = text[match.end():end]
        first = segment.splitlines()[0].strip()
        for status in ['ok', 'FAILED', 'ignored']:
            if first.startswith(status) or re.search(r'^' + status + r'$', segment, re.M):
                states[name] = status
                break
results = json.loads((args.folder / 'results.json').read_text())
summary = dict(groups=len(results), listed_tests=len(listed), observed=len(states),
               passed=sum(value == 'ok' for value in states.values()),
               failed=sum(value == 'FAILED' for value in states.values()),
               ignored=sum(value == 'ignored' for value in states.values()),
               missing=sorted(listed - states.keys()),
               ignored_tests=sorted(name for name, value in states.items() if value == 'ignored'),
               group_exit_codes=sorted({item['exit_code'] for item in results}))
args.output.write_text(json.dumps(summary, indent=2) + '\n')
assert not summary['missing'] and not summary['failed'] and summary['group_exit_codes'] == [0]
print(json.dumps({key: value for key, value in summary.items() if key != 'ignored_tests'}))
