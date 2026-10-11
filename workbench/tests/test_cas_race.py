"""R8 CAS 竞争：实际 Git 写入前 G 变化，须重验且保留外部提交。

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
        _, candidate = self.setup_candidate(verified=True)
        first = self.status()['verification']
        control = self.install_git_wrapper('before')
        original = self.start_cli('integrate', '--task', self.task)
        barrier = self.wait_barrier(control, original)
        # This commit and writer are independent of the candidate and gate internals.
        (self.repo / 'external.txt').write_text('External writer owns this value.\n', encoding='utf-8')
        self.git('add', 'external.txt')
        self.git('commit', '-m', 'External writer during integration')
        external = self.git('rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(self.ref(), external)
        # Keep the first live wrapper, but disarm injection for subsequent Git
        # invocations. The frozen wrapper treats release-all as cleanup/abort.
        restored = self.git_route.with_suffix('.unwrapped.json')
        recovery.write_new(restored, {'executable': recovery.REAL_GIT})
        restored.replace(self.git_route)
        (self.oracle_control / 'release-all').write_text('continue', encoding='utf-8')
        self.release(barrier)
        reply = self.parse_cli(self.complete(original))
        self.check(reply['ok'] is True, 'CAS failure revalidates before integration', True, reply['ok'])
        current = self.status()
        verification = current['verification']
        self.check(current['state'] == 'accepted', 'Only the new complete verification accepts', 'accepted', current['state'])
        self.check(verification['verification_id'] != first['verification_id'] and verification['G'] == external and
                   verification['C'] == candidate,
                   'CAS revalidation binds the new G and unchanged C', [external, candidate], verification)
        for ancestor in (external, candidate):
            relation = self.process(['git', '-C', self.repo, 'merge-base', '--is-ancestor', ancestor, self.ref()])
            self.check(relation.returncode == 0, 'CAS integration preserves ancestor ' + ancestor, 0, relation.returncode)
        content = (self.repo / 'external.txt').read_text(encoding='utf-8') if (self.repo / 'external.txt').exists() else None
        self.check(content == 'External writer owns this value.\n', 'CAS preserves external writer content',
                   'External writer owns this value.\n', content)
        self.check(len(self.entries(self.oracle_control)) == 2, 'CAS revalidation executes the oracle again', 2,
                   len(self.entries(self.oracle_control)))
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
