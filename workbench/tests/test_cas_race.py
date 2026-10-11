"""CAS 契约反例：检查 G 后、实际 Git 写入前出现外部写入，必须保留外部引用。

独立预期来自 managed-delivery / recovery 契约；仅复用夹具，不导入门禁实现。
运行时需给 COOP_E2E_ARTIFACT_ROOT、COOP_E2E_TRACE；产物由本卡 runner 归档。
"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'acceptance'))
import test_coop_e2e as helper
import test_recovery_e2e as recovery


class CASRace(recovery.RecoveryCLI):
    def test_external_write_between_read_and_cas_is_preserved(self):
        self.setup_candidate(verified=True)
        control = self.install_git_wrapper('before')
        original = self.start_cli('integrate', '--task', self.task)
        barrier = self.wait_barrier(control, original)
        # This commit and writer are independent of the candidate and gate internals.
        (self.repo / 'external.txt').write_text('External writer owns this value.\n', encoding='utf-8')
        self.git('add', 'external.txt')
        self.git('commit', '-m', 'External writer during integration')
        external = self.git('rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(self.ref(), external)
        self.release(barrier)
        reply = self.parse_cli(self.complete(original))
        self.check(reply['ok'] is False, 'CAS rejects a changed expected old value', False, reply['ok'])
        self.check(self.ref() == external, 'CAS preserves the external writer reference', external, self.ref())
        self.check(self.status()['state'] != 'accepted', 'Lost CAS cannot accept the task',
                   'not accepted', self.status()['state'])
        self.finish_checks()


def main():
    suite = unittest.TestSuite([CASRace('test_external_write_between_read_and_cas_is_preserved')])
    result = unittest.TextTestRunner(verbosity=2, resultclass=recovery.EvidenceResult).run(suite)
    recovery.write_new(os.environ['COOP_E2E_TRACE'], {
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'results': recovery.TEST_RESULTS, 'assertions': recovery.ASSERTIONS,
        'commands': helper.COMMANDS, 'artifacts': helper.ARTIFACTS,
    })
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
