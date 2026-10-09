import base64
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path("/Users/luckye/Documents/Code/a2a")
ARTIFACTS = Path("/tmp/t060-independent.aDmVvS")
CANDIDATE = "c4ce31d73914fd5afa9eae59b5cb76a1fa5c1331"
PARENT = "8e260461f32e49c3b1bce50bedeceb4fad38aa8a"
NOW = "2026-10-09T12:00:00Z"
commands = []
judgments = {}
scenario_roots = []


def git_source(rev, name):
    path = ARTIFACTS / name
    data = subprocess.run(["git", "show", f"{rev}:scripts/inbox"], cwd=REPO,
                          check=True, capture_output=True).stdout
    path.write_bytes(data)
    path.chmod(0o755)
    return path


def setup_root(name):
    root = ARTIFACTS / name
    root.mkdir()
    for sub in (root / ".project-map/inbox", root / ".project-map/roles", root / ".project-map/tickets"):
        sub.mkdir(parents=True)
    (root / ".project-map/roles/ideation.md").write_text("角色卡 sentinel ideation\n", encoding="utf-8")
    (root / ".project-map/roles/executor.md").write_text("角色卡 sentinel executor\n", encoding="utf-8")
    scenario_roots.append(root)
    return root


def fixture_entry(directory, ident, sender="worker:sentinel", recipient="executor",
                  kind="report", created="2026-10-09T11:00:00Z", reply="", body="外部 nonce fixture\n", **extra):
    values = dict(id=ident, **{"from": sender}, to=recipient, kind=kind,
                  reply_to=reply, refs=[], created_at=created, schema=1, **extra)
    text = "---\n" + "".join(f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
                               for key, value in values.items()) + "---\n\n" + body
    path = directory / (ident + ".md")
    path.write_text(text, encoding="utf-8")
    return path


def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(root))] = base64.b64encode(path.read_bytes()).decode("ascii")
    return result


def run_cli(script, root, args, label):
    argv = [sys.executable, "-B", str(script), "--root", str(root), "--now", NOW, *args]
    p = subprocess.run(argv, cwd=root, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                       text=True, capture_output=True, timeout=15)
    rec = {"label": label, "argv": argv, "cwd": str(root), "exit_code": p.returncode,
           "stdout": p.stdout, "stderr": p.stderr}
    commands.append(rec)
    return p


def output_entries(stdout):
    return [line.split()[1:3] for line in stdout.splitlines() if line.startswith("ENTRY ")]


def terminal_fixture(root):
    inbox = root / ".project-map/inbox"
    fixture_entry(inbox, "terminal-executor-target", sender="executor", recipient="worker:alpha", kind="report", body="target-executor nonce\n")
    fixture_entry(inbox, "terminal-executor-ack", sender="worker:alpha", recipient="executor", kind="ack",
                  reply="terminal-executor-target", body="ack-executor nonce\n")
    fixture_entry(inbox, "terminal-ideation-target", sender="ideation", recipient="worker:alpha", kind="report", body="target-ideation nonce\n")
    fixture_entry(inbox, "terminal-ideation-ack", sender="worker:alpha", recipient="ideation", kind="ack",
                  reply="terminal-ideation-target", body="ack-ideation nonce\n")
    fixture_entry(inbox, "terminal-user-target", sender="user", recipient="worker:alpha", kind="report", body="target-user nonce\n")
    fixture_entry(inbox, "terminal-user-ack", sender="worker:alpha", recipient="user", kind="ack",
                  reply="terminal-user-target", body="ack-user nonce\n")
    fixture_entry(inbox, "live-executor", sender="worker:alpha", recipient="executor", kind="report", body="unseen live nonce\n")


