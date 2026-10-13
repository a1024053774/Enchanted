"""真实门禁在目录已快进、引用尚未 CAS 时中断，必须恢复同一意图。"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'acceptance'))
import test_coop_e2e as helper
import test_recovery_e2e as recovery

WORKTREE_BARRIER = r'''
import json, os, pathlib, subprocess, sys, time, uuid
args = sys.argv[1:]
if "read-tree" not in args or "-n" in args:
    os.execv(REAL_GIT, [REAL_GIT] + args)
p = subprocess.run([REAL_GIT] + args, text=True, capture_output=True)
control = pathlib.Path(CONTROL)
identity = uuid.uuid4().hex
release = control / (identity + ".release")
data = {"pid": os.getpid(), "ppid": os.getppid(), "argv": [REAL_GIT] + args,
        "phase": "after-worktree", "release": str(release), "executed_real_git": True,
        "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
def save(suffix):
    (control / (identity + suffix)).write_text(json.dumps(data), encoding="utf-8")
save(".result.json")
if p.returncode == 0 and not (control / "release-all").exists():
    save(".entry.json")
    deadline = time.monotonic() + 40
    while not release.exists() and not (control / "release-all").exists():
        if time.monotonic() >= deadline:
            raise RuntimeError("worktree barrier expired")
        time.sleep(0.02)
save(".done.json")
try:
    sys.stdout.write(p.stdout)
    sys.stdout.flush()
except BrokenPipeError:
    sys.stdout = open(os.devnull, "w")
sys.stderr.write(p.stderr)
sys.exit(p.returncode)
'''


class WorkBranchRecovery(recovery.RecoveryCLI):
    def test_after_worktree_before_CAS_recovers_same_intent(self):
        attempt, candidate = self.setup_candidate(verified=True)
        control = self.root / 'worktree barrier'
        control.mkdir()
        self.controls.append(control)
        bin_dir = self.root / 'worktree tools'
        bin_dir.mkdir()
        wrapper = bin_dir / 'git'
        wrapper.write_text('#!' + sys.executable + '\nREAL_GIT = ' + repr(recovery.REAL_GIT)
                           + '\nCONTROL = ' + repr(str(control)) + '\n' + WORKTREE_BARRIER, encoding='utf-8')
        wrapper.chmod(0o755)
        self.env['PATH'] = str(bin_dir) + os.pathsep + self.original_path
        original = self.start_cli('integrate', '--task', self.task)
        entry = self.wait_barrier(control, original)
        self.check(entry[1]['exit_code'] == 0, 'Real Git completed the worktree update', 0, entry[1])
        before = self.snapshot('after-worktree-before-CAS')
        self.check(self.ref() == self.base, 'Reference remains G before CAS', self.base, self.ref())
        self.check((self.repo / 'pager.py').read_bytes() == Path(attempt['workspace'], 'pager.py').read_bytes(),
                   'Worktree already contains the verified candidate', 'candidate content', str(self.repo))
        self.kill_owned_cli(original, 'after worktree update before reference CAS')
        (control / 'release-all').write_text('continue without a second barrier', encoding='utf-8')
        self.release(entry)
        self.wait_done(entry)
        log_before = self.reflog()
        self.cli('integrate', '--task', self.task)
        after = self.snapshot('worktree-recovery-completed')
        self.same_intent(before, after)
        self.preserved_history(before, after)
        self.check(self.ref() == candidate and after['status']['state'] == 'accepted',
                   'Recovery completes the original integration', candidate, after['status'])
        self.check(len(self.reflog().splitlines()) == len(log_before.splitlines()) + 1,
                   'Recovery performs exactly the missing reference update', 1,
                   len(self.reflog().splitlines()) - len(log_before.splitlines()))
        self.check(self.git('status', '--porcelain').stdout == '', 'Recovered worktree and index match M',
                   '', self.git('status', '--porcelain').stdout)
        accepted_log = self.reflog()
        self.cli('integrate', '--task', self.task)
        self.check(self.reflog() == accepted_log, 'Integration replay does not write Git', accepted_log, self.reflog())
        self.finish_checks()


def main():
    suite = unittest.TestSuite([WorkBranchRecovery('test_after_worktree_before_CAS_recovers_same_intent')])
    result = unittest.TextTestRunner(verbosity=2, resultclass=recovery.EvidenceResult).run(suite)
    recovery.write_new(os.environ['COOP_E2E_TRACE'], {
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'results': recovery.TEST_RESULTS, 'assertions': recovery.ASSERTIONS,
        'commands': helper.COMMANDS, 'artifacts': helper.ARTIFACTS,
    })
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
