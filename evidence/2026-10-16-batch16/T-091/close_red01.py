#!/usr/bin/env python3
"""Controller-only cleanup for red-01 Electron PID 6599 and its exact fixture.

Starts: no Electron, daemon, agent, API or PTY. Hooks/keys/model turns: 0.
Reads /bin/ps; requests normal quit ONLY through NSRunningApplication.terminate()
for PID 6599 after checking start time, full command and fixture. No force quit,
signals, process-group operations, daemon_stop, restart, deletion or PID override.
If normal quit fails or identity changes, stop and report BLOCKED. After verified
exit of every recorded writer, copy the fixture to a NEW external directory,
compare file count/bytes, retain the original and save a text archive manifest.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import traceback

from owned_electron import confirm_owner, normal_quit, read_process
from run_red import inventory, write_json

PID = 6599
STARTED = 'Sat Oct 17 06:30:34 2026'
SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t091')
FIXTURE = Path('/private/tmp/t078-2-t091-red-05cht89k')
ROOT = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091')
OLD = ROOT / 'red-01'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='NEW directory directly under external T-091 evidence root')
    parser.add_argument('--label', default='red-01-close-01')
    parser.add_argument('--approval-ref', required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not os.path.ismount('/Volumes/WD-Elements') or output.parent != ROOT.resolve():
        raise RuntimeError('mounted_external_output_required')
    if not args.label or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for char in args.label):
        raise RuntimeError('invalid_summary_label')
    script_dir = Path(__file__).resolve().parent
    for suffix in ['run.json', 'archive.json']:
        if (script_dir / f'{args.label}.{suffix}').exists():
            raise RuntimeError('cleanup_summary_exists; use a new output and label')
    output.mkdir(exist_ok=False)
    result = {'status': 'BLOCKED', 'scope': 'red-01 PID 6599 normal quit and stopped-fixture archive only',
              'approval_ref': args.approval_ref, 'argv': sys.argv, 'pid': PID, 'fixture': str(FIXTURE),
              'red_01_status': 'INCOMPLETE', 'red_observed': False, 'keys': [], 'model_turns': 0,
              'zero_input_basis': 'controller #30 reports no key or model turn; cleanup adds neither'}

    def observe(event):
        with (output / 'cleanup-events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + '\n')

    try:
        recorded = json.loads((OLD / 'run.json').read_text(encoding='utf-8'))
        plan = json.loads((OLD / 'window-plan.json').read_text(encoding='utf-8'))
        command = json.loads((OLD / 'electron-command.json').read_text(encoding='utf-8'))
        executable = str(SOURCE / 'workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron')
        driver = str(script_dir / 'red_window.mjs')
        argv = [executable, driver, str(OLD / 'window-plan.json'), str(OLD / 'observer-events.jsonl')]
        if FIXTURE.resolve(strict=True) != FIXTURE or recorded['fixture'] != str(FIXTURE) or \
                plan['state'] != str(FIXTURE / 'state') or plan['userData'] != str(FIXTURE / 'ui') or \
                command != {'argv': argv, 'start_new_session': True}:
            raise RuntimeError('red_01_fixture_or_command_binding_changed')
        if not any(row.get('owned_pid') == PID for row in recorded['cleanup_errors']):
            raise RuntimeError('red_01_does_not_record_pid_6599')
        owner = {'pid': PID, 'started': STARTED, 'command': ' '.join(argv),
                 'executable': executable, 'driver': driver}
        write_json(output / 'expected-owner.json', owner)
        current = confirm_owner(owner)
        observe({'identity_before_normal_quit': current})
        # Other PIDs are read-only checks. This script has no operation to stop them.
        writers = json.loads((OLD / 'owned-processes.json').read_text(encoding='utf-8'))
        if {row['pid'] for row in writers} != {5171, 5524, 5535, 5574, 5575, 5744, 5750}:
            raise RuntimeError('red_01_writer_inventory_changed')
        for writer in writers:
            value = read_process(writer['pid'])
            observe({'writer_pid': writer['pid'], 'current': value})
            if value is not None:
                raise RuntimeError('another_recorded_pid_is_present; only_6599_cleanup_is_authorized')
        if (FIXTURE / 'state/control.sock').exists() or (FIXTURE / 'state/daemon.pid').exists():
            raise RuntimeError('daemon_stop_is_not_confirmed')
        normal_quit(owner, observe=observe, timeout=15)
        if confirm_owner(owner) is not None:
            raise RuntimeError('electron_exit_is_not_confirmed')
        for writer in writers:
            if read_process(writer['pid']) is not None:
                raise RuntimeError('writer_absence_changed_before_archive')
        before = inventory(FIXTURE)
        archive = output / 'fixture'
        shutil.copytree(FIXTURE, archive)
        after = inventory(archive)
        if before != after:
            raise RuntimeError('archive_file_count_or_bytes_mismatch')
        manifest = {'original': str(FIXTURE), 'archive': str(archive), **after,
                    'original_retained': True, 'comparison': before == after,
                    'replay': shlex.join([sys.executable, str(Path(__file__).resolve()), '--output', str(output) + '-new',
                                          '--label', args.label + '-new', '--approval-ref', '<本次新批准引用>'])}
        write_json(script_dir / f'{args.label}.archive.json', manifest)
        result.update(status='PASS', electron_exit_confirmed=True, archive=manifest,
                      scope='cleanup/archive only; red-01 remains INCOMPLETE and is not red-state evidence')
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    write_json(output / 'run.json', result)
    write_json(script_dir / f'{args.label}.run.json', result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
