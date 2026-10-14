#!/usr/bin/env python3
"""Reproduce F1 from preserved final-05 receipts, without running a product."""
import argparse
import io
import json
from pathlib import Path
import unittest

E = Path(__file__).resolve().parent


class RecordedClassifier(unittest.TestCase):
    def check_target(self, index, case):
        path = E / 'outside-rebase-final-05' / ('conflict-red-%02d' % index) / ('01-' + case) / 'result.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        self.assertFalse(record['business_red'], 'A pre-target failure cannot prove this target: ' + str(path))

    def test_forbidden_path(self):
        self.check_target(6, 'test_conflict_rework_still_rejects_forbidden_path')

    def test_foreign_trailer(self):
        self.check_target(7, 'test_conflict_rework_still_rejects_foreign_trailer')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RecordedClassifier))
    (args.output / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    report = {'status': 'INCOMPLETE', 'scope': 'recorded classifier defect reproduction', 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'counterfactual_confirmed': len(result.failures) == 2 and not result.errors, 'real_codex_turns': 0}
    with (args.output / 'run.json').open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2); output.write('\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['counterfactual_confirmed'] else 1)
