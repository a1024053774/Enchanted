"""Replay T-060 counterexamples through the real CLI; retain every run."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, default=ROOT / "scripts/inbox")
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=False)
source = args.candidate.read_text(encoding="utf-8")
guards = {
    "list": '        if item["kind"] == "ack":\n            continue\n',
    "send": '        if target["kind"] == "ack":\n            raise InboxError("ack 是终结，不能再确认：" + target["id"])\n',
    "ack": '    if target["kind"] == "ack":\n        raise InboxError("ack 是终结，不能再确认：" + target["id"])\n',
}
for guard in guards.values():
    assert source.count(guard) == 1, "冻结候选的终结检查不匹配"
results = []
for name, removed in (("old-behavior", ("list", "send", "ack")),
                      ("list-only", ("list",)), ("send-only", ("send",)), ("ack-only", ("ack",))):
    mutant = source
    for key in removed:
        mutant = mutant.replace(guards[key], "", 1)
    script = out / (name + ".py")
    script.write_text(mutant, encoding="utf-8")
    script.chmod(0o755)
    selected = ["InboxCLI.test_ack_is_terminal_in_all_role_lists"] if name == "list-only" else [
        "InboxCLI.test_ack_terminal_rejects_both_write_entry_points"]
    if name == "old-behavior":
        selected.insert(0, "InboxCLI.test_ack_is_terminal_in_all_role_lists")
    artifacts = out / (name + "-run")
    argv = [sys.executable, "-B", str(ROOT / "acceptance/test_inbox_e2e.py"),
            "--artifacts", str(artifacts), *selected]
    p = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, INBOX_SCRIPT=str(script)),
                       text=True, capture_output=True, timeout=60)
    run = json.loads((artifacts / "run.json").read_text(encoding="utf-8"))
    record = dict(name=name, removed=list(removed), script=str(script), argv=argv,
                  env_override={"INBOX_SCRIPT": str(script)}, exit_code=p.returncode,
                  stdout=p.stdout, stderr=p.stderr, run=run,
                  rejected=p.returncode == 1 and run["failures"] > 0 and run["errors"] == 0)
    results.append(record)
    print(json.dumps({k: record[k] for k in ("name", "exit_code", "rejected")}, ensure_ascii=False))
(out / "mutants.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if all(record["rejected"] for record in results) else 1)
