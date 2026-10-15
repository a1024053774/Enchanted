"""Read-only Stage-A-04 pane/daemon/launch diagnosis; never writes pane input."""
import base64
import json
import os
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
SCENE = BASE / '09b-stage-a-04/result.json'


def main():
    output = BASE / '09b-stage-a-04-readback-01'
    output.mkdir(exist_ok=False)
    scene = json.loads(SCENE.read_bytes())
    root = Path(scene['root'])
    attempt = scene['attempt']
    launch = attempt['runtime_identity']['launch']
    thread = attempt['thread_id']
    task = attempt['task_id']
    state = root / 'state'
    node = '/opt/homebrew/bin/node'
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CLAUDE_', 'CODEX_'))}
    commands = [
        ('daemon-status', ['daemon_status']),
        ('launch-show', ['launch_show', '--launch', launch]),
        ('pane-status', ['pane_status', '--thread', thread]),
        ('pane-process-info', ['pane_process_info', '--thread', thread]),
        ('pane-output', ['pane_output', '--launch', launch, '--offset', '0', '--max-bytes', '20000']),
        ('orchestration-events', ['orchestration_events', '--task', task]),
    ]
    rows = []
    for name, args in commands:
        argv = [node, str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', str(state), *args]
        result = subprocess.run(argv, cwd=SOURCE, env=clean_env, capture_output=True)
        (output / f'{name}.stdout.bin').write_bytes(result.stdout)
        (output / f'{name}.stderr.bin').write_bytes(result.stderr)
        rows.append({'name': name, 'argv': argv, 'exit_code': result.returncode})
    pane = json.loads((output / 'pane-output.stdout.bin').read_bytes())
    pane_text = base64.b64decode(pane['data_base64']).decode('utf-8', errors='replace')
    (output / 'pane-output.txt').write_text(pane_text, encoding='utf-8')
    launch_show = json.loads((output / 'launch-show.stdout.bin').read_bytes())['launch']
    pane_info = json.loads((output / 'pane-process-info.stdout.bin').read_bytes())
    pane_status = json.loads((output / 'pane-status.stdout.bin').read_bytes())
    events = json.loads((output / 'orchestration-events.stdout.bin').read_bytes())['events']
    launch_config = json.loads((root / 'target/launch-config.json').read_bytes())
    (output / 'launch-config.json').write_bytes((root / 'target/launch-config.json').read_bytes())
    only_zsh = len(pane_info.get('processes', [])) == 1 and pane_info['processes'][0]['command'] == '/bin/zsh'
    result = {
        'status': 'PASS' if all(row['exit_code'] == 0 for row in rows) and pane_info.get('leader') is None and only_zsh and 'create sessions: File exists' in pane_text and launch_show['argv'][0] == launch_config['codex_bin'] else 'INCOMPLETE',
        'scope': 'Read-only gate CLI pane/daemon/launch inspection; no pane input, signal, daemon stop, or process mutation',
        'root': str(root), 'task': task, 'attempt': attempt, 'commands': rows,
        'pane_text_contains_create_sessions_file_exists': 'create sessions: File exists' in pane_text,
        'pane_processes_only_zsh': only_zsh,
        'leader': pane_info.get('leader'), 'pane_state': pane_status.get('state'),
        'pane_lifecycle': pane_status.get('lifecycle'), 'queued': pane_status.get('queued'),
        'launch_codex_bin': launch_config.get('codex_bin'), 'launch_argv_first': launch_show.get('argv', [None])[0],
        'launch_shell_argv': launch_show.get('shell_argv'),
        'event_types': [event.get('type') for event in events],
        'receiver_path_exists': Path(launch_config['codex_bin']).is_file(),
        'receiver_started_observed': any(launch_config['codex_bin'] in str(p) for p in pane_info.get('processes', [])),
    }
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'output': str(output), 'leader': result['leader'], 'event_types': result['event_types']}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
