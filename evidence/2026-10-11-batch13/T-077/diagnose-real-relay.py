#!/usr/bin/env python3
"""Retrospective read-only diagnosis of the completed four-turn experiment."""
import argparse
import json
from pathlib import Path
import sqlite3
import tarfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
BASE = ROOT / 'evidence/2026-10-11-batch13/T-077/real-conflict-01'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    launches = [json.loads((BASE / f'attempt-{n}/launch-record.json').read_text(encoding='utf-8')) for n in (1, 2)]
    container = json.loads((BASE / 'attempt-2/events-before-stop.json').read_text(encoding='utf-8'))
    events = container['events']
    first = (BASE / 'attempt-1/original-rollout.jsonl').read_bytes()
    old_meta = json.loads(first.splitlines()[0])['payload']
    with tarfile.open(BASE / 'attempt-2/fixture-artifacts.tar.gz', 'r:gz') as archive:
        files = [m for m in archive if m.isfile() and m.name.startswith('codex-home/sessions/') and m.name.endswith('.jsonl')]
        rollouts = []
        requests = [json.loads(archive.extractfile(f'request-files-a{n}/delivery.json').read()) for n in (1, 2)]
        unchanged = False
        for member in files:
            raw = archive.extractfile(member).read()
            metadata = json.loads(raw.splitlines()[0])['payload']
            if metadata['id'] == old_meta['id']:
                unchanged = raw == first
            rollouts.append({'member': member.name, 'bytes': len(raw),
                             'metadata': {k: metadata[k] for k in ('id', 'source', 'cwd', 'cli_version')}})
    rows = []
    for launch in launches:
        metadata = [e for e in events if e['launch'] == launch['id'] and e['type'] == 'native_record' and
                    e['data']['record']['type'] == 'session_meta' and e['data']['record']['payload'].get('source') == 'cli']
        assert len(metadata) == 1
        m = metadata[0]['data']['record']['payload']
        stops = [e for e in events if e['launch'] == launch['id'] and e['type'] == 'turn_end_signal']
        idle = [e for e in events if e['launch'] == launch['id'] and e['type'] == 'pane_idle']
        rows.append({'launch': launch['id'], 'attempt': launch['attempt'], 'fence': launch['fence'],
                     'metadata_seq': metadata[0]['seq'], 'native': m['id'], 'cwd': m['cwd'],
                     'workspace_matches': m['cwd'] == launch['worktree'],
                     'stop_sequences': [e['seq'] for e in stops], 'idle_sequences': [e['seq'] for e in idle],
                     'stops_match_native': bool(stops) and all(e['data']['session_id'] == m['id'] for e in stops)})
    rejected = [{'seq': e['seq'], 'launch': e['launch'], 'key': e['data']['key'], 'result': e['data']['result']}
                for e in events if e['type'] == 'relay_rejected' and e['launch'] == launches[1]['id']]
    db_path = BASE / 'attempt-2/databases-after-stop/state.sqlite3'
    with sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        intents = [dict(r) for r in db.execute('SELECT key,launch,task,attempt,request_id FROM relay_requests')]
        gate_events = [dict(r) for r in db.execute("SELECT type,attempt FROM events WHERE type IN ('submitted','runtime_bound')")]
        task = json.loads(db.execute('SELECT data FROM tasks').fetchone()[0])
    checks = {
        'old_rollout_bytes_preserved': unchanged,
        'two_distinct_native_roots': len(rollouts) == 2 and rows[0]['native'] != rows[1]['native'],
        'each_launch_observed_its_own_cwd_and_stop': all(r['workspace_matches'] and r['stops_match_native'] for r in rows),
        'same_request_label_new_binding': requests[0]['request_id'] == requests[1]['request_id'] == 'delivery' and
                                         requests[0]['attempt'] != requests[1]['attempt'] and requests[1]['fence'] == 2,
        'second_launch_rejected_before_intent': len(rejected) == 2 and all(r['result']['error'] == 'relay_request_id_reused' for r in rejected) and
                                              not any(r['launch'] == launches[1]['id'] for r in intents),
        'second_submit_never_reached_gate': not any(r['type'] == 'submitted' and r['attempt'] == launches[1]['attempt'] for r in gate_events),
        'claimed_binding_not_yet_persisted': task['state'] == 'claimed' and task['candidate_commit'] is None and
                                           task['current_attempt']['runtime_identity']['native_session'] is None,
    }
    result = {'status': 'PASS' if all(checks.values()) else 'INCOMPLETE',
              'scope': 'Read-only retrospective diagnosis; real end-to-end result remains INCOMPLETE',
              'checks': checks, 'launch_observations': rows, 'archived_rollouts': rollouts,
              'requests': requests, 'rejections': rejected, 'relay_intents': intents, 'gate_events': gate_events,
              'sources': [str(BASE / 'attempt-2/events-before-stop.json'), str(db_path),
                          str(BASE / 'attempt-2/fixture-artifacts.tar.gz'), str(BASE / 'attempt-1/original-rollout.jsonl')],
              'real_turns_consumed': 4, 'new_real_turns': 0}
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps({'status': result['status'], 'checks': checks, 'new_real_turns': 0}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
