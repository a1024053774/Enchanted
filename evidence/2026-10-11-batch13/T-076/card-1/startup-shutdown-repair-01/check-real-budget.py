"""Verify only the two explicitly approved zero-turn reconciliations."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

probe_path, ledger, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(probe_path.resolve().parent))
spec = importlib.util.spec_from_file_location('t076_budget_probe', probe_path)
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
entries = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
assert probe.accounted_real_turns(entries) == 0
cases = [{'case': 'two approved zero reconciliations', 'expected': 0, 'observed': 0}]
for name, mutate in [
    ('wrong approval for second attempt', lambda rows: rows[-1].update(decision_ref='evidence/2026-10-11-batch13/T-076/card-1/controller-decision-02.md')),
    ('nonzero actual consumption', lambda rows: rows[-1].update(actual=1)),
    ('duplicate reconciliation', lambda rows: rows.append(copy.deepcopy(rows[-1]))),
    ('mismatched reserved count', lambda rows: rows[-1].update(reserved=3)),
]:
    bad = copy.deepcopy(entries); mutate(bad)
    try: probe.accounted_real_turns(bad)
    except RuntimeError: cases.append({'case': name, 'expected': 'refused', 'observed': 'refused'})
    else: raise AssertionError(name)
next_entries = copy.deepcopy(entries) + [{'kind': 'reservation', 'reserved': 2,
    'output': str(Path(entries[-1]['output']).with_name('outside-real-03'))}]
assert probe.accounted_real_turns(next_entries) == 2
cases.append({'case': 'new planned two-turn reservation blocks another invocation', 'expected': 2, 'observed': 2})
record = {'status': 'PASS', 'argv': sys.argv, 'real_codex_turns': 0, 'cases': cases}
with output.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(record, ensure_ascii=False))
