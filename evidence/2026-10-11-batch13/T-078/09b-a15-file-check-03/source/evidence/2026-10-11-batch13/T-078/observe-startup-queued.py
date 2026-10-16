"""Read the real refreshed inbox receipt after one executor startup key."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import traceback

SOURCE = Path(__file__).resolve().parents[3]


def validate(value, entry_id):
    assert value['entry_id'] == entry_id == value['refreshed']['entry']['id']
    assert value['refreshed']['delivery']['state'] == 'queued', 'startup refreshed receipt must remain queued'
    assert not any(row['state'] == 'delivered' for row in value['history']), 'startup delivery history contains delivered'
    assert value['state'] == 'unknown' and value['active'] is None
    assert value['queue'] == [value['refreshed']['delivery']['message']]
    assert not value['I2'], 'startup must not register I2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p1', type=Path, required=True)
    parser.add_argument('--i1-result', type=Path, required=True)
    parser.add_argument('--expected-keys', type=int, choices=range(1, 7), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    result = {'status': 'INCOMPLETE', 'scope': 'read-only gate inbox refresh, pane status and SQLite; no keys/release/send/ack'}
    try:
        inp = json.loads((args.p1 / 'input.json').read_bytes()); root = Path(inp['root'])
        original = json.loads(args.i1_result.read_bytes()); assert original['status'] == 'READY_FOR_EXECUTOR'
        assert inp['preset'] == 'executor'; entry = original['stop_entry']
        env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
        env['A2A_OPERATOR_CREDENTIAL'] = str(root / 'operator.json')
        def gate(*argv):
            response = subprocess.run(['node', str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', inp['state'], *argv], cwd=SOURCE, env=env, capture_output=True, text=True, timeout=10)
            assert response.returncode == 0, 'read_only_gate_refused'
            payload = json.loads(response.stdout); assert payload['ok'] is True
            return payload
        listed = gate('inbox_list', '--role', 'executor')
        refreshed = next(row for row in listed['entries'] if row['entry']['id'] == entry['id'])
        pane = gate('pane_status', '--thread', inp['thread'])
        assert pane['launch'] == inp['launch'] and refreshed['delivery']['thread'] == inp['thread']
        assert refreshed['entry']['created_at'] == entry['created_at']
        with closing(sqlite3.connect((root / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            history = [json.loads(row[0]) for row in db.execute('SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq', (entry['id'],))]
            feedback = [row[0] for row in db.execute("SELECT seq FROM orchestration_events WHERE type IN ('relay_feedback_intent','relay_feedback_registered') AND json_extract(data,'$.entry_id')=?", (entry['id'],))]
            keys = db.execute("SELECT count(*) FROM orchestration_events WHERE launch=? AND type='controller_screen_key_written'", (inp['launch'],)).fetchone()[0]
            business = db.execute("SELECT count(*) FROM orchestration_events WHERE launch=? AND type IN ('paste_intent','turn_submit_intent','turn_submitted')", (inp['launch'],)).fetchone()[0]
        value = {'entry_id': entry['id'], 'refreshed': {'entry': {'id': refreshed['entry']['id']}, 'delivery': refreshed['delivery']},
                 'history': history, 'state': pane['state'], 'active': pane['active'], 'queue': pane['queued'], 'I2': feedback}
        validate(value, entry['id'])
        assert keys == args.expected_keys and business == 0
        requests = root / 'roles/executor/requests.ndjson'
        assert not requests.exists() or not requests.read_text(encoding='utf-8').splitlines()
        result.update(status='PASS', observation=value, startup_keys=keys, business_inputs=business)
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(args.output), 'error': result.get('error')}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
