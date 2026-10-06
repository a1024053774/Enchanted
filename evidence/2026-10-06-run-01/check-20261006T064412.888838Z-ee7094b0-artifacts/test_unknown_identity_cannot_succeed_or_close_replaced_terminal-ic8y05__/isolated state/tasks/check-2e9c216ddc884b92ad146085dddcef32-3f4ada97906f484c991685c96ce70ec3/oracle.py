CONTROL = '/Users/luckye/Documents/Code/a2a/evidence/2026-10-06-run-01/check-20261006T064412.888838Z-ee7094b0-artifacts/test_unknown_identity_cannot_succeed_or_close_replaced_terminal-ic8y05__/oracle barrier'
ORACLE_SOURCE = '"""Independent subprocess oracle; expected values are literals from the fixture contract."""\nimport json\nfrom pathlib import Path\nimport subprocess\nimport sys\n\nA = {"id": "a", "ts": 2, "value": "alpha"}\nB = {"id": "b", "ts": 2, "value": "beta"}\nC = {"id": "c", "ts": 3, "value": "gamma"}\nD = {"id": "d", "ts": 5, "value": "delta"}\nCASES = [\n    ("unordered-ties", {"items": [D, B, C, A], "limit": 2},\n     {"items": [A, B], "next_cursor": [2, "b"]}),\n    ("continuation", {"items": [B, D, A, C], "limit": 2, "after": [2, "b"]},\n     {"items": [C, D], "next_cursor": None}),\n    ("missing-cursor", {"items": [D, B, C, A], "limit": 1, "after": [2, "az"]},\n     {"items": [B], "next_cursor": [2, "b"]}),\n    ("past-end", {"items": [A, D], "limit": 3, "after": [9, "z"]},\n     {"items": [], "next_cursor": None}),\n    ("empty", {"items": [], "limit": 5}, {"items": [], "next_cursor": None}),\n    ("exact-boundary", {"items": [B, A], "limit": 2},\n     {"items": [A, B], "next_cursor": None}),\n    ("unseen-input", {"items": [{"id": "unique-47", "ts": -7, "extra": [1, 9]}], "limit": 1},\n     {"items": [{"id": "unique-47", "ts": -7, "extra": [1, 9]}], "next_cursor": None}),\n    ("invalid-limit", {"items": [A], "limit": 0}, {"error": "invalid_limit"}),\n    ("maximum-limit", {"items": [B, A], "limit": 100},\n     {"items": [A, B], "next_cursor": None}),\n    ("above-maximum-limit", {"items": [{"id": "boundary-101", "ts": 1}], "limit": 101},\n     {"error": "invalid_limit"}),\n    ("boolean-limit", {"items": [A], "limit": True}, {"error": "invalid_limit"}),\n    ("invalid-cursor", {"items": [A], "limit": 2, "after": [True, "a"]},\n     {"error": "invalid_cursor"}),\n]\ndef main():\n    root = Path(sys.argv[1]).resolve()\n    results = []\n    for name, request, expected in CASES:\n        command = [sys.executable, "-B", str(root / "pager.py")]\n        try:\n            p = subprocess.run(command, input=json.dumps(request), text=True,\n                               capture_output=True, cwd=root, timeout=10)\n        except subprocess.TimeoutExpired as exc:\n            results.append({"case": name, "pass": False, "error": "timeout", "command": command})\n            continue\n        try:\n            actual = json.loads(p.stdout)\n        except json.JSONDecodeError:\n            actual = None\n        results.append({"case": name, "input": request, "expected": expected,\n                        "actual": actual, "exit": p.returncode, "stderr": p.stderr,\n                        "pass": p.returncode == 0 and actual == expected})\n    ok = all(r["pass"] for r in results)\n    print(json.dumps({"status": "PASS" if ok else "FAIL", "candidate": str(root),\n                      "cases": results}, ensure_ascii=False, indent=2))\n    return 0 if ok else 1\nif __name__ == "__main__":\n    sys.exit(main())\n'

import contextlib, io, json, os, pathlib, sys, time, traceback, uuid
control = pathlib.Path(CONTROL)
identity = uuid.uuid4().hex
entry = control / (identity + ".entry.json")
release = control / (identity + ".release")
entry.write_text(json.dumps({"pid": os.getpid(), "ppid": os.getppid(),
    "argv": sys.argv, "candidate_directory": sys.argv[1],
    "release": str(release), "phase": "oracle"}), encoding="utf-8")
deadline = time.monotonic() + 40
while not release.exists() and not (control / "release-all").exists():
    if time.monotonic() > deadline:
        raise RuntimeError("fixture oracle barrier expired")
    time.sleep(0.02)
stdout, stderr = io.StringIO(), io.StringIO()
code = 0
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    try:
        exec(compile(ORACLE_SOURCE, "frozen-independent-pagination-oracle", "exec"))
    except SystemExit as exit:
        code = exit.code
    except Exception:
        traceback.print_exc()
        code = 1
(control / (identity + ".result.json")).write_text(json.dumps({
    "pid": os.getpid(), "argv": sys.argv, "exit_code": code,
    "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}), encoding="utf-8")
try:
    sys.stdout.write(stdout.getvalue())
    sys.stderr.write(stderr.getvalue())
finally:
    (control / (identity + ".done")).write_text("oracle exited", encoding="utf-8")
sys.exit(code)
