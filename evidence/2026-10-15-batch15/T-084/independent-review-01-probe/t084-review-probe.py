#!/usr/bin/env python3
"""Independent T-084 probes. Writes only under /tmp. Does not modify the repo."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path("/Users/luckye/Documents/Code/a2a-wt-t084")
OUT = Path("/tmp/t084-review-probe")
SPEC = importlib.util.spec_from_file_location(
    "t084", ROOT / "workbench/tests/test_t084_trailer_record.py")
t084 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t084)

sys.path.insert(0, str(ROOT / "workbench/tests"))
from legacy_quality_driver import QualityDriver  # noqa: E402


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def trailer_facts(events, oid):
    checks = [e for e in events if e["type"] == "trailer_check" and e["details"].get("commit") == oid]
    interventions = [e for e in events if e["type"] == "human_intervention"]
    return {
        "trailer_passed": [e["details"].get("passed") for e in checks],
        "trailer_error": [e["details"].get("error") for e in checks],
        "trailer_launch": [e["details"].get("trailers", {}).get("launch") for e in checks],
        "trailer_model": [e["details"].get("trailers", {}).get("model") for e in checks],
        "trailer_effort": [e["details"].get("trailers", {}).get("effort") for e in checks],
        "interventions": len(interventions),
    }


def setup(name, host):
    env = t084.git_env()
    artifact = Path(tempfile.mkdtemp(prefix="t084r-", dir="/tmp"))
    state = artifact / "s"
    state.mkdir()
    boundary = artifact / "worker"
    boundary.mkdir()
    (boundary / "store.json").write_text(json.dumps({
        "threads": {}, "next": 0, "scenario": "done-no-submit", "prompts": [], "closes": [], "archived": {},
    }) + "\n", encoding="utf-8")
    review = t084.prepare_review_control(artifact, count=4) if False else None
    from legacy_quality_driver import prepare_review_control
    review = prepare_review_control(artifact, count=4)
    logs = OUT / (name + "-daemon")
    if logs.exists():
        shutil.rmtree(logs)
    logs.mkdir(parents=True)
    t084.HOST = host
    host_proc, stdout, stderr, argv = t084.start_daemon(
        state, boundary, review, ROOT / "workbench/src/gates/core.ts", env, logs)
    gate = t084.Gate(state, env, [])
    return {
        "env": env, "artifact": artifact, "state": state, "boundary": boundary,
        "review": review, "host": host_proc, "stdout": stdout, "stderr": stderr,
        "argv": argv, "gate": gate, "logs": logs,
    }


def stop(ctx):
    t084.stop_daemon(ctx["host"], ctx["state"], ctx["env"], ctx["stdout"], ctx["stderr"])


def card_for(task):
    return {
        "id": task, "source": None, "goal": "把 src/value.txt 写成 worker",
        "non_goals": ["不改验收文件"], "paths": {"allow": ["src/"], "deny": ["src/private/"]},
        "oracle_paths": ["acceptance/criterion.py"],
        "completion_conditions": [{"argv": [sys.executable, "-I", "-B", "-c",
            "from pathlib import Path; import runpy; runpy.run_path('acceptance/criterion.py')"]}],
        "red_commands": [], "task_type": "后端逻辑", "repair_target": None, "complexity": "S",
        "executor": {"cli": "Codex", "model": t084.MODEL, "effort": t084.EFFORT},
        "base_commit": None, "writer": None,
    }


def open_task(ctx, task, command):
    repo, _git = t084.init_repo(ctx["artifact"] / task, ctx["env"])
    case = OUT / task
    case.mkdir(parents=True, exist_ok=True)
    card_file = case / "card.json"
    card_file.write_text(json.dumps(card_for(task), ensure_ascii=False), encoding="utf-8")
    ctx["gate"](task, "card_save", "--card", card_file, "--expected-version", "0")
    ctx["gate"](task, "create", "--repo", repo, "--branch", "refs/heads/main", "--card-version", "1", "--project", "fixture")
    if command == "claim":
        attempt = ctx["gate"](task, "claim", "--owner", "independent-review")["attempt"]
        record = None
    else:
        attempt = ctx["gate"](task, "dispatch", "--runtime-mode", "approval-required")["attempt"]
        rows = [json.loads(line) for line in (ctx["boundary"] / "worker-creations.jsonl").read_text(encoding="utf-8").splitlines()]
        record = next(row for row in rows if row["attempt"] == attempt["attempt_id"])
    return repo, attempt, record


def commit_with(ctx, repo, attempt, values):
    return t084.commit_candidate(repo, ctx["env"], attempt, values)


def nine(attempt, **overrides):
    values = {
        "Task": attempt["task_id"], "Attempt": attempt["attempt_id"],
        "Session": attempt["session_id"], "Role": "worker",
        "Tool": "not-the-recorded-cli", "Model": "not-the-recorded-model",
        "Effort": "not-the-recorded-effort",
        "Native-Session": "native-turn:" + (attempt["thread_id"] or "no-thread"),
        "Launch": "not-this-attempt-launch",
    }
    values.update(overrides)
    return values


def snapshot(ctx, task, oid, repo, base):
    verified = ctx["gate"](task, "verify")
    status = ctx["gate"](task, "status")
    events = ctx["gate"](task, "events")["events"]
    attempt = status["task"]["current_attempt"]
    delivery = attempt.get("delivery")
    main = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], env=ctx["env"],
                          check=True, capture_output=True, text=True).stdout.strip()
    return {
        "verify_ok": verified.get("ok"), "verify_error": verified.get("error"),
        "task_state": status["task"]["state"],
        "thread_id": attempt.get("thread_id"),
        "delivery_present": delivery is not None,
        "delivery": None if not delivery else {
            "launch_id": delivery.get("launch_id"), "cli": delivery.get("cli"),
            "model": delivery.get("model"), "effort": delivery.get("effort"),
        },
        "main_unchanged": main == base, "main": main,
        **trailer_facts(events, oid),
    }


def claim_probe(ctx):
    task = "t084-claim-forged"
    repo, attempt, _record = open_task(ctx, task, "claim")
    oid, _body, base = commit_with(ctx, repo, attempt, nine(attempt))
    submitted = ctx["gate"](task, "submit", "--attempt", attempt["attempt_id"], "--session", attempt["session_id"],
                            "--fence", attempt["fence"], "--spec-rev", attempt["spec_rev"], "--commit", oid)
    fact = snapshot(ctx, task, oid, repo, base)
    fact["submit_ok"] = submitted.get("ok")
    fact["submit_error"] = submitted.get("error")
    integrate = {"attempted": False}
    if fact["verify_ok"] and fact["task_state"] == "reviewing":
        driver = QualityDriver(ROOT / "workbench/src/gates/cli.ts", ctx["state"], ctx["review"], ctx["env"])
        try:
            driver.complete_review(task, attempt, oid)
            score = driver.score_file(attempt)
            integrated = ctx["gate"](task, "integrate", "--attempt", attempt["attempt_id"], "--score-file", score)
            after = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], env=ctx["env"],
                                   check=True, capture_output=True, text=True).stdout.strip()
            status = ctx["gate"](task, "status")
            integrate = {
                "attempted": True, "review_completed": True,
                "integrate_ok": integrated.get("ok"), "integrate_error": integrated.get("error"),
                "task_state": status["task"]["state"], "main_after": after, "main_moved": after != base,
            }
        except Exception as error:  # probe must keep the gate error, not hide it
            integrate = {"attempted": True, "review_completed": False, "exception": str(error)}
            try:
                score = ctx["review"] / "unused-score.json"
                score.write_text(json.dumps({
                    "result": "通过", "boundary_discipline": 3, "boundary_reason": "受控测试在合同边界内",
                    "engineering_taste": 2, "engineering_reason": "独立夹具固定评分", "notes": "",
                }, ensure_ascii=False), encoding="utf-8")
                integrated = ctx["gate"](task, "integrate", "--attempt", attempt["attempt_id"], "--score-file", score)
                integrate["integrate_without_review_ok"] = integrated.get("ok")
                integrate["integrate_without_review_error"] = integrated.get("error")
            except Exception as second:
                integrate["integrate_without_review_exception"] = str(second)
    fact["integrate"] = integrate
    return fact


def effort_unknown_probe(ctx):
    task = "t084-effort-unknown"
    repo, attempt, record = open_task(ctx, task, "dispatch")
    values = nine(attempt, Tool=record["cli_version"], Model=record["model"], Effort="unknown", Launch=record["id"])
    oid, _body, base = commit_with(ctx, repo, attempt, values)
    submitted = ctx["gate"](task, "submit", "--attempt", attempt["attempt_id"], "--session", attempt["session_id"],
                            "--fence", attempt["fence"], "--spec-rev", attempt["spec_rev"], "--commit", oid)
    fact = snapshot(ctx, task, oid, repo, base)
    fact["submit_ok"] = submitted.get("ok")
    fact["record_effort"] = record["effort"]
    fact["record_model"] = record["model"]
    fact["card_model"] = t084.MODEL
    return fact


def divergence_probe(ctx):
    results = []
    for name, model in (("card-model", t084.MODEL), ("record-model", "observed-not-card")):
        task = "t084-div-" + name
        repo, attempt, record = open_task(ctx, task, "dispatch")
        values = nine(attempt, Tool=record["cli_version"], Model=model, Effort=record["effort"], Launch=record["id"])
        oid, _body, base = commit_with(ctx, repo, attempt, values)
        submitted = ctx["gate"](task, "submit", "--attempt", attempt["attempt_id"], "--session", attempt["session_id"],
                                "--fence", attempt["fence"], "--spec-rev", attempt["spec_rev"], "--commit", oid)
        fact = snapshot(ctx, task, oid, repo, base)
        fact.update({
            "name": name, "submit_ok": submitted.get("ok"), "submit_error": submitted.get("error"),
            "trailer_model_sent": model, "record_model": record["model"], "card_model": t084.MODEL,
            "record_cli": record["cli_version"],
        })
        results.append(fact)
    return results


def make_host(directory):
    tests = directory / "workbench/tests"
    tests.mkdir(parents=True)
    src = Path(ROOT / "workbench/tests/daemon_acceptance_host.ts").read_text(encoding="utf-8")
    old = 'cli_version: "controlled-runtime fixture", model: task.card.executor.model, effort: task.card.executor.effort,'
    new = 'cli_version: "controlled-runtime fixture", model: "observed-not-card", effort: task.card.executor.effort,'
    if src.count(old) != 1:
        raise RuntimeError("host model line is not unique")
    (tests / "daemon_acceptance_host.ts").write_text(src.replace(old, new, 1), encoding="utf-8")
    for name in ("controlled_quality_pty.ts", "legacy_review_runtime.ts"):
        os.symlink(ROOT / "workbench/tests" / name, tests / name)
    os.symlink(ROOT / "workbench/src", directory / "workbench/src")
    os.symlink(ROOT / "workbench/node_modules", directory / "workbench/node_modules")
    os.symlink(ROOT / "acceptance", directory / "acceptance")
    return tests / "daemon_acceptance_host.ts"


def effort_exemption_core(directory):
    text = (ROOT / "workbench/src/gates/core.ts").read_text(encoding="utf-8")
    old = 'else if (attempt.delivery && trailers.effort![0] !== attempt.delivery.effort) error = "trailer_identity_mismatch";\n'
    new = 'else if (attempt.delivery && trailers.effort![0] !== "unknown" && trailers.effort![0] !== attempt.delivery.effort) error = "trailer_identity_mismatch";\n'
    if text.count(old) != 1:
        raise RuntimeError("effort comparison is not unique")
    src = directory / "src"
    shutil.copytree(ROOT / "workbench/src", src, symlinks=True)
    target = src / "gates/core.ts"
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    (directory / "node_modules").symlink_to(ROOT / "workbench/node_modules")
    return target


def card_model_core(directory):
    text = (ROOT / "workbench/src/gates/core.ts").read_text(encoding="utf-8")
    old = 'else if (attempt.delivery && trailers.model![0] !== "unknown" && trailers.model![0] !== attempt.delivery.model) error = "trailer_identity_mismatch";\n'
    new = 'else if (attempt.delivery && trailers.model![0] !== "unknown" && trailers.model![0] !== task.card.executor.model) error = "trailer_identity_mismatch";\n'
    if text.count(old) != 1:
        raise RuntimeError("model comparison is not unique")
    src = directory / "src"
    shutil.copytree(ROOT / "workbench/src", src, symlinks=True)
    target = src / "gates/core.ts"
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    (directory / "node_modules").symlink_to(ROOT / "workbench/node_modules")
    return target


def run_suite(phase, core, out, modes):
    t084.HOST = ROOT / "workbench/tests/daemon_acceptance_host.ts"
    return t084.run_cases(phase, core, out, modes)


def save(report):
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    stock = ROOT / "workbench/tests/daemon_acceptance_host.ts"
    ctx = setup("stock", stock)
    try:
        report["claim_forged"] = claim_probe(ctx)
        save(report)
        report["effort_unknown_real_core"] = effort_unknown_probe(ctx)
        save(report)
    except Exception:
        report["stock_exception"] = traceback.format_exc()
        save(report)
    finally:
        stop(ctx)
    layout = Path("/tmp/t084-host-layout")
    if layout.exists():
        shutil.rmtree(layout)
    host = make_host(layout)
    ctx = setup("diverged", host)
    try:
        report["model_card_versus_record"] = divergence_probe(ctx)
        save(report)
    except Exception:
        report["diverged_exception"] = traceback.format_exc()
        save(report)
    finally:
        stop(ctx)
    scratch = Path(tempfile.mkdtemp(prefix="t084m-review-", dir="/tmp"))
    try:
        core = t084.mutant_core("launch", scratch)
        report["mutant_delete_launch"] = run_suite(
            "mutant-launch", core, OUT / "mutant-delete-launch", ["launch"])
        save(report)
    except Exception:
        report["mutant_delete_launch_exception"] = traceback.format_exc()
        save(report)
    scratch = Path(tempfile.mkdtemp(prefix="t084m-effort-", dir="/tmp"))
    try:
        core = effort_exemption_core(scratch)
        modes = [*t084.MISMATCHES, "match", "unknown", "none"]
        report["mutant_effort_unknown_exemption_suite"] = run_suite(
            "green", core, OUT / "mutant-effort-exemption", modes)
        save(report)
    except Exception:
        report["mutant_effort_unknown_exemption_exception"] = traceback.format_exc()
        save(report)
    scratch = Path(tempfile.mkdtemp(prefix="t084m-card-", dir="/tmp"))
    try:
        core = card_model_core(scratch)
        modes = [*t084.MISMATCHES, "match", "unknown", "none"]
        report["mutant_compare_model_to_card_suite"] = run_suite(
            "green", core, OUT / "mutant-card-model", modes)
        save(report)
    except Exception:
        report["mutant_compare_model_to_card_exception"] = traceback.format_exc()
        save(report)
    print(json.dumps({key: (value.get("status") if isinstance(value, dict) and "status" in value else "see-report")
                      for key, value in report.items()}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
