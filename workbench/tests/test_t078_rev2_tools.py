"""Contract entry for rev2 tools; deterministic files and input/lifecycle spies."""
import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'kind': 'new-contract', 'model_turns': 0,
              'real_role_CLIs': 0, 'checks': []}
    try:
        paths = [Path(__file__).parent / name for name in
                 ['t078_raw_retention.py', 't078_09c_driver.py']]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            record.update(error='requested_tools_not_implemented', missing=missing)
        else:
            suite = importlib.import_module('t078_rev2_tools_cases')
            suite.run(args.output, record['checks'])
            record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
