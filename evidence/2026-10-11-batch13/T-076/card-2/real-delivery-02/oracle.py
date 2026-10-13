"""Independent literal oracle for the owned fixture. It writes no files."""
import json
from pathlib import Path
import runpy
import sys

fn = runpy.run_path(str(Path(sys.argv[1]) / 'src/clamp.py'))['clamp']
cases = [('negative', -100, 0), ('zero', 0, 0), ('interior', 73, 73), ('upper', 100, 100), ('overflow', 1000, 100)]
invalid = [('bool-true', True), ('bool-false', False), ('float', 1.5), ('string', '1'), ('none', None), ('list', [])]
for case, value, expected in cases:
    actual = fn(value)
    if type(actual) is not int or actual != expected:
        print(json.dumps({'schema': 1, 'failed_case': case, 'expected': expected, 'actual': actual})); raise SystemExit(1)
for case, value in invalid:
    try: fn(value)
    except ValueError as error:
        if str(error) != 'not_int':
            print(json.dumps({'schema': 1, 'failed_case': case, 'error': str(error)})); raise SystemExit(1)
    else:
        print(json.dumps({'schema': 1, 'failed_case': case, 'error': 'invalid type accepted'})); raise SystemExit(1)
print(json.dumps({'schema': 1, 'passed_cases': len(cases) + len(invalid)}))
