"""Project only A14 counts, approved tools/results, errors and original I1 pending receipt."""
import argparse
import importlib.util
import json
import re
import shlex
import sqlite3
import tarfile
import traceback
from contextlib import closing
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve().parents[3]
ROOT = Path('/private/tmp/t078-2-09b-run-gbxz0tyb')


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line] if path.exists() else []


def code(value):
    if value is None:
        return None
    assert isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', value), 'non-code error text must not enter archive'
    return value


def safe_pending(request_id, result):
    entry, delivery = result['entry'], result['delivery']
    assert result['ok'] is True and entry['kind'] == 'stop' and entry['from'] == 'ideation' and entry['to'] == 'executor'
    assert delivery['state'] == 'pending' and delivery['reason'] == 'role_session_missing' and delivery['entry_id'] == entry['id']
    assert not delivery.get('thread') and not delivery.get('message')
    return {'request_id': request_id, 'ok': True,
            'entry': {key: entry[key] for key in ['id', 'kind', 'from', 'to', 'reply_to', 'refs', 'created_at'] if key in entry},
            'delivery': {key: delivery[key] for key in ['entry_id', 'state', 'reason', 'created_at', 'thread', 'message'] if key in delivery}}


def tool_projection(row, role, owner, pending):
    body = json.loads(row.get('body_raw', '{}')); uses = []; results = []
    for message in body.get('messages', []):
        if not isinstance(message, dict) or not isinstance(message.get('content'), list):
            continue
        for block in message['content']:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'tool_use':
                assert role == 'ideation' and block.get('name') == 'Bash'
                assert isinstance(block.get('id'), str) and re.fullmatch(r'[A-Za-z0-9_-]{1,160}', block['id'])
                assert set(block['input']) == {'command'}
                argv = shlex.split(block['input']['command'])
                protocol = json.loads((BASE / '09b-materials-01/protocol.json').read_bytes())
                target = json.loads((Path(owner['stage_a']) / 'readiness.json').read_bytes())['target_binding']
                input_id = next(ref.split(':', 1)[1] for ref in pending['entry']['refs'] if ref.startswith('input:'))
                values = {'target.thread_id': target['thread_id'], 'target.attempt_id': target['attempt_id'], 'synthetic_user_input.id': input_id}
                expected = []
                for token in protocol['commands']['I_SEND_STOP']['argv']:
                    for key, value in values.items(): token = token.replace('{' + key + '}', value)
                    if token.endswith('/roles/ideation/stop-body.txt'): token = str(ROOT / 'roles/ideation/stop-body.txt')
                    expected.append(token)
                assert argv == expected, 'only the approved scratch I_SEND_STOP tool is retained'
                uses.append({'id': block['id'], 'name': 'Bash', 'input': {'command': block['input']['command']}})
            if block.get('type') == 'tool_result':
                content = block.get('content')
                if isinstance(content, list): content = ''.join(part['text'] for part in content if part.get('type') == 'text')
                payload = json.loads(content) if isinstance(content, str) else content
                assert isinstance(payload, dict)
                assert role == 'ideation' and payload.get('ok') is True and payload.get('queued') is True and payload.get('delivered') is False
                assert payload.get('request_id') == pending['request_id']
                assert Path(payload['path']) == ROOT / 'roles' / role / 'requests' / (pending['request_id'] + '.json')
                assert isinstance(block.get('tool_use_id'), str) and re.fullmatch(r'[A-Za-z0-9_-]{1,160}', block['tool_use_id'])
                safe = {key: payload[key] for key in ['ok', 'queued', 'delivered', 'request_id', 'path']}
                results.append({'tool_use_id': block['tool_use_id'], 'content': safe, 'is_error': bool(block.get('is_error', False))})
    return {'tool_use': uses, 'tool_result': results, 'error_code': code(row.get('error'))}


