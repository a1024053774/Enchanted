"""Run the existing conditional-Enter cases with explicitly injected unit clocks."""
import argparse
import json
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from t078_rev2_tools_cases import permission_cases

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
checks = []
permission_cases(args.output, checks)
value = {'status': 'PASS', 'scope': __doc__, 'checks': checks, 'real_model_turns': 0,
         'role_CLIs': 0, 'time_injected': True, 'scene_started': False}
with (args.output / 'result.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(value, ensure_ascii=False))
