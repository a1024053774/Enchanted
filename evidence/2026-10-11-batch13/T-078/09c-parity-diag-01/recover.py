"""Finish only the blocked parity rehearsal; never repeat daemon_stop or keys."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE.parents[2]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
import t078_raw_retention as raw

ROOT = Path('/private/tmp/t078-2-a14-rehearsal-xlbempfy')
FLOW = BASE / '09c-caffeinate-parity-rehearsal-01/flow'
STAGE = FLOW / 'retention-staging'
OLD_ARCHIVE = FLOW / 'retention-archive/scene.tar.gz'
EXTERNAL = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-parity-recovery-01')
ARCHIVE = EXTERNAL / 'scene.tar.gz'
EXPECTED = {'daemon': 26924, 'target_shell': 27014, 'target_leader': 27016,
            'ideation_shell': 27047, 'ideation_cli': 27048,
            'executor_shell': 27061, 'executor_cli': 27062,
            'ideation_api': 26921, 'executor_api': 26923}
APIS = ['ideation_api', 'executor_api']
HELPERS = [27049, 27063]
HARNESS = 26889


def inputs():
    owner = raw.read_json(ROOT / 'raw-owner.json')
    raw.require(owner['root'] == str(ROOT) and owner['scene'] == '09C' and
                owner['source_revision'] == 'e26a7379d5747398ce7ab7b900f7e55cb5837013', 'wrong_original_owner')
    raw.require({key: value['pid'] for key, value in owner['processes'].items()} == EXPECTED, 'wrong_original_PIDs')
    raw.validate_owner_receipts(owner)
    # This is exactly the effective owner used by CScene.cleanup, not a new scene.
    owner = {**owner, 'evidence_trees': owner['evidence_trees'] +
             [str(FLOW / 'coordinator-01'), str(FLOW / 'startup-topology')]}
    prior = raw.read_json(FLOW / 'cleanup-standard/result.json')
    raw.require(prior['status'] == 'BLOCKED' and prior['signals_sent'] == [] and
                prior['root_removed'] is False and
                prior['error'] == "ValueError('owned_process_exit_unconfirmed')" and
                'runtime.wait_absent(managed, 20)' in prior['traceback'], 'wrong_prior_failure')
    raw.require([row['name'] for row in prior['steps']] == ['OWNERS_VERIFIED',
                'ARCHIVE_BYTES_AND_RAW_FILES_VERIFIED_BEFORE_STOP', 'DAEMON_STOP_RETURNED', 'BLOCKED'],
                'prior_stop_sequence_changed')
    intent = raw.read_json(FLOW / 'retention-archive/shutdown-intent.json')
    raw.require(intent['root'] == str(ROOT) and intent['processes'] == owner['processes'], 'original_shutdown_intent_required')
    helpers = raw.read_json(FLOW / 'cleanup-standard/auxiliary-before-stop.json')
    raw.require(sorted(row['pid'] for row in helpers) == HELPERS, 'wrong_original_helpers')
    for row in helpers:
        raw.require(row['executable'] == '/usr/bin/caffeinate' and row['command'] == 'caffeinate -i -t 300' and
                    row['ppid'] == EXPECTED[row['role'] + '_cli'], 'helper_original_identity_changed')
    raw.require(raw.verify_archive(STAGE, OLD_ARCHIVE) ==
                raw.read_json(FLOW / 'retention-archive/bundle.archive.json')['inventory'], 'original_archive_changed')
    raw.require(raw.readback(OLD_ARCHIVE) == raw.read_json(FLOW / 'retention-readback.json')['counts'], 'original_recount_changed')
    raw.assert_stable(owner, STAGE)  # Files only. No SQLite/WAL open anywhere in this recovery.
    return owner, prior, helpers


def signed(approval, owner):
    for key in ['root', 'scene', 'source_revision', 'target_binding', 'processes']:
        raw.require(approval.get(key) == owner[key], 'recovery_approval_mismatch:' + key)
    raw.require(approval.get('approved_by') == 'executor' and bool(approval.get('approval_ref')) and
                approval.get('archive') == str(ARCHIVE) and approval.get('operation') == 'two_API_SIGTERM_then_remove_root' and
                approval.get('daemon_stop_allowed') is False, 'signed_recovery_approval_required')


def ps(pid, out, tag):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,ppid=,pgid=,stat=,lstart=,command='],
                            capture_output=True, text=True, timeout=5, env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
    raw.save(out / (tag + '.json'), {'pid': pid, 'at': time.time(), 'exit': result.returncode,
                                    'stdout': result.stdout, 'stderr': result.stderr})
    raw.require(not result.stderr.strip() and result.returncode in (0, 1), 'ps_read_failed:' + str(pid))
    if result.returncode == 1:
        raw.require(not result.stdout.strip(), 'ambiguous_absence:' + str(pid)); return None
    lines = result.stdout.splitlines()
    raw.require(len(lines) == 1, 'ambiguous_identity:' + str(pid))
    cells = lines[0].split(None, 9)
    raw.require(len(cells) == 10 and int(cells[0]) == pid, 'ps_parse_failed:' + str(pid))
    return {'identity': {'pid': pid, 'started': ' '.join(cells[4:9]), 'command': cells[9]},
            'ppid': int(cells[1]), 'pgid': int(cells[2]), 'stat': cells[3]}


def identities(owner, out, tag, alive):
    result = {}
    for passno in [1, 2]:
        sample = {}
        for label, expected in owner['processes'].items():
            value = ps(expected['pid'], out, f'{tag}-{passno}-{label}')
            if label in alive:
                raw.require(value is not None and value['identity'] == expected and value['ppid'] == 1 and
                            'Z' not in value['stat'], 'API_identity_or_parent_changed:' + label)
            else:
                raw.require(value is None, 'owned_PID_not_absent:' + label)
            sample[label] = value
        for pid in HELPERS + [HARNESS]:
            raw.require(ps(pid, out, f'{tag}-{passno}-absent-{pid}') is None, 'auxiliary_or_harness_not_absent:' + str(pid))
        result[str(passno)] = sample
    raw.require(not os.path.lexists(ROOT / 'state/control.sock') and not os.path.lexists(ROOT / 'state/daemon.pid'),
                'daemon_shutdown_not_complete')
    return result


def wait_absent(pid, out, tag):
    until = time.monotonic() + 3; index = 0
    while True:
        value = ps(pid, out, f'{tag}-{index:03d}'); index += 1
        if value is None: return
        raw.require(time.monotonic() < until, 'API_exit_unconfirmed:' + str(pid)); time.sleep(.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['inspect', 'archive', 'finish'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--approval', type=Path, default=Path(__file__).with_name('approval.json'))
    parser.add_argument('--readback', type=Path)
    parser.add_argument('--check-only', action='store_true', help='File/JSON/archive validation only; no ps or mutation.')
    args = parser.parse_args()
    owner, prior, helpers = inputs()
    if args.check_only:
        raw.require(not args.output.exists(), 'output_exists')
        print(json.dumps({'status': 'PASS', 'scope': 'file-only; no ps/API/stop/signal/delete',
                          'root': str(ROOT), 'old_archive_byte_readback': 'PASS', 'SQLite_reads': 0})); return 0
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    log = {'status': 'BLOCKED', 'root': str(ROOT), 'signal_intents': [], 'signals_sent': [], 'daemon_commands_sent': [],
           'root_removed': False, 'post_stop_SQLite_reads': 0, 'mode': args.mode}
    def persist():
        (out / 'result.json').write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    try:
        observed = identities(owner, out / 'ps', 'initial', APIS)
        log['identities_double_read'] = 'PASS'
        if args.mode != 'inspect':
            approval = raw.read_json(args.approval); signed(approval, owner)
            raw.require(Path('/Volumes/WD-Elements').is_mount() and EXTERNAL.resolve().parent ==
                        Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078'), 'external_volume_required')
            if args.mode == 'archive':
                stage = out / 'redacted'; shutil.copytree(STAGE, stage)
                # Preserve the original pre-stop SQLite projection, do not refresh it after stop.
                raw.save(stage / 'recovery-context.json', {'prior_failure': prior, 'original_auxiliaries': helpers,
                    'current_observations': observed, 'original_archive': str(OLD_ARCHIVE),
                    'scope': 'original pre-stop snapshot plus file-only recovery context; no new database reads'})
                capture = raw.archive_capture(owner, stage, ARCHIVE)
                raw.save(out / 'capture-result.json', capture)
                raw.save(out / 'readback-template.json', {'archive': str(ARCHIVE), 'counts': raw.readback(ARCHIVE),
                    'approved_by': None, 'approval_ref': None})
                raw.assert_stable(owner, STAGE)
                log.update(archive=str(ARCHIVE), archive_bytes=ARCHIVE.stat().st_size, byte_readback='PASS')
            else:
                raw.require(args.readback is not None, 'signed_readback_path_required')
                capture = raw.read_json(EXTERNAL / 'bundle.archive.json')
                readback = raw.read_json(args.readback)
                raw.require(capture['root'] == str(ROOT) and capture['source_revision'] == owner['source_revision'] and
                            capture['archive'] == str(ARCHIVE), 'external_archive_binding_changed')
                stage = Path(capture['staging'])
                raw.require(raw.verify_archive(stage, ARCHIVE) == capture['inventory'], 'external_archive_bytes_changed')
                raw.require(readback.get('approved_by') == 'executor' and bool(readback.get('approval_ref')) and
                            readback['archive'] == str(ARCHIVE) and readback['counts'] == raw.readback(ARCHIVE) ==
                            raw.readback(OLD_ARCHIVE), 'signed_independent_tar_recount_required')
                raw.assert_stable(owner, STAGE)
                identities(owner, out / 'ps', 'before-signal', APIS)
                raw.save(EXTERNAL / 'recovery-intent.json', {'root': str(ROOT), 'processes': owner['processes'],
                    'approval_ref': approval['approval_ref'], 'operation': 'no daemon_stop; one SIGTERM per API'})
                alive = list(APIS)
                for label in APIS:
                    # Recheck both remaining APIs before the first signal and the exact second identity later.
                    identities(owner, out / 'ps', 'signal-' + label, alive)
                    intent = {'pid': EXPECTED[label], 'signal': 'SIGTERM'}
                    raw.save(EXTERNAL / (label + '-SIGTERM-intent.json'), intent)
                    log['signal_intents'].append(intent); persist()
                    os.kill(EXPECTED[label], signal.SIGTERM)
                    log['signals_sent'].append(intent); persist()
                    wait_absent(EXPECTED[label], out / 'ps', 'exit-' + label); alive.remove(label)
                identities(owner, out / 'ps', 'all-exited', [])
                raw.verify_archive(stage, ARCHIVE); raw.assert_stable(owner, STAGE)
                raw.require(ROOT == raw.owned_root(owner), 'root_changed_before_delete')
                shutil.rmtree(ROOT)
                log.update(root_removed=not ROOT.exists(), archive=str(ARCHIVE),
                           archive_bytes=ARCHIVE.stat().st_size, byte_readback='PASS')
        log.update(status='PASS', planned_actions=['SIGTERM once: 26921', 'SIGTERM once: 26923',
                   'verify all nine + two helpers + old harness absent', 'verify archived bytes', 'remove exact root'])
    except Exception as error:
        log.update(error=repr(error), traceback=traceback.format_exc())
    persist(); print(json.dumps(log, ensure_ascii=False)); return 0 if log['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