def collect(owner):
    assert Path(owner['root']) == ROOT and ROOT.is_dir()
    ideation_launch = owner['roles']['ideation']['launch']
    with closing(sqlite3.connect((ROOT / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        rows = db.execute('SELECT q.request_id,r.data FROM relay_requests q JOIN relay_results r ON q.key=r.key WHERE q.launch=?', (ideation_launch,)).fetchall()
        matches = [(request_id, json.loads(data)) for request_id, data in rows
                   if json.loads(data).get('ok') is True and json.loads(data).get('entry', {}).get('kind') == 'stop']
        assert len(matches) == 1
        pending = safe_pending(*matches[0])
        expected = json.loads(Path(owner['I1_result']).read_bytes())
        assert expected['status'] == 'READY_FOR_EXECUTOR' and expected['messages'] == 2
        assert pending == safe_pending(expected['request_id'], expected['relay_receipt'])
        history = [json.loads(row[0]) for row in db.execute('SELECT data FROM inbox_deliveries WHERE entry=? ORDER BY seq', (pending['entry']['id'],))]
        assert history and not any(row['state'] == 'delivered' for row in history)
        feedback = db.execute("SELECT count(*) FROM orchestration_events WHERE type IN ('relay_feedback_intent','relay_feedback_registered') AND json_extract(data,'$.entry_id')=?", (pending['entry']['id'],)).fetchone()[0]
        assert feedback == 0
        errors = []
        for event_type, data in db.execute("SELECT type,data FROM orchestration_events WHERE type IN ('request_result','request_rejected','relay_rejected')"):
            value = json.loads(data); error = value.get('error') or value.get('result', {}).get('error')
            if error: errors.append({'event_type': event_type, 'error_code': code(error)})
    roles = {}
    for role in ['ideation', 'executor']:
        api_root = ROOT / 'roles' / role
        requests = read_rows(api_root / 'requests.ndjson'); responses = read_rows(api_root / 'responses.ndjson')
        roles[role] = {'request_count': len(requests), 'response_count': len(responses),
                       'http_POST_files': len(list((api_root / 'http-exchanges').glob('*.request.bin'))),
                       'requests': [tool_projection(row, role, owner, pending) for row in requests]}
    assert [(roles[role]['request_count'], roles[role]['response_count']) for role in ['ideation', 'executor']] == [(2, 2), (0, 0)]
    uses = [value for row in roles['ideation']['requests'] for value in row['tool_use']]
    results = [value for row in roles['ideation']['requests'] for value in row['tool_result']]
    assert len(uses) == len(results) == 1 and uses[0]['id'] == results[0]['tool_use_id']
    assert (ROOT / 'target/home/received.bin').read_bytes() == (ROOT / 'target-baseline.bin').read_bytes()
    return {'schema': 1, 'status': 'PASS', 'roles': roles, 'errors': errors, 'original_I1_pending_receipt': pending,
            'delivery_states': [row['state'] for row in history], 'feedback_count': feedback, 'target_new_bytes': 0,
            'raw_messages_retained': False, 'headers_metadata_system_auth_retained': False}


def archive_projection(summary, out, archive):
    projection = out / 'projection'; projection.mkdir()
    (projection / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('owned_archive_bytes', BASE / 'cleanup-09b-stage-a-03.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    inventory = helper.archive_and_verify(projection, archive)
    return inventory


def verify_archive(result):
    archive = Path(result['archive']); summary_file = Path(result['summary_file'])
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        assert {item.name for item in members} == {'projection', 'projection/summary.json'}
        assert tar.getmember('projection').isdir() and tar.getmember('projection/summary.json').isfile()
        assert tar.extractfile('projection/summary.json').read() == summary_file.read_bytes()
    return json.loads(summary_file.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); owner = json.loads(args.owner.read_bytes())
    assert Path(owner['root']) == ROOT
    out = args.output.resolve(); out.mkdir(exist_ok=False)
    result = {'status': 'BLOCKED', 'root': str(ROOT), 'scope': 'counts, approved tool_use/tool_result, error codes and original I1 pending receipt only'}
    try:
        summary = collect(owner)
        archive = Path(owner['external_archive'])
        assert Path('/Volumes/WD-Elements').is_mount() and archive.parent.parent.resolve() == archive.parent.parent
        archive.parent.mkdir(exist_ok=False)
        inventory = archive_projection(summary, out, archive)
        result.update(archive=str(archive), archive_bytes=archive.stat().st_size,
                      summary_file=str(out / 'projection/summary.json'), byte_readback='PASS', inventory=inventory)
        assert verify_archive(result) == summary
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result.get(key) for key in ['status', 'archive', 'byte_readback', 'error']}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
