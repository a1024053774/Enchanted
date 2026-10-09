"""Run the original eight delivery cases and the approved nine recovery cases."""
import json
import os
from pathlib import Path
import unittest

import test_coop_e2e as helper
import test_recovery_e2e as recovery

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromTestCase(helper.ManagedDeliveryCLI),
    unittest.TestSuite(recovery.RecoveryCLI(name) for name in recovery.RecoveryCLI.__dict__ if name.startswith('test_')),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
with Path(os.environ['COOP_E2E_TRACE']).open('x', encoding='utf-8') as out:
    json.dump(dict(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   assertions=recovery.ASSERTIONS, commands=helper.COMMANDS, artifacts=helper.ARTIFACTS,
                   suite_sources=[str(Path(helper.__file__).resolve()), str(Path(recovery.__file__).resolve())]), out, ensure_ascii=False, indent=2)
    out.write('\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
