"""Check final approved budget and smaller oracle without a model or daemon."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

source, ledger, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(source.resolve().parent))
spec = importlib.util.spec_from_file_location('final_probe', source)
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
entries = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
assert probe.accounted_real_turns(entries) == 1
cases = [{'case': 'prior actual consumption', 'expected': 1, 'observed': 1}]
for name, mutate in [('refund spent turn', lambda rows: rows[-1].update(actual=0)),
                     ('wrong approval', lambda rows: rows[-1].update(decision_ref='conversation:主控 #12')),
                     ('duplicate accounting', lambda rows: rows.append(copy.deepcopy(rows[-1])))]:
    bad = copy.deepcopy(entries); mutate(bad)
    try: probe.accounted_real_turns(bad)
    except RuntimeError: cases.append({'case': name, 'observed': 'refused'})
    else: raise AssertionError(name)
final = copy.deepcopy(entries) + [{'kind': 'reservation', 'reserved': 2,
    'output': str(Path(entries[-1]['output']).with_name('outside-real-04'))}]
assert probe.accounted_real_turns(final) == 3
cases.append({'case': 'last two reserved reaches cap and blocks another run', 'expected': 3, 'observed': 3})
assert probe.WAIT_SECONDS >= 900
fixture = output / 'fixture'; (fixture / 'src').mkdir(parents=True)
oracle = output / 'oracle.py'; oracle.write_text(probe.ORACLE, encoding='utf-8')
module = fixture / 'src/normalize.py'
module.write_text('def normalize(rows):\n    return {}\n', encoding='utf-8')
def run(label):
    result = subprocess.run([sys.executable, '-I', '-B', str(oracle), str(fixture)], capture_output=True, text=True)
    (output / (label + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (output / (label + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    return result.returncode
assert run('baseline-stub') == 1
control = '''def normalize(rows):
    totals = {}
    for row in rows:
        name, minutes = row.get("name"), row.get("minutes")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid_name")
        if type(minutes) is not int or minutes < 0:
            raise ValueError("invalid_minutes")
        name = name.strip(); totals[name] = totals.get(name, 0) + minutes
    return {"entries": [{"name": name, "minutes": totals[name]} for name in sorted(totals)],
            "total_minutes": sum(totals.values())}
'''
module.write_text(control, encoding='utf-8'); assert run('control') == 0
module.write_text(control.replace('type(minutes) is not int', 'not isinstance(minutes, int)'), encoding='utf-8')
assert run('bool-mutant') == 1
record = {'status': 'PASS', 'argv': sys.argv, 'budget_cases': cases,
    'wait_seconds': probe.WAIT_SECONDS, 'oracle': {'baseline_exit': 1, 'control_exit': 0, 'bool_mutant_exit': 1},
    'real_codex_turns': 0, 'scope': 'fixture oracle and exact approval accounting; no transport or model'}
with (output / 'run.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(record, ensure_ascii=False))
