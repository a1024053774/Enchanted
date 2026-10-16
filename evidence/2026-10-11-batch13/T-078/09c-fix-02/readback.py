"""Read only the closed #356 rehearsal evidence; never open the deleted root."""
import argparse
import base64
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

SOURCE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from t078_09c_driver import visible_command


def load(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    flow = Path(__file__).resolve().parent.parent / '09c-fix-01/real-chain-outside-01/flow'
    role = flow / 'after-stop-roles/ideation'
    peer = flow / 'after-stop-peer/ideation'
    hook = load(peer / 'hook-02.json')
    assert hook['payload']['hook_event_name'] == 'PermissionRequest' and hook['exit_code'] == 0
    command = hook['payload']['tool_input']['command']
    meta = load(role / 'http-exchanges/0001.meta.json')
    response = (role / 'http-exchanges/0001.response.bin').read_bytes()
    assert meta['status'] == 200 and meta['complete'] is True
    assert len(response) == meta['response_bytes'] == meta['wire_bytes_confirmed']
    sse = [json.loads(line[6:]) for line in response.decode('utf-8').splitlines() if line.startswith('data: ')]
    tool = next(v['content_block'] for v in sse if v['type'] == 'content_block_start')
    tool_input = json.loads(''.join(v['delta']['partial_json'] for v in sse if v['type'] == 'content_block_delta'))
    assert tool['name'] == 'Bash' and tool_input['command'] == command
    actual_tool = load(next(peer.glob('permission-*.json')))['tool_use']
    assert actual_tool == {**tool, 'input': tool_input}
    screens = sorted(flow.glob('C-I1-review-screen-*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
    assert screens and all(p.read_bytes() == screens[0].read_bytes() for p in screens)
    raw = screens[0].read_bytes()
    assert command not in raw.decode('utf-8') and visible_command(raw.decode('utf-8')) == command
    page_count = 0
    for path in flow.glob('command-*.json'):
        record = load(path)
        if 'pane_output' in record['argv']:
            page = json.loads(record['stdout'])
            assert base64.b64decode(page['data_base64']) == raw
            assert page['start_offset'] == 0 and page['next_offset'] == page['total_bytes'] == len(raw)
            page_count += 1
    assert page_count == len(screens)
    with closing(sqlite3.connect((flow / 'sqlite/state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        db.row_factory = sqlite3.Row
        events = [dict(r) for r in db.execute('SELECT * FROM orchestration_events')]
        for event in events:
            event['data'] = json.loads(event['data'])
        waits = [e for e in events if e['type'] == 'permission_wait']
        assert len(waits) == 1 and waits[0]['data'] == hook['payload']
        counts = {name: db.execute('SELECT count(*) FROM ' + name).fetchone()[0]
                  for name in ('inbox_records', 'relay_requests', 'relay_results')}
    assert all(value == 0 for value in counts.values())
    assert not list(peer.glob('permission-key-*')) and not list(peer.glob('tool-execution-*'))
    assert not any(e['type'] == 'window_opened' for e in events)
    hooks = []
    for path in sorted((role / 'hooks').iterdir()):
        stdin = load(path / 'stdin.bin')
        finished = load(path / 'finished.json')
        assert finished['exit_code'] == 0 and (path / 'stderr.bin').read_bytes() == b''
        hooks.append({'trace': path.name, 'event': stdin['hook_event_name'], 'finished': finished})
    result = {'status': 'PASS', 'scope': 'closed #356 evidence diagnosis; not a successful full rehearsal',
              'source_result': str(flow.parent / 'result.json'), 'HTTP': meta, 'SSE_events': len(sse),
              'tool_use': actual_tool, 'permission_event': waits[0], 'hooks': hooks,
              'screens': len(screens), 'screen_bytes': len(raw), 'complete_pane_output_reads': page_count,
              'raw_continuous_command_match': False, 'native_command_box_match': True,
              'window_opened': 0, 'permission_key_files': 0, 'business_records': counts,
              'root_cause': '09B raw command substring waiter was inherited by the wrapped 09C command box',
              'SQLite_reads': 'closed pre-stop consistent backup only; immutable diagnostic read',
              'sidecar_note': 'WAL/SHM were already present in the saved output; earlier ordinary read-only diagnosis may update SHM lock metadata. No result, screen, HTTP/hook or primary database was rewritten.'}
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'HTTP': meta['status'], 'screens': len(screens),
                      'permission_seq': waits[0]['seq'], 'window_opened': 0, 'key_writes': 0}))


if __name__ == '__main__':
    main()
