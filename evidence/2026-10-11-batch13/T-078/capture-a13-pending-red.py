"""Read only the owner-bound A-13 missing-role receipt and its feedback event."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-0fe6fcpf')
LAUNCH = '35db30f3-807c-418e-92c5-ba2cc73c8e42'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'output_exists'
    readiness_file = BASE / '09b-a13-stage-a-01/readiness.json'
    input_file = BASE / '09b-a13-i1-materials-01/b1-input.json'
    cli = SOURCE / 'workbench/src/gates/cli.ts'
    for path in [readiness_file, input_file, cli, ROOT / 'operator.json']:
        assert path.is_file(), ('missing_path', str(path))
    ready = json.loads(readiness_file.read_bytes())
    inp = json.loads(input_file.read_bytes())
    assert ready['root'] == str(ROOT) == inp['root'] and inp['launch'] == LAUNCH
    env = {key: value for key, value in os.environ.items() if not key.startswith('A2A_')}
    env['A2A_OPERATOR_CREDENTIAL'] = str(ROOT / 'operator.json')
    command = [shutil.which('node'), str(cli), '--state', str(ROOT / 'state'), 'orchestration_events']
    response = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True, text=True, timeout=10, check=True)
    payload = json.loads(response.stdout)
    assert payload.get('ok') is True
    rejected = [e for e in payload['events'] if e['seq'] == 116 and e['launch'] == LAUNCH and e['type'] == 'relay_rejected']
    feedback = [e for e in payload['events'] if e['seq'] == 117 and e['launch'] == LAUNCH and e['type'] == 'dispatch_queued']
    assert len(rejected) == len(feedback) == 1
    receipt = rejected[0]['data']['result']
    assert receipt['ok'] is False and receipt['error'] == 'wake_undelivered'
    assert receipt['delivery']['state'] == 'undelivered' and receipt['delivery']['reason'] == 'role_session_missing'
    assert receipt['entry']['from'] == 'ideation' and receipt['entry']['to'] == 'executor'
    assert feedback[0]['data']['source'] == 'gate' and rejected[0]['data']['request_id'] in feedback[0]['data']['text']
    counts = {}
    for name in ['requests.ndjson', 'responses.ndjson']:
        path = ROOT / 'roles/ideation' / name
        counts[name] = sum(bool(line) for line in path.read_text(encoding='utf-8').splitlines()) if path.exists() else 0
    result = {
        'status': 'PASS', 'product_contract': 'INCOMPLETE', 'kind': 'new-contract red state',
        'source_revision': ready['source_revision'],
        'observer_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
        'root': str(ROOT), 'launch': LAUNCH, 'task': ready['task'], 'target_binding': ready['target_binding'],
        'observed': {'entry_saved': True, 'delivery': 'undelivered', 'reason': 'role_session_missing',
                     'relay_error': 'wake_undelivered', 'feedback_dispatch': feedback[0]['data']['id']},
        'events': rejected + feedback, 'api_counts_at_readback': counts,
        'readback_command': command, 'exit_code': response.returncode,
        'raw_logs_copied': False, 'credentials_copied': False,
        'scope': 'read-only gate events 116/117 and counts; no dispatch, key, Stop signal, or process start',
    }
    out.mkdir()
    (out / 'readback.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'product_contract': 'INCOMPLETE', 'events': [116, 117], 'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
