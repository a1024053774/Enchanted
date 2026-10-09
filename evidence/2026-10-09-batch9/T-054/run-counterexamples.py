"""Create isolated known-bad CLI candidates; never mutate production scripts."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def main():
    work = BASE / "counterexamples-01-artifacts"
    work.mkdir(exist_ok=False)
    summaries = []
    cases = (
        ("missing-marker", "dispatch", 'sent = f"⟦主控 #{sequence}⟧\\n" + text',
         'sent = text', "Contract.test_dispatch_multiline_roles_and_append"),
        ("overwrite-log", "record_io.py", "os.O_WRONLY | os.O_APPEND | os.O_CREAT",
         "os.O_WRONLY | os.O_TRUNC | os.O_CREAT", "Contract.test_dispatch_multiline_roles_and_append"),
        ("overlap-copy", "session-copy", 'start = previous[-1]["end_byte"] if previous else 0',
         'start = max(0, previous[-1]["end_byte"] - 1) if previous else 0',
         "Contract.test_copy_incremental_cross_batch_and_git"),
    )
    for name, target, before, after, test in cases:
        candidate = work / name
        candidate.mkdir()
        for script in ("dispatch", "session-copy", "record_io.py"):
            (candidate / script).write_bytes((ROOT / "scripts" / script).read_bytes())
        path = candidate / target
        text = path.read_text(encoding="utf-8")
        if text.count(before) != 1:
            raise RuntimeError("Mutation anchor changed: " + name)
        path.write_text(text.replace(before, after, 1), encoding="utf-8")
        argv = [sys.executable, "-B", str(ROOT / "acceptance/test_dispatch_session_e2e.py"),
                "--artifacts", str(candidate / "run-artifacts"), test]
        env = dict(os.environ, DISPATCH_SCRIPT=str(candidate / "dispatch"),
                   SESSION_COPY_SCRIPT=str(candidate / "session-copy"))
        p = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)
        (BASE / (name + "-01.log")).write_text(p.stdout+p.stderr, encoding="utf-8")
        summaries.append(dict(name=name, mutation_file=target, before=before, after=after,
                              argv=argv, selectors={key:env[key] for key in ("DISPATCH_SCRIPT", "SESSION_COPY_SCRIPT")},
                              exit_code=p.returncode))
        if p.returncode != 1 or "FAIL" not in p.stderr or "Traceback" not in p.stderr:
            raise RuntimeError("Counterexample was not rejected by assertion: " + name)
    # New file-input / Claude and copy-concurrency cases also reject absent
    # parent entry points, without touching the current implementations.
    argv = [sys.executable, "-B", str(ROOT / "acceptance/test_dispatch_session_e2e.py"),
            "--artifacts", str(work / "missing-parent-artifacts"),
            "Contract.test_body_file_preserves_crlf_and_claude_bytes",
            "Contract.test_copy_concurrent_requests_do_not_duplicate_range"]
    env = dict(os.environ, DISPATCH_SCRIPT=str(work / "absent-dispatch"), SESSION_COPY_SCRIPT=str(work / "absent-copy"))
    p = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)
    (BASE / "red-added-01.log").write_text(p.stdout+p.stderr, encoding="utf-8")
    summaries.append(dict(name="missing-parent-added-cases", argv=argv,
                          selectors={key:env[key] for key in ("DISPATCH_SCRIPT", "SESSION_COPY_SCRIPT")},
                          exit_code=p.returncode))
    if p.returncode != 1 or p.stderr.count("EXPECTED_RED") < 2:
        raise RuntimeError("Added cases did not reject missing parent entry points")
    (BASE / "counterexamples-01.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("PASS: three specified mutants and added-case parent counterfactual rejected")


if __name__ == "__main__":
    main()
