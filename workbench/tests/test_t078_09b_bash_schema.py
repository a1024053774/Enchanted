"""Offline check against Claude Code 2.1.296's recorded Bash tool schema."""
import argparse
import json
from pathlib import Path


def run(scene, mutant=None):
    rows = [json.loads(line) for line in scene.read_text(encoding='utf-8').splitlines() if line]
    request = json.loads(rows[0]['body_raw'])
    bash = next(tool for tool in request['tools'] if tool.get('name') == 'Bash')
    properties = bash['input_schema']['properties']
    command_only = 'command' in properties and 'argv' not in properties
    if mutant == 'argv':
        return {'status': 'PASS' if command_only else 'INCOMPLETE', 'mutant': mutant,
                'decision': '409' if command_only else '200', 'reason': 'recorded Claude schema rejects argv-only input',
                'schema_properties': sorted(properties)}
    if mutant == 'missing-command':
        return {'status': 'PASS' if command_only else 'INCOMPLETE', 'mutant': mutant,
                'decision': '409' if command_only else '200', 'reason': 'command is required by recorded schema',
                'schema_properties': sorted(properties)}
    return {'status': 'PASS' if command_only else 'INCOMPLETE', 'scene_request': str(scene),
            'schema_properties': sorted(properties), 'tool_name': bash['name'],
            'accepted_input': {'command': 'node /path/inbox send --from executor'},
            'rejected_input': {'argv': ['node', '/path/inbox', 'send']},
            'scope': 'offline fixture schema readback; no process/API/CLI'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--scene', type=Path, required=True); parser.add_argument('--output', type=Path, required=True); parser.add_argument('--mutant', choices=['argv', 'missing-command'])
    args = parser.parse_args(); args.output.mkdir(parents=False, exist_ok=False); result = run(args.scene, args.mutant)
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'mutant': args.mutant, 'properties': result.get('schema_properties')}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
