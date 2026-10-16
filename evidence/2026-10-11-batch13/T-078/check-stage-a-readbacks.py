"""Exercise Stage A receipt preflight on preserved reports; never launch a scene."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import types

BASE = Path(__file__).resolve().parent
RUNNER = BASE / 'run-09b.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--omit-legacy-guard', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(exist_ok=False)
    source = RUNNER.read_text(encoding='utf-8')
    if args.omit_legacy_guard:
        guard = "    assert full['status'] == 'INCOMPLETE' and full.get('error') == 'AssertionError()', 'legacy_failure_must_be_CAS_classifier_only'\n"
        assert source.count(guard) == 1
        source = source.replace(guard, '', 1)
    module = types.ModuleType('stage_a_check'); module.__file__ = str(RUNNER)
    exec(compile(source, str(RUNNER), 'exec'), module.__dict__)
    relative = [name + '/result.json' for name in module.REGRESSION_REPORTS]
    relative += ['review-followup-regressions-02/' + suite + '/run.json' for suite in ['coop', 'recovery', 'run', 'cas', 'cards', 'mutant-cas']]
    relative += [name + '/mutant-' + mutant + '/run.json' for name, mutant in
                 [('review-followup-mutant-cas-03', 'cas'), ('review-followup-mutant-lock-04', 'lock')]]
    originals = {name: json.loads((BASE / name).read_bytes()) for name in relative}
    cases = [('four-real-receipts', None, None, True),
             ('unrelated-legacy-error', 'review-followup-regressions-02/result.json', lambda r: r.update(error="RuntimeError('other failure')"), False),
             ('legacy-status-not-explicit', 'review-followup-regressions-02/result.json', lambda r: r.update(status='PASS'), False),
             ('legacy-failed-prior-stage', 'review-followup-regressions-02/result.json', lambda r: r['stages'][0].update(status='INCOMPLETE'), False),
             ('legacy-wrong-frame', 'review-followup-regressions-02/result.json', lambda r: r.update(traceback='AssertionError\n'), False),
             ('CAS-supplement-failed', 'review-followup-mutant-cas-03/result.json', lambda r: r.update(status='INCOMPLETE'), False),
             ('lock-supplement-failed', 'review-followup-mutant-lock-04/result.json', lambda r: r.update(status='INCOMPLETE'), False),
             ('lock-wrong-case', 'review-followup-mutant-lock-04/mutant-lock/run.json', lambda r: r.update(selected_cases=['unrelated_method']), False),
             ('lock-harness-error', 'review-followup-mutant-lock-04/mutant-lock/run.json', lambda r: r.update(errors=1), False),
             ('own-regression-incomplete', 'merge-main-4-t078-regressions-01/result.json', lambda r: r['stages'][0].update(status='INCOMPLETE'), False),
             ('original-suite-unexecuted', 'review-followup-regressions-02/coop/run.json', lambda r: r.update(unexecuted_methods=['some_method']), False),
             ('missing-lock-receipt', 'review-followup-mutant-lock-04/result.json', 'delete', False),
             ('approval-list-mismatch', None, 'approval', False)]
    rows = []
    with tempfile.TemporaryDirectory(prefix='t078-stage-a-readbacks-', dir='/private/tmp') as scratch:
        for name, target, change, expected in cases:
            root = Path(scratch) / name; root.mkdir()
            for path, original in originals.items():
                value = copy.deepcopy(original)
                if path == target:
                    if change == 'delete': continue
                    change(value)
                dest = root / path; dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(value), encoding='utf-8')
            module.BASE = root
            static = json.loads((BASE / '09b-executable-materials-16/static-check.json').read_bytes())
            static['regression_readbacks'] = [str(root / n / 'result.json') for n in module.REGRESSION_REPORTS]
            approval = {'regression_readbacks': list(static['regression_readbacks'])}
            if change == 'approval': approval['regression_readbacks'].pop()
            try:
                audit = module.validate_regression_readbacks(static, approval)
                accepted, error = audit['status'] == 'PASS', None
            except (AssertionError, FileNotFoundError) as exc:
                accepted, error = False, repr(exc)
            rows.append({'name': name, 'expected_acceptance': expected, 'accepted': accepted,
                         'pass': accepted == expected, 'error': error})
    result = {'status': 'PASS' if all(x['pass'] for x in rows) else 'INCOMPLETE', 'checks': rows,
              'scope': 'Real saved receipts, isolated file counterexamples, read-only Git; no runtime scene',
              'known_bad_preflight': args.omit_legacy_guard, 'runtime_process_starts': 0, 'live_signatures_written': False}
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
