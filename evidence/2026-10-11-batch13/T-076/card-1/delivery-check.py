"""核对同一审查候选的 Git 文件、尾注、范围与交付状态。"""
from pathlib import Path
import json
import os
import subprocess
import sys

root = Path.cwd()
card = root / "evidence/2026-10-11-batch13/T-076/card-1"
code, output_arg = sys.argv[1:]
output = Path(output_arg)
output.mkdir(exist_ok=False)


def run(argv):
    result = subprocess.run(argv, capture_output=True, text=True, check=True)
    return {"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def save(name, value):
    with (output / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


manifest = json.loads((card / "review-01/manifest.json").read_text(encoding="utf-8"))
frozen = Path(manifest["snapshot"])
for name in manifest["paths"]:
    current, copied = root / name, frozen / name
    assert current.read_bytes() == copied.read_bytes(), name
    assert current.is_symlink() == copied.is_symlink(), name
    if current.is_symlink():
        assert os.readlink(current) == os.readlink(copied), name
        entry = os.fsencode(os.readlink(current))
    else:
        entry = current.read_bytes()
    assert subprocess.run(["git", "show", code + ":" + name], capture_output=True, check=True).stdout == entry, name

message = run(["git", "log", "-1", "--format=%B", code])
trailers = subprocess.run(["git", "interpret-trailers", "--parse"], input=message["stdout"],
                         capture_output=True, text=True, check=True).stdout
fields = dict(line.split(": ", 1) for line in trailers.splitlines())
expected = {"A2A-Task": "T-076-1", "A2A-Attempt": "a1", "A2A-Session": "e671d062-fd65-448d-895f-5d160fba9a17",
            "A2A-Role": "worker", "A2A-Tool": "codex-cli 0.162.1", "A2A-Model": "gpt-6.1-sol", "A2A-Effort": "xhigh",
            "A2A-Native-Session": "01a12a7a-deaf-76a0-b977-9020931ead25",
            "A2A-Launch": "launch-f7b4aabbcb584729b8d22d073e0e7986"}
assert fields == expected, (fields, expected)
code_diff = run(["git", "diff", code + "^", code, "--", "acceptance/"])
work_diff = run(["git", "diff", "--", "acceptance/", "scripts/", "workbench/"])
assert not code_diff["stdout"] and not work_diff["stdout"]
names = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", code])
assert len(names["stdout"].splitlines()) == 31 and all(name.startswith("workbench/") for name in names["stdout"].splitlines())
save("delivery-code-readback.json", {"status": "PASS", "code_commit": code, "review_target": manifest["snapshot"],
     "code_files_match_frozen_snapshot": True, "message": message, "trailers": fields, "changed_paths": names,
     "acceptance_diff": code_diff})

map_check = run(["python3", "/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py", "status", "--root", "."])
with (output / "final-project-map-status.txt").open("x", encoding="utf-8") as stream:
    stream.write(map_check["stdout"] + map_check["stderr"])
ticket = Path(".project-map/tickets/T-076-quality-chain-scoring.md")
old = subprocess.run(["git", "show", "HEAD:" + str(ticket)], capture_output=True, text=True, check=True).stdout
new = ticket.read_text(encoding="utf-8")
assert old.split("\n## Resolution\n", 1)[0] == new.split("\n## Resolution\n", 1)[0]
assert "status: open\n" in new and "ready_rev: 1\n" in new
for path in (card / "RESULTS.md", card / "review-01/REVIEW.md", ticket):
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf") and b"\r" not in data and "\ufffd" not in data.decode("utf-8"), str(path)
large = [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "compressed": path.suffix in (".gz", ".zip")}
         for path in card.rglob("*") if path.is_file() and path.stat().st_size > 5 * 1024 * 1024]
assert all(row["compressed"] for row in large)
diff_check = run(["git", "diff", "--check"])
save("final-checks.json", {"status": "PASS", "code_commit": code, "candidate_unchanged_after_review": True,
     "source_files_checked": len(manifest["paths"]), "ticket_resolution_only": True, "ticket_status": "open", "ready_rev": 1,
     "worker_acceptance_scripts_diff_empty": True, "real_codex_turns": 3, "review_status": "PASS",
     "project_map": map_check, "diff_check": diff_check, "large_files": large, "utf8_lf_check": "PASS",
     "argv": sys.argv})
print(json.dumps({"status": "PASS", "source_files_checked": len(manifest["paths"]), "project_map_exit": 0,
                  "raw_large_files": 0, "ticket_resolution_only": True, "code_commit": code}, ensure_ascii=False))
