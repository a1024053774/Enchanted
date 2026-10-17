"""Replay preserved CAS results through the classifier; never start the gate."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import types

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parents[2]
RUNNER = BASE / 'run-review-followup-regressions.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runner-revision')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    source = (subprocess.check_output(['git', 'show', args.runner_revision + ':' + str(RUNNER.relative_to(SOURCE))],
                                     cwd=SOURCE) if args.runner_revision else RUNNER.read_bytes())
    module = types.ModuleType('cas_classifier_under_test')
    module.__file__ = str(RUNNER)
    exec(compile(source, str(RUNNER), 'exec'), module.__dict__)
    fixture = BASE / 'review-followup-regressions-02/mutant-cas'
    raw = {'run': json.loads((fixture / 'run.json').read_bytes())}
    for name in ('assertions', 'artifacts', 'commands'):
        raw[name] = json.loads(gzip.decompress((fixture / (name + '.json.gz')).read_bytes()))
    core = Path(raw['run']['mutant_core'])
    binding = 'CAS revalidation binds the new G and unchanged C'
    oracle = 'CAS revalidation executes the oracle again'
    cases = [('preserved-real-business-red', raw, 1, True)]

    def negative(name, change):
        data = copy.deepcopy(raw)
        change(data)
        cases.append((name, data, 1, False))

    negative('unrelated-failure', lambda d: d.update(assertions=[{
        'claim': 'Unrelated operation failed', 'pass': False}]))
    negative('binding-actually-correct', lambda d: next(x for x in d['assertions'] if x['claim'] == binding)
             ['observed'].update(G=next(x for x in d['assertions'] if x['claim'] == binding)['expected'][0]))
    negative('oracle-actually-reran', lambda d: next(x for x in d['assertions'] if x['claim'] == oracle).update(observed=2))
    negative('candidate-changed', lambda d: next(x for x in d['assertions'] if x['claim'] == binding)
             ['observed'].update(C='unexpected-candidate'))
    negative('external-ancestor-preserved', lambda d: next(x for x in d['assertions'] if
             x['claim'] == 'CAS integration preserves ancestor ' + next(a for a in d['assertions'] if a['claim'] == binding)['expected'][0])
             .update(observed=0, **{'pass': True}))
    negative('wrong-loaded-core', lambda d: d['artifacts'][0]['daemons'][0]['host_ready'].update(gate='/wrong/core.ts'))
    negative('harness-error', lambda d: d['run'].update(errors=1))
    negative('not-business-red', lambda d: d['run']['original_results'][0].update(classification='harness-error'))
    negative('wrong-original-method', lambda d: d['run'].update(selected_cases=['another_method']))
    good = BASE / 'review-followup-regressions-02/cas'
    green = {'run': json.loads((good / 'run.json').read_bytes())}
    for name in ('assertions', 'artifacts', 'commands'):
        green[name] = json.loads(gzip.decompress((good / (name + '.json.gz')).read_bytes()))
    cases.append(('unmutated-success-is-not-red', green, 0, False))
    rows = []
    with tempfile.TemporaryDirectory(prefix='t078-cas-classifier-', dir='/private/tmp') as scratch:
        for name, data, code, expected in cases:
            folder = Path(scratch) / name
            folder.mkdir()
            (folder / 'run.json').write_text(json.dumps(data['run']), encoding='utf-8')
            for field in ('assertions', 'artifacts', 'commands'):
                (folder / (field + '.json.gz')).write_bytes(gzip.compress(json.dumps(data[field]).encode('utf-8')))
            try:
                verdict = module.verify_mutant(folder, 'cas', core, code)
                accepted, error = verdict['status'] == 'PASS', None
            except AssertionError as exc:
                accepted, error = False, repr(exc)
            rows.append({'name': name, 'expected_acceptance': expected, 'accepted': accepted,
                         'pass': accepted == expected, 'error': error})
    record = {'status': 'PASS' if all(x['pass'] for x in rows) else 'INCOMPLETE',
              'scope': 'Saved evidence replay and classifier counterexamples; no gate/API/CLI execution',
              'fixture': str(fixture), 'runner_revision': args.runner_revision,
              'tests': rows, 'gate_processes': 0, 'real_model_turns': 0}
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
