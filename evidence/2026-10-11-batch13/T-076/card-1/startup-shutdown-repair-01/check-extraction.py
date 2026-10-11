"""Compare the unchanged startup prerequisite before/after function extraction."""
import ast
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
source = root.parents[4]
old = ast.parse((root / 'run_t076_real.py.before').read_text(encoding='utf-8'))
new = ast.parse((source / 'workbench/tests/run_t076_real.py').read_text(encoding='utf-8'))
main = next(x for x in old.body if isinstance(x, ast.FunctionDef) and x.name == 'main')
old_loop = next(x for x in ast.walk(main) if isinstance(x, ast.While) and any(
    isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == 'call' and
    v.args and isinstance(v.args[0], ast.Constant) and v.args[0].value == 'pane_process_info' for v in ast.walk(x)))
fn = next(x for x in new.body if isinstance(x, ast.FunctionDef) and x.name == 'release_initial_worker')
new_loop = next(x for x in fn.body if isinstance(x, ast.While))
old_if = next(x for x in old_loop.body if isinstance(x, ast.If) and x.body and isinstance(x.body[0], ast.Break))
new_if = next(x for x in new_loop.body if isinstance(x, ast.If) and x.body and isinstance(x.body[0], ast.Break))
same = ast.dump(old_if.test) == ast.dump(new_if.test)
record = {'status': 'PASS' if same else 'INCOMPLETE', 'startup_predicate_unchanged': same,
          'argv': sys.argv, 'real_codex_turns': 0}
with Path(sys.argv[1]).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(record))
raise SystemExit(0 if same else 1)
