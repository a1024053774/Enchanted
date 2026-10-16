"""Check the coordinator against preserved business failures and non-business failures."""
import argparse
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('verdict_under_test', BASE / 'run-review-followup-regressions.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    observed = []
    with tempfile.TemporaryDirectory(prefix='t078-f4-verdict-', dir='/private/tmp') as scratch:
        for name in ['fence', 'cas', 'lock']:
            old = json.loads((BASE / 'outside-final-01' / ('mutant-' + name) / 'run.json').read_bytes())
            folder = Path(scratch) / name; folder.mkdir()
            def write(record):
                (folder / 'run.json').write_text(json.dumps(record), encoding='utf-8')
                for field in ['commands', 'artifacts', 'assertions']:
                    (folder / (field + '.json.gz')).write_bytes(gzip.compress(json.dumps(record[field]).encode('utf-8')))
            write(old); verdict = module.verify_mutant(folder, name, Path(old['mutant_core']), 1)
            assert verdict['status'] == 'PASS'
            negatives = []
            bad = copy.deepcopy(old); bad['errors'] = 1; negatives.append(('setup-error', bad))
            bad = copy.deepcopy(old)
            for artifact in bad['artifacts']:
                for generation in artifact['daemons']: generation['host_ready']['gate'] = '/foreign/core.ts'
            negatives.append(('wrong-loaded-core', bad))
            if name in ['cas', 'lock']:
                bad = copy.deepcopy(old)
                for item in bad['original_results']: item['classification'] = 'fixture-error'
                negatives.append(('fixture-classification', bad))
                bad = copy.deepcopy(old)
                for item in bad['assertions']: item['pass'] = True
                negatives.append(('no-business-violation', bad))
            for label, record in negatives:
                write(record)
                try: module.verify_mutant(folder, name, Path(old['mutant_core']), 1)
                except AssertionError: continue
                raise AssertionError('non-business failure was accepted: ' + name + '/' + label)
            observed.append({'name': name, 'historical_business_red_accepted': True,
                             'rejected_non_business_cases': [label for label, _ in negatives]})
    result = {'status': 'PASS', 'scope': 'Historical stored verdict schema only; not a new product regression',
              'cases': observed, 'scene_actions': 0, 'daemon_starts': 0, 'API_starts': 0, 'CLI_starts': 0}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result)); return 0


if __name__ == '__main__': raise SystemExit(main())
