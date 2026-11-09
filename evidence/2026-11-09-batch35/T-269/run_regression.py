"""T-269 regression set: run existing store, question and turn-trust tests and keep a text record of each.

Usage (from the repository root): python3 evidence/2026-11-09-batch35/T-269/run_regression.py <label> <scratch dir> <record.json>
The scratch dir receives the tests' own outputs and fixtures and is removed afterwards; the record keeps, per test,
the command, exit code, the status the test reported, a verdict and the last lines of its output.

Invariant (T-269 review 02 #1): an exit code of 0 is not a pass by itself. A test passes only when it reports PASS
(its summary file or a JSON line on stdout), or, for relay_core, which reports `failure`, when that is null with at
least one effect. Anything else that exits 0 is "unverified", never "pass". A test that failed before reaching the
changed code proves nothing about that code; the record keeps its error so a reader can see where it stopped.
"""
import json
import os
import shutil
import subprocess
import sys
import time

label, scratch, record = sys.argv[1], sys.argv[2], sys.argv[3]
electron = "/Applications/Enchanted.app/Contents/MacOS/Enchanted"
driver = "evidence/2026-11-09-batch35/T-269/t108_contract_driver.mjs"
os.makedirs(scratch)
# (name, argv after the runtime, extra env, summary file, directory to create first)
tests = [
    ("t096_restore", ["workbench/tests/test_t096_restore.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t112_execution", ["workbench/tests/test_t112_execution.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t146_released_projection", ["workbench/tests/test_t146_released_projection.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t146_session_end", ["workbench/tests/test_t146_session_end.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t146_ended_projection", ["workbench/tests/test_t146_ended_projection.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t109_hierarchy", ["workbench/tests/test_t109_hierarchy.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t140_project_events", ["workbench/tests/test_t140_project_events.ts"], {}, None, None),
    ("relay_core", ["workbench/tests/test_relay_core.ts", "{out}"], {}, None, None),
    ("t078_pane_runtime", ["workbench/tests/test_t078_pane_runtime.ts", "{out}"], {}, None, None),
    ("t139_layout_store", ["workbench/tests/test_t139_layout_store.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t108_questions", ["workbench/tests/test_t108_questions.mjs", "{out}.json"], {}, "{out}.json", None),
    ("t108_answer_lifecycle", [driver, "workbench/tests/t108_answer_lifecycle_contracts.mjs", "answerLifecycleContracts", "{out}.json"],
     {}, "{out}.json", None),
    ("t108_hook_failure", [driver, "workbench/tests/t108_hook_failure_contracts.mjs", "hookFailureContracts", "{out}.json"],
     {}, "{out}.json", None),
    ("t166_queued_input", ["workbench/tests/test_t166_queued_input.ts", ".", "{out}"], {}, "{out}/results.json", "{out}"),
    ("t258_codex_late_start", ["workbench/tests/test_t258_codex_late_start.ts"],
     {"T258_SUMMARY": "{out}.json", "T258_SOURCE_ROOT": "."}, "{out}.json", None),
]


def stdout_report(text):
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                return value
    return None


results = []
try:
    for name, args, extra, summary_path, make_dir in tests:
        out = os.path.join(scratch, name)
        if make_dir:
            os.makedirs(make_dir.format(out=out))
        argv = [electron] + [a.format(out=out) for a in args]
        env = dict(os.environ, ELECTRON_RUN_AS_NODE="1", **{k: v.format(out=out) for k, v in extra.items()})
        started = time.time()
        try:
            done = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=300)
            code, text = done.returncode, done.stdout + done.stderr
        except subprocess.TimeoutExpired:
            code, text = "timeout", ""
        summary = None
        if summary_path and os.path.isfile(summary_path.format(out=out)):
            with open(summary_path.format(out=out), encoding="utf-8") as handle:
                summary = json.load(handle)
        printed = stdout_report(text)
        status = (summary or {}).get("status") or (printed or {}).get("status")
        if status == "PASS" and code == 0:
            verdict = "pass"
        elif name == "relay_core" and code == 0 and printed and "failure" in printed:
            verdict = "pass" if printed["failure"] is None and printed.get("effect_count", 0) > 0 else "fail"
        elif code == 0 and status is None:
            verdict = "unverified"
        else:
            verdict = "fail"
        error = (summary or {}).get("error")
        lines = [line for line in text.splitlines() if line.strip() and "ExperimentalWarning" not in line and "--trace-warnings" not in line]
        entry = {"test": name, "argv": [os.path.relpath(a) if a.startswith(scratch) else a for a in argv[1:]],
                 "exit": code, "status": status, "verdict": verdict, "error": (str(error)[:400] if error else None),
                 "seconds": round(time.time() - started, 1), "tail": lines[-12:]}
        if summary and "cases" in summary:
            entry["cases"], entry["failed_cases"] = summary["cases"], summary["failed"]
        results.append(entry)
        print(name, code, status, verdict, flush=True)
finally:
    shutil.rmtree(scratch, ignore_errors=True)
    with open(record, "x", encoding="utf-8") as handle:
        json.dump({"label": label, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runtime": electron,
                   "results": results}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
