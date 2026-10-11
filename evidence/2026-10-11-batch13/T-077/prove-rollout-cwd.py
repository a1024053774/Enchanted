#!/usr/bin/env python3
"""Read recorded real/fixture evidence; never launch Codex or a daemon."""
import argparse
import json
from pathlib import Path
import tarfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
REAL = ROOT / 'evidence/2026-10-11-batch13/T-076/card-1/outside-real-04'
FAILED = ROOT / 'evidence/2026-10-11-batch13/T-077/outside-rebase-01-shutdown'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    launch = json.loads((REAL / 'launch-record.json').read_text(encoding='utf-8'))
    real_run = json.loads((REAL / 'run.json').read_text(encoding='utf-8'))
    launch_cwd = launch['argv'][launch['argv'].index('-C') + 1]
    member = 'state/traces/' + launch['id'] + '/native.jsonl'
    with tarfile.open(REAL / 'fixture-artifacts.tar.gz', 'r:gz') as archive:
        metadata = json.loads(archive.extractfile(member).readline())
    events = json.loads((REAL / 'orchestration-events.json').read_text(encoding='utf-8'))
    if isinstance(events, dict):
        events = events['events']
    rows = [e for e in events if e['type'] == 'native_record' and e['launch'] == launch['id'] and
            e['data']['record']['type'] == 'session_meta']
    payload = metadata['payload']
    checks = {
        'real_run_passed': real_run['status'] == 'PASS',
        'recorded_cli_0_162_1': launch['cli_version'] == 'codex-cli 0.162.1' and payload['cli_version'] == '0.162.1',
        'root_cli': metadata['type'] == 'session_meta' and payload['source'] == 'cli',
        'native_identity_matches_real_run': payload['id'] == real_run['native_session'] and launch['id'] == real_run['launch'],
        'cwd_matches_launch_C_and_worktree': payload['cwd'] == launch_cwd == launch['worktree'],
        'archive_equals_recorded_root_event': len(rows) == 1 and rows[0]['data']['record'] == metadata,
    }
    failed = json.loads((FAILED / 'run.json').read_text(encoding='utf-8'))
    artifact = next(a for a in failed['artifacts'] if a['test'].endswith('test_native_binds_after_first_input'))
    case = Path(artifact['case'])
    before = json.loads((case / 'before-first-input.json').read_text(encoding='utf-8'))
    with tarfile.open(FAILED / 'fixtures.tar.gz', 'r:gz') as archive:
        members = [m.name for m in archive if m.isfile() and
                   m.name.startswith(Path(artifact['root']).name + '/control/home/sessions/') and m.name.endswith('.jsonl')]
        assert len(members) == 1
        fixture_meta = json.loads(archive.extractfile(members[0]).readline())
    readback = json.loads((case / 'before-cleanup-stop.json').read_text(encoding='utf-8'))
    orchestration = readback['tables']['orchestration_events']
    counts = {key: sum(row['type'] == key for row in orchestration)
              for key in ('native_record', 'turn_submit_intent', 'pane_idle')}
    checks.update(fixture_cwd_missing='cwd' not in fixture_meta['payload'],
                  input_preceded_wait_failure=counts['turn_submit_intent'] == 1 and counts['native_record'] == 0,
                  one_expected_fixture_error=not failed['failures'] and len(failed['errors']) == 1 and
                  failed['errors'][0]['test'] == artifact['test'])
    record = {'status': 'PASS' if all(checks.values()) else 'INCOMPLETE',
              'scope': 'Recorded Codex 0.162.1 cwd fact and shutdown fixture diagnosis',
              'checks': checks, 'real_source': str(REAL), 'archive_member': member,
              'root_event_sequence': rows[0]['seq'], 'root_rollout_file': rows[0]['data']['file'],
              'launch': {key: launch[key] for key in ('id', 'cli_version', 'worktree')}, 'launch_C': launch_cwd,
              'session_meta_excerpt': {key: payload[key] for key in ('id', 'source', 'cli_version', 'cwd')},
              'failed_source': str(FAILED), 'failed_archive_member': members[0],
              'failed_metadata': fixture_meta, 'failed_attempt_workspace': before['current_attempt']['workspace'],
              'before_cleanup_event_counts': counts, 'new_real_codex_turns': 0}
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps({'status': record['status'], 'checks': checks, 'new_real_codex_turns': 0}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