def run_terminal_checks(version, script):
    list_root = setup_root(f"{version}-terminal-list")
    terminal_fixture(list_root)
    list_results = {}
    for role in ("executor", "ideation", "user"):
        p = run_cli(script, list_root, ["list", "--role", role], f"{version}/list/{role}")
        list_results[role] = {"entries": output_entries(p.stdout), "stdout": p.stdout,
                              "stderr": p.stderr, "exit_code": p.returncode}

    ack_root = setup_root(f"{version}-terminal-ack")
    terminal_fixture(ack_root)
    before_ack = snapshot(ack_root)
    p_ack = run_cli(script, ack_root, ["ack", "--role", "executor", "--id", "terminal-executor-ack"],
                    f"{version}/ack-on-ack")
    after_ack = snapshot(ack_root)

    send_root = setup_root(f"{version}-terminal-send")
    terminal_fixture(send_root)
    before_send = snapshot(send_root)
    p_send = run_cli(script, send_root,
                     ["send", "--from", "executor", "--to", "worker:alpha", "--kind", "ack",
                      "--reply-to", "terminal-executor-ack", "--body", "send-ack nonce"],
                     f"{version}/send-kind-ack-on-ack")
    after_send = snapshot(send_root)

    result = {
        "list": list_results,
        "ack_on_ack": {"exit_code": p_ack.returncode, "stdout": p_ack.stdout, "stderr": p_ack.stderr,
                        "unchanged": before_ack == after_ack, "before_files": sorted(before_ack),
                        "after_files": sorted(after_ack)},
        "send_kind_ack_on_ack": {"exit_code": p_send.returncode, "stdout": p_send.stdout,
                                  "stderr": p_send.stderr, "unchanged": before_send == after_send,
                                  "before_files": sorted(before_send), "after_files": sorted(after_send)},
    }
    judgments[version + "/terminal"] = result
    return result


