"""Finish #322 archive verification/root removal; no signal or daemon command."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-gbxz0tyb')
PIDS = [48453, 48454, 48461, 48560, 48562, 48938, 48939, 52257, 52258]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def ps(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}, timeout=5)
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def validate_receipts(owner, approval, prior, archived):
    assert owner['root'] == approval['root'] == prior['root'] == archived['root'] == str(ROOT)
    assert approval['pids'] == PIDS and approval['approved_by'] == 'executor'
    assert approval['approval_ref'] == prior['approval_ref'] and '主控 #322' in approval['approval_ref']
    assert prior['status'] == 'BLOCKED' and prior['root_removed'] is False
    assert prior['error'] == "OperationalError('unable to open database file')" and 'redactor.collect(owner)' in prior['traceback']
    assert prior['daemon_stop']['exit_code'] == 0
    receipt = json.loads(prior['daemon_stop']['stdout'])
    assert receipt['ok'] is True and receipt['pid'] == 48461 and receipt['stopping'] is True
    assert prior['signals_sent'] == [{'pid': 48453, 'signal': 'SIGTERM'}, {'pid': 48454, 'signal': 'SIGTERM'}]
    assert archived['status'] == 'PASS' and archived['byte_readback'] == 'PASS'
    assert archived['archive'] == owner['external_archive'] == approval['external_archive']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ['owner', 'approval', 'prior-result', 'redaction-result', 'output']:
        parser.add_argument('--' + flag, type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(exist_ok=False)
    record = {'status': 'BLOCKED', 'root': str(ROOT), 'signals_sent': [], 'daemon_commands_sent': [],
              'root_removed': False, 'slots_removed': [], 'dry_run': args.dry_run,
              'scope': 'Only archive readback and remaining root removal after #322; no SQLite access'}
    try:
        owner = json.loads(args.owner.read_bytes()); approval = json.loads(args.approval.read_bytes())
        prior = json.loads(args.prior_result.read_bytes()); archived = json.loads(args.redaction_result.read_bytes())
        validate_receipts(owner, approval, prior, archived)
        assert ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        assert not (ROOT / 'state/control.sock').exists() and not (ROOT / 'state/daemon.pid').exists()
        observed = {pid: ps(pid) for pid in PIDS}; assert all(value is None for value in observed.values()), 'PID_present_no_action'
        redactor = load('a14_finish_redactor', BASE / 'redact-a14-scene.py')
        cleanup = load('a14_finish_archive_check', BASE / 'cleanup-09b-a14.py')
        # The archived summary already matched the live scene before #322's
        # daemon_stop, as the preserved source/control flow and receipt show.
        summary = redactor.verify_archive(archived)
        cleanup.verify_archive_after_stop(redactor, archived, summary)
        assert Path(archived['archive']).stat().st_size == archived['archive_bytes']
        assert {pid: ps(pid) for pid in PIDS} == observed, 'PID_changed_no_action'
        record.update(archive=archived['archive'], archive_bytes=archived['archive_bytes'],
                      archive_inventory=archived['inventory'], byte_readback='PASS', process_observations=observed,
                      prior_result=str(args.prior_result.resolve()), approval_ref=approval['approval_ref'],
                      post_stop_validation='archive only; no collect or SQLite/WAL access')
        if not args.dry_run:
            shutil.rmtree(ROOT); assert not ROOT.exists(); record['root_removed'] = True
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists())
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: record.get(key) for key in ['status', 'dry_run', 'signals_sent', 'root_removed', 'error']}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
