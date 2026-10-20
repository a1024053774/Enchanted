"""Actual cleanup helper; supplied ps observations, clock and signal boundary.

Failures: E/Z command truncation rejected, exit declared before disappearance,
signals sent to E/Z, Claude's live version title rejected, PID reuse accepted,
unrelated live command mismatch accepted, inspection
errors swallowed, or a persistent exit/live state reported as successful cleanup.
No process is spawned or signalled by these cases. Python 3.9.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import types
from unittest.mock import patch


BASELINE = '92bc8820800bf7990cacfb3bcb4cddcfe4b48217'
LIVE_TITLE_BASELINE = '363c4944e33a7b6717a55392a16a4cae364cbdda'
OWNER = dict(pid=73428, pgid=73428, ppid=73400,
             started='Tue Oct 20 10:28:50 2026', stat='S+', command='fixture-cli --session-id original')
CLAUDE_OWNER = dict(OWNER, command='/Users/luckye/.local/bin/claude --session-id original')
VERSIONED_CLAUDE_OWNER = dict(OWNER, command='/Users/luckye/.local/share/claude/versions/2.1.304 --session-id original')


def load(source):
    module = types.ModuleType('cleanup_contract_subject')
    exec(compile(source, 't108_cleanup.py', 'exec'), module.__dict__)
    return module


def exercise(module):
    results = []

    def state(stat='S+', **changes):
        return dict(OWNER, **dict(stat=stat, **changes))

    def case(name, observations, expected_signals=(), refusal=None, owner=OWNER):
        pending, reads, signals, clock = list(observations), [], [], [0.0]

        def observe(pid):
            assert pid == OWNER['pid'], 'Inspect only the caller-owned PID'
            found = pending.pop(0) if len(pending) > 1 else pending[0]
            if isinstance(found, Exception):
                raise found
            reads.append(found)
            return found

        def kill(pid, sig):
            assert pid == OWNER['pid'], 'Signal only the caller-owned PID'
            signals.append(sig)

        def sleep(seconds):
            assert seconds > 0
            clock[0] += seconds

        with patch.object(module, 'observe', observe), patch.object(module.os, 'kill', kill), \
                patch.object(module.time, 'monotonic', lambda: clock[0]), patch.object(module.time, 'sleep', sleep):
            receipt, error = None, None
            try:
                receipt = module.stop_owned(dict(owner))
            except RuntimeError as failure:
                error = str(failure)
        assert signals == list(expected_signals), (name, 'Unexpected cleanup signals', signals, error)
        if refusal:
            assert error and refusal in error, (name, 'Expected cleanup refusal', error, receipt)
        else:
            assert error is None, (name, 'Owned exiting process must be awaited', error)
            assert receipt['pid'] == OWNER['pid'] and receipt['status'] == 'exited', (name, receipt)
            assert receipt['signals'] == [sig.name for sig in expected_signals]
            assert reads[-1] is None, (name, 'Do not declare exit before the PID disappears', reads)
            if any(row and any(flag in row['stat'] for flag in ('E', 'Z')) for row in reads):
                assert clock[0] > 0, (name, 'Exit states require waiting')
        assert clock[0] <= 6.2, (name, 'Keep cleanup bounded', clock[0])
        results.append(dict(name=name, status='PASS', signals=[sig.name for sig in signals],
                            observed_states=[row['stat'] if row else None for row in reads],
                            elapsed=clock[0], receipt=receipt, refusal=error))

    case('mac_exiting_command_truncated', [state('?E', ppid=1, command='(2.1.304)'),
                                         state('?E', ppid=1, command='(2.1.304)'), None])
    case('zombie_waits_without_signal', [state('Z+', ppid=1, command='<defunct>'),
                                       state('Z+', ppid=1, command='<defunct>'), None])
    case('term_then_exiting_then_zombie', [state(), state('?E', ppid=1, command='(2.1.304)'),
                                          state('Z', ppid=1, command='<defunct>'), None], [signal.SIGTERM])
    for owner in (CLAUDE_OWNER, VERSIONED_CLAUDE_OWNER):
        kind = 'alias' if owner is CLAUDE_OWNER else 'versioned'
        case('live_claude_title_' + kind, [state('R', ppid=1, command='(2.1.304)'), None],
             [signal.SIGTERM], owner=owner)
    case('claude_retitles_after_term', [dict(CLAUDE_OWNER), state('R', ppid=1, command='(2.1.304)'), None],
         [signal.SIGTERM], owner=CLAUDE_OWNER)
    case('live_claude_title_persistent_still_fails', [state('R', command='(2.1.304)')],
         [signal.SIGTERM, signal.SIGKILL], refusal='Verified test process remains alive', owner=CLAUDE_OWNER)
    for key, value in [('pid', OWNER['pid'] + 1), ('pgid', OWNER['pgid'] + 1), ('started', 'another-start-time')]:
        case('reused_' + key + '_live_claude_title', [state('R', command='(2.1.304)', **{key: value})],
             refusal='Process identity changed', owner=CLAUDE_OWNER)
        case('changed_' + key + '_after_claude_term', [state('R', command='(2.1.304)'),
             state('R', command='(2.1.304)', **{key: value})], [signal.SIGTERM],
             refusal='Process identity changed', owner=CLAUDE_OWNER)
    case('version_title_does_not_authorize_unrelated_owner', [state('R', command='(2.1.304)')],
         refusal='Process identity changed')
    case('claude_arbitrary_live_command_still_refused', [state('R', command='another-program')],
         refusal='Process identity changed', owner=CLAUDE_OWNER)
    case('claude_malformed_title_still_refused', [state('R', command='(not-a-version)')],
         refusal='Process identity changed', owner=CLAUDE_OWNER)
    case('versioned_claude_different_title_still_refused', [state('R', command='(2.1.305)')],
         refusal='Process identity changed', owner=VERSIONED_CLAUDE_OWNER)
    for stat in ['?E', 'Z']:
        for key, value in [('pid', OWNER['pid'] + 1), ('pgid', OWNER['pgid'] + 1), ('started', 'another-start-time')]:
            case('reused_' + key + '_' + stat, [state(stat, **{key: value})], refusal='Process identity changed')
    case('live_command_mismatch_still_refused', [state(command='another-program')], refusal='Process identity changed')
    case('replacement_during_exit_wait_refused', [state('?E', command='(2.1.304)'),
                                                 state('Z', started='another-start-time')], refusal='Process identity changed')
    case('exit_flag_does_not_authorize_later_live_command', [state('?E', command='(2.1.304)'),
                                                           state('S+', command='another-program')], refusal='Process identity changed')
    case('persistent_exiting_times_out_without_signal', [state('?E', command='(2.1.304)')],
         refusal='Verified test process remains alive')
    case('persistent_zombie_times_out_without_signal', [state('Z', command='<defunct>')],
         refusal='Verified test process remains alive')
    case('already_absent', [None])
    case('normal_term_and_exit', [state(), None], [signal.SIGTERM])
    case('persistent_live_process_still_escalates_and_fails', [state()],
         [signal.SIGTERM, signal.SIGKILL], refusal='Verified test process remains alive')
    case('inspection_failure_propagates', [RuntimeError('Cannot inspect process identity: fixture')],
         refusal='Cannot inspect process identity')
    case('inspection_failure_after_term_propagates', [state(), RuntimeError('Cannot inspect process identity: fixture')],
         [signal.SIGTERM], refusal='Cannot inspect process identity')
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    assert not args.summary.exists(), 'Use a fresh summary path'
    source = Path(__file__).resolve().parents[2]
    env = dict(os.environ, LC_ALL='C')
    for key in ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE']:
        env.pop(key, None)
    report = dict(status='INCOMPLETE', scope='actual stop_owned; supplied ps/clock/signal boundaries',
                  model_calls=0, vendor_calls=0, cases=[])
    try:
        original = subprocess.check_output(['git', 'show', BASELINE + ':workbench/tests/t108_cleanup.py'], cwd=source, env=env, text=True)
        try:
            exercise(load(original))
        except AssertionError as error:
            report['known_bad'] = dict(revision=BASELINE,
                rejected='Owned exiting process must be awaited' in str(error) and 'Process identity changed' in str(error),
                error=str(error))
        assert report.get('known_bad', {}).get('rejected'), 'Baseline must reject the observed E-state command change'
        previous = subprocess.check_output(['git', 'show', LIVE_TITLE_BASELINE + ':workbench/tests/t108_cleanup.py'], cwd=source, env=env, text=True)
        try:
            exercise(load(previous))
        except AssertionError as error:
            report['live_title_known_bad'] = dict(revision=LIVE_TITLE_BASELINE,
                rejected='live_claude_title_alias' in str(error) and 'Process identity changed' in str(error), error=str(error))
        assert report.get('live_title_known_bad', {}).get('rejected'), 'Merged baseline must reject the observed running Claude title'
        report['cases'] = exercise(load((source / 'workbench/tests/t108_cleanup.py').read_text(encoding='utf-8')))
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
    with args.summary.open('x', encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), cases=len(report['cases']), error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
