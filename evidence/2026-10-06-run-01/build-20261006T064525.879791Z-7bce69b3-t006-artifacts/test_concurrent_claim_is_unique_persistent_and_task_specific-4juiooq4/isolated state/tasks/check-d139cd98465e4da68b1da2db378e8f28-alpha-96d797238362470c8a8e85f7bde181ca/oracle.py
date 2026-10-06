"""Independent subprocess oracle; expected values are literals from the fixture contract."""
import json
from pathlib import Path
import subprocess
import sys

A = {"id": "a", "ts": 2, "value": "alpha"}
B = {"id": "b", "ts": 2, "value": "beta"}
C = {"id": "c", "ts": 3, "value": "gamma"}
D = {"id": "d", "ts": 5, "value": "delta"}
CASES = [
    ("unordered-ties", {"items": [D, B, C, A], "limit": 2},
     {"items": [A, B], "next_cursor": [2, "b"]}),
    ("continuation", {"items": [B, D, A, C], "limit": 2, "after": [2, "b"]},
     {"items": [C, D], "next_cursor": None}),
    ("missing-cursor", {"items": [D, B, C, A], "limit": 1, "after": [2, "az"]},
     {"items": [B], "next_cursor": [2, "b"]}),
    ("past-end", {"items": [A, D], "limit": 3, "after": [9, "z"]},
     {"items": [], "next_cursor": None}),
    ("empty", {"items": [], "limit": 5}, {"items": [], "next_cursor": None}),
    ("exact-boundary", {"items": [B, A], "limit": 2},
     {"items": [A, B], "next_cursor": None}),
    ("unseen-input", {"items": [{"id": "unique-47", "ts": -7, "extra": [1, 9]}], "limit": 1},
     {"items": [{"id": "unique-47", "ts": -7, "extra": [1, 9]}], "next_cursor": None}),
    ("invalid-limit", {"items": [A], "limit": 0}, {"error": "invalid_limit"}),
    ("maximum-limit", {"items": [B, A], "limit": 100},
     {"items": [A, B], "next_cursor": None}),
    ("above-maximum-limit", {"items": [{"id": "boundary-101", "ts": 1}], "limit": 101},
     {"error": "invalid_limit"}),
    ("boolean-limit", {"items": [A], "limit": True}, {"error": "invalid_limit"}),
    ("invalid-cursor", {"items": [A], "limit": 2, "after": [True, "a"]},
     {"error": "invalid_cursor"}),
]
def main():
    root = Path(sys.argv[1]).resolve()
    results = []
    for name, request, expected in CASES:
        command = [sys.executable, "-B", str(root / "pager.py")]
        try:
            p = subprocess.run(command, input=json.dumps(request), text=True,
                               capture_output=True, cwd=root, timeout=10)
        except subprocess.TimeoutExpired as exc:
            results.append({"case": name, "pass": False, "error": "timeout", "command": command})
            continue
        try:
            actual = json.loads(p.stdout)
        except json.JSONDecodeError:
            actual = None
        results.append({"case": name, "input": request, "expected": expected,
                        "actual": actual, "exit": p.returncode, "stderr": p.stderr,
                        "pass": p.returncode == 0 and actual == expected})
    ok = all(r["pass"] for r in results)
    print(json.dumps({"status": "PASS" if ok else "FAIL", "candidate": str(root),
                      "cases": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1
if __name__ == "__main__":
    sys.exit(main())
