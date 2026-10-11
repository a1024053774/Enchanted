"""Replay only the actual runner's final print with the preserved coop receipt."""
import ast
import contextlib
import io
import json
from pathlib import Path
import sys
import traceback

source, receipt, output = map(Path, sys.argv[1:])
tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_probe")
statement = function.body[-2]
assert isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
assert isinstance(statement.value.func, ast.Name) and statement.value.func.id == "print"
record = json.loads(receipt.read_text(encoding="utf-8"))
assert (record["tests_run"], record["failures"], record["errors"], record["skipped"]) == (8, 0, 0, 0)
stdout = io.StringIO()
result = {"source": str(source), "receipt": str(receipt), "argv": sys.argv, "real_codex_turns": 0}
try:
    with contextlib.redirect_stdout(stdout):
        exec(compile(ast.Module(body=[statement], type_ignores=[]), str(source), "exec"),
             {"json": json, "record": record})
    summary = json.loads(stdout.getvalue())
    assert summary["runner"] == "daemon-acceptance"
    assert (summary["status"], summary["tests_run"], summary["failures"], summary["errors"], summary["exit_code"]) == ("PASS", 8, 0, 0, 0)
    result.update(status="PASS", summary=summary, exit=0)
except (KeyError, AssertionError, ValueError) as error:
    result.update(status="INCOMPLETE", error=repr(error), traceback=traceback.format_exc(), exit=1)
result["stdout"] = stdout.getvalue()
with output.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({key: result.get(key) for key in ("status", "exit", "error")}, ensure_ascii=False))
raise SystemExit(result["exit"])
