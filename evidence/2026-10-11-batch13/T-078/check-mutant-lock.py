"""Check the scoped lock CLI and replay historical lock evidence without running a gate."""
import argparse
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
RUNNER = BASE / 'run-review-followup-regressions.py'
CASE = 'test_live_verify_excludes_verify_and_integrate'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('scoped_runner', RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original = BASE / 'outside-final-01/mutant-lock'
    run = json.loads((original / 'run.json').read_bytes())
    raw = json.loads((original / 'test-result.json').read_bytes())
    assert run['selected_original_methods'] == [CASE]
    data = {'run': run, **{name: raw[name] for name in ('artifacts', 'assertions', 'commands')}}
    rows = []
    variants = [('historical-real-lock-business-red', data, True)]
    unrelated = copy.deepcopy(data)
    unrelated['assertions'] = [{'claim': 'Unrelated failure', 'pass': False}]
    variants.append(('unrelated-failure', unrelated, False))
    wrong_core = copy.deepcopy(data)
    wrong_core['artifacts'][0]['daemons'][0]['host_ready']['gate'] = '/wrong/core.ts'
    variants.append(('wrong-core', wrong_core, False))
    harness = copy.deepcopy(data)
    harness['run']['errors'] = 1
    variants.append(('harness-error', harness, False))
    not_business = copy.deepcopy(data)
    for item in not_business['run']['original_results']:
        item['classification'] = 'harness-error'
    variants.append(('not-business-red', not_business, False))
    with tempfile.TemporaryDirectory(prefix='t078-lock-replay-', dir='/private/tmp') as scratch:
        for name, variant, expected in variants:
            folder = Path(scratch) / name
            folder.mkdir()
            (folder / 'run.json').write_text(json.dumps(variant['run']), encoding='utf-8')
            for field in ('artifacts', 'assertions', 'commands'):
                (folder / (field + '.json.gz')).write_bytes(gzip.compress(json.dumps(variant[field]).encode('utf-8')))
            try:
                verdict = runner.verify_mutant(folder, 'lock', Path(run['mutant_core']), 1)
                accepted = verdict['status'] == 'PASS'
            except AssertionError:
                accepted = False
            rows.append({'name': name, 'expected_acceptance': expected, 'accepted': accepted, 'pass': accepted == expected})
    target = BASE / 'review-followup-mutant-lock-04'
    argv = [sys.executable, '-B', str(RUNNER), '--only-mutant', 'lock', '--output', str(target), '--check-only']
    child = subprocess.run(argv, capture_output=True)
    (out / 'check-only.stdout.txt').write_bytes(child.stdout)
    (out / 'check-only.stderr.txt').write_bytes(child.stderr)
    cli_ok = child.returncode == 0
    if cli_ok:
        reply = json.loads(child.stdout)
        cli_ok = reply['suites'] == [] and reply['mutants'] == {'lock': ['recovery', CASE]}
    rows.append({'name': 'real-runner-lock-check-only', 'exit_code': child.returncode,
                 'output_created': target.exists(), 'pass': cli_ok and not target.exists()})
    labels = {'Live operation excludes concurrent verify', 'Live operation excludes concurrent integrate',
              'Busy commands never start a second oracle'}
    claims = [{**{k: x[k] for k in ('claim', 'expected', 'pass')},
               'observed': {k: x['observed'].get(k) for k in ('ok', 'error')} if isinstance(x['observed'], dict) else x['observed']}
              for x in raw['assertions'] if x['claim'] in labels]
    record = {'status': 'PASS' if all(x['pass'] for x in rows) else 'INCOMPLETE',
              'scope': 'Historical saved-result replay and CLI check-only; no runtime gate evidence',
              'fixture': str(original), 'historical_revision': run.get('head_after'),
              'format_conversion': 'Original run JSON and original arrays only repackaged in temporary files; no field synthesis',
              'claims': claims, 'checks': rows, 'argv': argv, 'gate_processes': 0, 'real_model_turns': 0}
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
