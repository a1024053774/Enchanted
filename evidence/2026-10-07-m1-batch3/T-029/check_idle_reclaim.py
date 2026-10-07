"""Accepted work cannot close a working worker; idle then permits reclaim."""
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'acceptance'))
import test_run_e2e as checks


class IdleReclaim(checks.RunCLI):
    def change_status(self, pane, status):
        with (self.boundary / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            store = self.store()
            store['panes'][pane]['agent_status'] = status
            store['panes'][pane]['state_change_seq'] += 1
            temporary = self.boundary / (uuid.uuid4().hex + '.store.tmp')
            checks.write_new(temporary, store)
            temporary.replace(self.boundary / 'store.json')

    def runTest(self):
        self.create()
        handle = self.start_run(seconds=8)
        pane = self.wait_prompt(handle)
        self.change_status(pane, 'working')
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        deadline = time.monotonic() + 8
        while self.status()['state'] != 'accepted':
            if handle['process'].poll() is not None:
                self.new_result(self.complete(handle), 'run')
                self.check(False, 'Valid submitted candidate reaches acceptance', 'accepted', self.status())
                self.finish_checks()
            if time.monotonic() >= deadline:
                raise checks.recovery.FixtureError('Did not reach accepted while worker stays working')
            time.sleep(.05)
        # Allow a complete observer/cleanup cycle without guessing one precise
        # scheduling instant. The external fake status remains working.
        time.sleep(1)
        observed = self.store()
        self.check(pane in observed['panes'] and not observed['closes'],
                   'A submitted accepted worker remains open while it is working',
                   'owned pane open; no close request', observed)
        if pane in observed['panes']:
            self.change_status(pane, 'idle')
        value = self.new_result(self.complete(handle), 'run')
        self.check(value['run']['outcome'] == 'completed', 'Idle permits completed run', 'completed', value['run'])
        self.only_own_close(pane)
        self.finish_checks()


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    artifacts = ROOT / '.runtime' / ('t029-' + output.name)
    artifacts.mkdir(parents=True, exist_ok=False)
    os.environ['COOP_E2E_ARTIFACT_ROOT'] = str(artifacts)
    result = unittest.TextTestRunner(verbosity=2, resultclass=checks.EvidenceResult).run(unittest.TestSuite([IdleReclaim()]))
    checks.write_new(output / 'result.json', dict(status='PASS' if result.wasSuccessful() else 'INCOMPLETE',
                      assertions=checks.ASSERTIONS, results=checks.TEST_RESULTS,
                      commands=checks.COMMANDS, artifacts=checks.ARTIFACTS))
    sys.exit(0 if result.wasSuccessful() else 1)
