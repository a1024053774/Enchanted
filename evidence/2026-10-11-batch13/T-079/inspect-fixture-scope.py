#!/usr/bin/env python3
"""Compare the approved fixture commit with its parent, without hashes or tests."""
import ast
import json
from pathlib import Path
import subprocess
import sys

before = "8ab5177d09dcb25f57a50ad2166dc0006ea99ce3"
after = "d8446fc982aed0309e7d4892760cbe4e69b694eb"
files = {"acceptance/test_herdr_traceability_e2e.py": {"setUp", "managed_env"},
         "acceptance/test_launcher_shell_ready_e2e.py": {"setUp"}}
report = []
for name, allowed in files.items():
    sources = [subprocess.check_output(["git", "show", revision+":"+name], text=True)
               for revision in (before, after)]
    methods = [{node.name: ast.get_source_segment(source, node)
                for cls in ast.parse(source).body if isinstance(cls, ast.ClassDef)
                for node in cls.body if isinstance(node, ast.FunctionDef)} for source in sources]
    if methods[0].keys() != methods[1].keys():
        raise SystemExit("方法集合被改动；停止")
    changed = [key for key in methods[0] if methods[0][key] != methods[1][key]]
    if not set(changed) <= allowed:
        raise SystemExit("业务方法或批准范围外的方法被改动；停止")
    report.append(dict(path=name, changed_methods=changed,
                       unchanged_methods=[key for key in methods[0] if key not in changed]))
launcher = [subprocess.check_output(["git", "show", revision+":scripts/launch-worker"])
            for revision in (before, after)]
if launcher[0] != launcher[1]:
    raise SystemExit("launcher 在夹具提交中被改动；停止")
target = Path(sys.argv[1])
target.mkdir()
(target / "scope.json").write_text(json.dumps(dict(status="PASS", before=before, after=after,
    launcher_bytes_unchanged=True, files=report), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(target / "adaptation.diff").write_text(subprocess.check_output(
    ["git", "diff", before, after, "--", *files], text=True), encoding="utf-8")
print(target)
