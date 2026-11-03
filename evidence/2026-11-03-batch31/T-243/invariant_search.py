"""T-243 invariant: when a test ends, whatever failed earlier in its cleanup, it still tries to stop the private core
and check the fixture's processes. For every stop_fixture_core call in workbench/tests, list the statements that run
before it on the way down from the outermost enclosing finally and are not inside a try that catches or a
try/finally that still reaches the call. Usage: invariant_search.py (prints one line per call; UNGUARDED lines break it)"""
import ast
from pathlib import Path

TESTS = Path(__file__).resolve().parents[3] / 'workbench/tests'

def calls(node):
    return any(isinstance(n, ast.Call) and getattr(n.func, 'id', getattr(n.func, 'attr', None)) == 'stop_fixture_core' for n in ast.walk(node))

def guarded(stmt):
    # A try whose handlers catch everything reaching here, or whose finally the path continues in.
    return isinstance(stmt, ast.Try) and (stmt.handlers and any(h.type is None or getattr(h.type, 'id', '') in ('Exception', 'BaseException') for h in stmt.handlers))

def walk(body, path, out):
    for index, stmt in enumerate(body):
        if not calls(stmt):
            continue
        before = [s for s in body[:index] if not guarded(s)]
        out.append((path, before))
        if isinstance(stmt, ast.Try):
            if any(calls(s) for s in stmt.finalbody):
                walk(stmt.finalbody, path + ['finally'], out)
            elif any(calls(s) for s in stmt.body):
                walk(stmt.body, path + ['try'], out)
            else:
                for h in stmt.handlers: walk(h.body, path + ['except'], out)
        elif isinstance(stmt, (ast.If, ast.With, ast.For, ast.While, ast.FunctionDef)):
            walk(getattr(stmt, 'body'), path + [type(stmt).__name__], out)
            walk(getattr(stmt, 'orelse', []), path + ['else'], out)

for file in sorted(TESTS.glob('*.py')):
    tree = ast.parse(file.read_text(encoding='utf-8'))
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Try) and any(calls(s) for s in node.finalbody) and not any(calls(s) for s in node.body):
                out = []
                walk(node.finalbody, ['finally'], out)
                bad = [(p, b) for p, b in out if b]
                lines = '; '.join(f"{'/'.join(p)}: " + ', '.join(f'L{s.lineno} {ast.unparse(s).splitlines()[0][:60]}' for s in b) for p, b in bad)
                print(f"{'UNGUARDED' if bad else 'ok':9} {file.name}:{fn.name} finally@L{node.lineno} {lines}")