def run_non_ack_checks(version, script):
    root = setup_root(f"{version}-non-ack")
    inbox = root / ".project-map/inbox"
    kinds = ("assign", "revise", "cancel", "stop", "report", "needs-decision",
             "issue", "disposition", "answer")
    fixture_entry(inbox, "other-issue", sender="worker:omega", recipient="executor", kind="issue",
                  title="independent issue nonce", blocking=False, body="issue body nonce\n")
    for kind in kinds:
        ident = "other-" + kind
        extra = {}
        reply = ""
        if kind == "issue":
            # The issue target is also included above as the issue kind.
            continue
        if kind == "disposition":
            extra = {"action": "needs-user"}
            reply = "other-issue"
        elif kind == "answer":
            extra = {"certainty": "relayed", "bundle_id": "independent-answer-bundle"}
            reply = "other-issue"
        fixture_entry(inbox, ident, sender="worker:omega", recipient="executor", kind=kind,
                      reply=reply, body="non-ack " + kind + " nonce\n", **extra)
    before_list = snapshot(root)
    p_list = run_cli(script, root, ["list", "--role", "executor"], f"{version}/non-ack/list-before")
    ids_before = sorted(item[0] for item in output_entries(p_list.stdout))
    ack_results = []
    for ident in ["other-" + kind for kind in kinds if kind != "issue"] + ["other-issue"]:
        p = run_cli(script, root, ["ack", "--role", "executor", "--id", ident],
                    f"{version}/non-ack/ack-{ident}")
        ack_results.append({"id": ident, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    p_after = run_cli(script, root, ["list", "--role", "executor"], f"{version}/non-ack/list-after")
    ids_after = sorted(item[0] for item in output_entries(p_after.stdout))
    final = snapshot(root)
    result = {"expected_kind_ids": sorted(["other-" + kind for kind in kinds]),
              "ids_before": ids_before, "ids_after": ids_after,
              "list_before_exit": p_list.returncode, "list_after_exit": p_after.returncode,
              "ack_results": ack_results, "new_file_count": len(set(final) - set(before_list)),
              "stdout_before": p_list.stdout, "stdout_after": p_after.stdout}
    judgments[version + "/non-ack"] = result
    return result


def run_malformed_check(script):
    root = setup_root("candidate-malformed")
    inbox = root / ".project-map/inbox"
    fixture_entry(inbox, "valid-target", sender="worker:bad-entry", recipient="executor", kind="report",
                  body="valid target nonce\n")
    (inbox / "broken.md").write_text("---\nfrom: broken-only\n", encoding="utf-8")
    before_send = snapshot(root)
    p_send = run_cli(script, root,
                     ["send", "--from", "worker:bad-entry", "--to", "executor", "--kind", "report",
                      "--id", "must-not-write", "--body", "write attempt nonce"],
                     "candidate/malformed/send")
    after_send = snapshot(root)
    before_ack = snapshot(root)
    p_ack = run_cli(script, root, ["ack", "--role", "executor", "--id", "valid-target"],
                    "candidate/malformed/ack")
    after_ack = snapshot(root)
    result = {"send": {"exit_code": p_send.returncode, "stdout": p_send.stdout, "stderr": p_send.stderr,
                        "unchanged": before_send == after_send},
              "ack": {"exit_code": p_ack.returncode, "stdout": p_ack.stdout, "stderr": p_ack.stderr,
                      "unchanged": before_ack == after_ack}}
    judgments["candidate/malformed"] = result
    return result


candidate_script = git_source(CANDIDATE, "candidate-scripts-inbox")
parent_script = git_source(PARENT, "parent-scripts-inbox")
run_terminal_checks("candidate", candidate_script)
run_terminal_checks("parent", parent_script)
run_non_ack_checks("candidate", candidate_script)
run_non_ack_checks("parent", parent_script)
run_malformed_check(candidate_script)
help_root = setup_root("candidate-help")
p_help = run_cli(candidate_script, help_root, ["--help"], "candidate/help")
judgments["candidate/help"] = {"exit_code": p_help.returncode, "stdout": p_help.stdout,
                                "stderr": p_help.stderr,
                                "mentions_frontmatter_list": "front matter" in (p_help.stdout + p_help.stderr),
                                "mentions_corrupt_write": "损坏" in (p_help.stdout + p_help.stderr),
                                "mentions_terminal_ack": "ack 是终结" in (p_help.stdout + p_help.stderr)}

metadata = {"candidate": CANDIDATE, "parent": PARENT, "repo": str(REPO), "now": NOW,
            "python": sys.version, "candidate_source": str(candidate_script),
            "parent_source": str(parent_script), "probe": str(ARTIFACTS / "probe.py"),
            "scenario_roots": [str(root) for root in scenario_roots]}
(ARTIFACTS / "commands.json").write_text(json.dumps(commands, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ARTIFACTS / "judgments.json").write_text(json.dumps(judgments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ARTIFACTS / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Assertions are deliberately independent of acceptance/test_inbox_e2e.py.
c_term = judgments["candidate/terminal"]
p_term = judgments["parent/terminal"]
assert all(c_term["list"][role]["exit_code"] == 0 for role in ("executor", "ideation", "user"))
assert all(all(entry[1] != "ack" for entry in c_term["list"][role]["entries"]) for role in ("executor", "ideation", "user"))
assert c_term["list"]["executor"]["entries"] == [["live-executor", "report"]]
assert c_term["list"]["ideation"]["entries"] == []
assert c_term["ack_on_ack"]["exit_code"] == 1 and c_term["ack_on_ack"]["unchanged"]
assert "ack 是终结" in c_term["ack_on_ack"]["stderr"]
assert c_term["send_kind_ack_on_ack"]["exit_code"] == 1 and c_term["send_kind_ack_on_ack"]["unchanged"]
assert "ack 是终结" in c_term["send_kind_ack_on_ack"]["stderr"]
assert any(entry[1] == "ack" for entry in p_term["list"]["executor"]["entries"])
assert any(entry[1] == "ack" for entry in p_term["list"]["ideation"]["entries"])
assert p_term["ack_on_ack"]["exit_code"] == 0 and not p_term["ack_on_ack"]["unchanged"]
assert p_term["send_kind_ack_on_ack"]["exit_code"] == 0 and not p_term["send_kind_ack_on_ack"]["unchanged"]

for version in ("candidate", "parent"):
    r = judgments[version + "/non-ack"]
    assert r["ids_before"] == r["expected_kind_ids"]
    assert r["ids_after"] == []
    assert all(item["exit_code"] == 0 for item in r["ack_results"])
    assert r["new_file_count"] == 9
mal = judgments["candidate/malformed"]
assert mal["send"]["exit_code"] == 1 and mal["send"]["unchanged"] and "broken.md" in mal["send"]["stderr"]
assert mal["ack"]["exit_code"] == 1 and mal["ack"]["unchanged"] and "broken.md" in mal["ack"]["stderr"]

print(json.dumps({"artifacts": str(ARTIFACTS), "judgments": judgments}, ensure_ascii=False, indent=2))
