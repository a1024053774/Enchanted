"""Known real hook-review UI must not receive an automatic task/Enter."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'acceptance'))
import test_run_e2e as checks

# T-027 captured this exact UI with a misleading idle detection state.
checks.MUSTER_BOUNDARY = checks.MUSTER_BOUNDARY.replace(
    'stdout = "Isolated boundary: " + p["agent_status"] + ".\\n"',
    'stdout = "Hooks need review\\n17 hooks are new or changed.\\n1. Review hooks\\n2. Trust all and continue\\n3. Continue without trusting\\nenter confirm"')


class StartupPermission(checks.RunCLI):
    def runTest(self):
        self.create()
        result = self.process(self.cli_argv('run', *self.run_args(2)), label='startup-permission-gate')
        self.failed_run(result)
        self.check(not self.store()['prompts'], 'Hook trust UI receives no prompt or Enter', [], self.store()['prompts'])
        self.check(not self.store()['closes'] and len(self.store()['panes']) == 3,
                   'Permission waiting preserves the owned pane for controller approval',
                   [[], 3], [self.store()['closes'], len(self.store()['panes'])])
        self.finish_checks()


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    artifacts = ROOT / '.runtime' / ('t029-' + output.name)
    artifacts.mkdir(parents=True, exist_ok=False)
    os.environ['COOP_E2E_ARTIFACT_ROOT'] = str(artifacts)
    result = unittest.TextTestRunner(verbosity=2, resultclass=checks.EvidenceResult).run(unittest.TestSuite([StartupPermission()]))
    checks.write_new(output / 'result.json', dict(status='PASS' if result.wasSuccessful() else 'INCOMPLETE',
                      assertions=checks.ASSERTIONS, results=checks.TEST_RESULTS,
                      commands=checks.COMMANDS, artifacts=checks.ARTIFACTS))
    sys.exit(0 if result.wasSuccessful() else 1)
