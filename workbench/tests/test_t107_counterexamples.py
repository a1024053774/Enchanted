"""Run the same independent projection oracle against three single faults."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

output = Path(sys.argv[1])
assert not output.exists()
source = Path(__file__).resolve().parents[1]
root = Path(tempfile.mkdtemp(prefix='t107-counterexamples-', dir='/private/tmp'))
original = (source / 'src/sidebar.ts').read_text(encoding='utf-8')
mutations = [
    ('unknown_promoted', "  return 'unknown';\n}\n\nexport function aggregate", "  return 'running';\n}\n\nexport function aggregate", 'Missing signal must remain unknown'),
    ('role_parent', "parent: senders.size === 1 ? [...senders][0] : null", "parent: senders.size === 1 ? [...senders][0] : launches.find(p => p.project === record.project && p.preset === 'executor')?.id ?? null", 'Role-only parent must be rejected'),
    ('git_zero', 'ahead: ab ? Number(ab[1]) : null', 'ahead: ab ? 0 : null', 'Git ahead must match the independent divergent fixture'),
]
report = dict(status='INCOMPLETE', model_calls=0, cases=[], retained_root=str(root))
for name, old, new, expected in mutations:
    assert original.count(old) == 1
    module = root / (name + '.ts')
    module.write_text(original.replace(old, new), encoding='utf-8')
    result_path = root / (name + '.json')
    command = ['node', str(source / 'tests/test_t107_sidebar.mjs'), str(result_path), str(module)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    observed = json.loads(result_path.read_text(encoding='utf-8'))
    report['cases'].append(dict(name=name, command=command, exit=result.returncode, rejected=result.returncode != 0 and expected in observed.get('error', ''),
                                error=observed.get('error'), retained_fixture=observed.get('retained_fixture')))
report['status'] = 'PASS' if all(case['rejected'] for case in report['cases']) else 'INCOMPLETE'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
