"""Reproduce M5 survival, then verify refreshed-receipt completion conditions."""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
LEGACY = '06fc9feca6b91febd9879222d82bcb800e2e18ba'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['domain', 'entry'], required=True)
    parser.add_argument('--legacy-survival', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    assert not args.legacy_survival or args.suite == 'domain'
    product = SOURCE / 'workbench/src/panes.ts'; product_text = product.read_text(encoding='utf-8')
    mutation = json.loads((BASE / 'startup-receipt-oracle-312/M5.json').read_bytes())
    assert product_text.count(mutation['old']) == 1 and mutation['new'] not in product_text
    assert not subprocess.check_output(['git', 'diff', '--', 'workbench/src'], cwd=SOURCE), 'product source must remain unchanged'
    spec = importlib.util.spec_from_file_location('startup_snapshot', BASE / 'run-startup-pending-entry.py')
    snapshot = importlib.util.module_from_spec(spec); spec.loader.exec_module(snapshot)
    fixture = BASE / '09b-startup-pending-fixture-01'
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'CLAUDE_', 'CODEX_', 'ANTHROPIC_', 'NODE_COMPILE_CACHE'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = {'status': 'INCOMPLETE', 'suite': args.suite, 'legacy_survival': args.legacy_survival,
              'real_model_turns': 0, 'runs': [], 'scope': 'M5 counterfactual and candidate; no product edits or A14 scene access'}
    root = Path(tempfile.mkdtemp(prefix='t078-startup-receipt-', dir='/private/tmp')).resolve()
    try:
        modes = ['legacy-m5'] if args.legacy_survival else ['m5', 'candidate']
        for mode in modes:
            snap = root / mode; case = out / mode; case.mkdir()
            snapshot.prepare_snapshot(snap, product_text, 'green')
            domain = snap / 'workbench/tests/test_t078_startup_pending.ts'
            shutil.copy2(SOURCE / 'workbench/tests/test_t078_startup_pending.ts', domain)
            if mode == 'legacy-m5':
                domain.write_bytes(subprocess.check_output(['git', 'show', LEGACY + ':workbench/tests/test_t078_startup_pending.ts'], cwd=SOURCE))
            if mode in ['m5', 'legacy-m5']:
                (snap / mutation['target']).write_text(product_text.replace(mutation['old'], mutation['new']), encoding='utf-8')
            snapshot.probe_snapshot(snap, env, case)
            save(case / 'snapshot.json', {'base_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
                 'product_mutation': mutation if mode != 'candidate' else None, 'legacy_test_revision': LEGACY if mode == 'legacy-m5' else None})
            shutil.copy2(snap / mutation['target'], case / 'panes.ts')
            test = domain if args.suite == 'domain' else snap / 'workbench/tests/test_t078_a13_rehearsal.ts'
            shutil.copy2(test, case / test.name)
            if args.check_only:
                continue
            command = ['node', str(test), str(case / 'test')]
            command += [str(fixture)] if args.suite == 'domain' else ['--recipient-offline', str(fixture)]
            cwd = SOURCE if args.suite == 'domain' else snap
            deadline = 45 if args.suite == 'domain' else 190
            row = {'mode': mode, 'command': command, 'cwd': str(cwd), 'timeout_seconds': deadline}; result['runs'].append(row)
            with (case / 'stdout.bin').open('xb') as stdout, (case / 'stderr.bin').open('xb') as stderr:
                completed = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                           timeout=deadline, start_new_session=True)
            observed = json.loads((case / 'test' / ('results.json' if args.suite == 'domain' else 'result.json')).read_bytes())
            row.update(exit_code=completed.returncode, test_status=observed['status'])
            if mode in ['candidate', 'legacy-m5']:
                assert completed.returncode == 0 and observed['status'] == 'PASS', (mode, observed)
                assert all(check['status'] == 'PASS' for check in observed['checks']), observed
                row['checks'] = len(observed['checks'])
                row['meaning'] = 'known-bad survived frozen completion conditions' if mode == 'legacy-m5' else 'candidate accepted'
                if mode == 'candidate' and args.suite == 'domain':
                    reads = [item for check in observed['checks'] for item in check['receipt_refreshes']]
                    assert len(reads) == 7, ('missing_per_key_refresh', reads)
                    assert all(item['refreshed']['state'] == 'queued' and not item['i2']
                               and not any(receipt['state'] == 'delivered' for receipt in item['history']) for item in reads)
                    row['pre_release_refreshes'] = len(reads)
                if mode == 'candidate' and args.suite == 'entry':
                    assert len(list((case / 'test').glob('startup-receipt-*.json'))) == 6
                    for index in range(6):
                        readback = json.loads((case / 'test' / f'startup-receipt-{index}.json').read_bytes())
                        assert readback['entry_id'] == observed['stop_entry']['id'] == readback['refreshed']['entry']['id']
                        assert readback['refreshed']['delivery']['state'] == 'queued' and not readback['I2']
                        assert not any(receipt['state'] == 'delivered' for receipt in readback['history'])
                    row['pre_release_refreshes'] = 6
            else:
                assert completed.returncode != 0 and observed['status'] == 'INCOMPLETE', ('M5 survived', observed)
                if args.suite == 'domain':
                    rejected = [check for check in observed['checks'] if check['status'] != 'PASS']
                    assert rejected and all('startup refreshed receipt remains queued' in check['error'] for check in rejected), rejected
                    assert all(check['receipt_refreshes'][0]['refreshed']['state'] == 'delivered' for check in rejected)
                    row['failures'] = rejected
                else:
                    assert observed['step'] == 'approved startup keys keep the pending inbox queued', observed
                    assert observed['observed'] == 'delivered' and observed['expected'] == 'queued', observed
                    assert 'startup refreshed delivery 0' in observed['error'], observed
                    readback = json.loads((case / 'test/startup-receipt-0.json').read_bytes())
                    assert readback['refreshed']['delivery']['state'] == 'delivered'
                    assert readback['state'] == 'unknown' and readback['active'] is None and len(readback['queue']) == 1
                    assert readback['writes'] == ['\x1b[A']
                    row['failure'] = observed
                row['meaning'] = 'M5 rejected at the new refreshed-delivery assertion'
            save(case / 'verdict.json', row)
        assert product.read_text(encoding='utf-8') == product_text
        assert not subprocess.check_output(['git', 'diff', '--', 'workbench/src'], cwd=SOURCE)
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        shutil.rmtree(root); result['source_scratch_removed'] = True
        result['check_only'] = args.check_only
        save(out / 'result.json', result)
    print(json.dumps({'status': result['status'], 'suite': args.suite, 'legacy_survival': args.legacy_survival,
                      'check_only': args.check_only, 'error': result.get('error')}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
