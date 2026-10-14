"""静态路径检查；不创建夹具、home、daemon 或真实回合。"""
import argparse
import json
from pathlib import Path

from capability_command_paths import check_command_paths

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = json.loads((BASE / 'capability-prepared-01/fixture.json').read_text(encoding='utf-8'))
    try:
        result = check_command_paths(
            json.loads((args.review / 'launch-policy.first-turn.pending.json').read_text(encoding='utf-8')),
            (args.review / 'ROLE-BODY.md').read_text(encoding='utf-8'),
            (args.review / 'FIRST-TURN.template.md').read_text(encoding='utf-8'),
            run_root=args.run_root, task=args.task, g=fixture['G'], target=fixture['T'])
    except ValueError as error:
        result = {'status': 'NO_GO', 'error': error.args[0]}
    result.update(real_codex_turns=0, fixture_or_home_written=False,
                  argv=__import__('sys').argv)
    (args.output / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
