"""Check the persisted launch-policy report against its process exit status."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--exit-code', type=int, required=True)
    parser.add_argument('--stdout', type=Path)
    args = parser.parse_args()
    expected = 'PASS' if args.exit_code == 0 else 'INCOMPLETE'
    errors = []
    report = json.loads(args.report.read_text(encoding='utf-8'))
    observed = {'report': {k: report.get(k) for k in ('status', 'product_status')}}
    if args.stdout:
        summary = json.loads(args.stdout.read_text(encoding='utf-8'))
        observed['stdout'] = {k: summary.get(k) for k in ('status', 'product_status')}
    for source, fields in observed.items():
        for key, actual in fields.items():
            if actual != expected:
                errors.append({'field': source + '.' + key, 'expected': expected, 'actual': actual})
    print(json.dumps({'status': 'PASS' if not errors else 'INCOMPLETE', 'phase_exit_code': args.exit_code,
                      'expected': expected, 'observed': observed, 'errors': errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
