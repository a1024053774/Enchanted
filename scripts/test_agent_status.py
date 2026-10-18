#!/usr/bin/env python3
"""T-095 命令入口合同检查；合成 Herdr 读数不代替真实面板红态。"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "evidence/2026-10-16-batch16/T-095"
FAKE_HERDR = '''#!/usr/bin/env python3
import json, os, pathlib, sys
p = pathlib.Path(os.environ['T095_SOURCE'])
a = sys.argv[1:]
calls = p / 'calls.jsonl'
previous = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
with calls.open('a', encoding='utf-8') as f:
    f.write(json.dumps(a) + '\\n')
data = json.loads((p / 'source.json').read_text(encoding='utf-8'))
if data.get('record_change') and a[:2] == ['agent','read']:
    target = pathlib.Path(data['record_path'])
    rows = [json.loads(line) for line in target.read_text(encoding='utf-8').splitlines()]
    for row in rows:
        row['task'] = 'externally-replaced-task'
    target.write_text(''.join(json.dumps(row) + '\\n' for row in rows), encoding='utf-8')
if data.get('fail_command') == a[:2]:
    print('explicit synthetic Herdr failure', file=sys.stderr)
    sys.exit(1)
if a[:2] == ['agent','get'] and len(a) == 3:
    n = sum(json.loads(line)[:2] == ['agent','get'] for line in previous)
    agent = data['before'] if n == 0 else data['after']
    print(json.dumps({'result': {'agent': agent}}))
elif a[:2] == ['agent','read'] and len(a) == 7 and a[5:] == ['--format','text']:
    if a[3] != '--source' or a[4] not in ('visible', 'detection'):
        sys.exit(7)
    sys.stdout.write(data[a[4]])
else:
    print('unexpected command: ' + repr(a), file=sys.stderr)
    sys.exit(8)
'''


def frame(body="• Working (14s • esc to interrupt)"):
    return (body + "\n\n\n› Ask Codex to do anything\n\n"
            "  GPT-6.1-Sol xhigh fast · /fixture · synthetic contract\n"
            "  ? for shortcuts\n")


def run_case(entry, directory, number, case):
    root, observer, fakebin = directory / "root", directory / "observer", directory / "bin"
    for path in (root, observer, fakebin, root / "records"):
        path.mkdir(parents=True, exist_ok=True)
    agent_name, launch_id = f"sentinel-worker-{number}", f"launch-sentinel-{number}"
    pane, native, terminal = f"wTest:p{number}", f"native-sentinel-{number}", f"terminal-{number}"
    prepared = dict(schema=1, phase="prepared", launch_id=launch_id, created_at="2026-10-18T02:00:00Z",
                    project="synthetic", task=f"T-095-contract-{number}", attempt="a1", session=f"session-{number}",
                    role="worker", cli="codex", cli_version="codex-cli 0.163.0", model="gpt-6.1-sol",
                    effort="xhigh", service_tier_requested="fast", cwd=str(root), project_commit="synthetic-baseline",
                    launcher_commit="synthetic-baseline", role_card="synthetic-role", role_card_version="synthetic-role-v1",
                    argv=["codex", "--no-daemon"], native_session="unknown")
    live = dict(name=agent_name, agent="codex", pane_id=pane, terminal_id=terminal, revision=2,
                cwd=str(root), foreground_cwd=str(root), interactive_ready=True, state_change_seq=71,
                agent_status=case.get("raw_state", "working"),
                agent_session=dict(agent="codex", kind="id", source="herdr:codex", value=native))
    recorded = case.get("recorded")
    if recorded:
        meta, capture = recorded["meta"], recorded["capture"]
        agent_name, launch_id, pane = meta["worker"], meta["launch"], capture["before"]["pane_id"]
        prepared.update(launch_id=launch_id, project="a2a", task="T-095", cwd=meta["cwd"],
                        cli_version=meta["cli_version"], model=meta["model"], effort=meta["effort"],
                        argv=meta["start"]["result"]["argv"], project_commit=meta["code_revision"])
        live = copy.deepcopy(capture["before"])
    started = dict(prepared, phase="started", pane=pane, agent=agent_name,
                   herdr_result={"result": {"agent": copy.deepcopy(live)}})
    if recorded:
        started["herdr_result"] = copy.deepcopy(meta["start"])
    if case.get("no_native_identity"):
        live.pop("agent_session", None)
        started["herdr_result"]["result"]["agent"].pop("agent_session", None)
    if case.get("invalid_initial_native"):
        started["herdr_result"]["result"]["agent"]["agent_session"] = "malformed native identity"
    if case.get("empty_initial_native"):
        started["herdr_result"]["result"]["agent"]["agent_session"] = []
    rows = [prepared, started]
    if case.get("bound"):
        rows.append(dict(started, phase="native-session", native_session=native))
    data = dict(before=copy.deepcopy(live), after=copy.deepcopy(live),
                visible=case.get("screen", frame()), detection=case.get("detection", case.get("screen", frame())))
    if recorded:
        data = {key:copy.deepcopy(capture[key]) for key in ("before", "after", "visible", "detection")}
    for target in ("before", "after"):
        data[target].update(case.get(target, {}))
    if case.get("native_after"):
        data["after"]["agent_session"]["value"] = "replaced-native"
    if case.get("native_both"):
        for target in ("before", "after"):
            data[target]["agent_session"]["value"] = "replaced-native"
    if case.get("latest_mutation"):
        rows.append(dict(started, phase="native-session", native_session=native, agent="other-worker"))
    if case.get("superseded"):
        other = dict(prepared, launch_id="launch-newer")
        rows.extend([other, dict(other, phase="started", pane=pane, agent=agent_name, herdr_result=started["herdr_result"])])
    if case.get("fail_command"):
        data["fail_command"] = case["fail_command"]
    if case.get("record_change"):
        data.update(record_change=True, record_path=str(root / "records/launches.jsonl"))
    if case.get("prepared_only"):
        rows = rows[:1]
    launches = root / "records/launches.jsonl"
    content = "".join(json.dumps(row) + "\n" for row in rows)
    if case.get("corrupt_record"):
        content = content[:-1]
    if not case.get("missing_record"):
        launches.write_text(content, encoding="utf-8")
    (observer / "source.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    executable = fakebin / "herdr"
    # Use the runner's interpreter directly. PATH may select a platform launcher
    # before Python starts, which is outside the simulated Herdr response.
    executable.write_text("#!" + sys.executable + "\n" + FAKE_HERDR.split("\n", 1)[1], encoding="utf-8")
    executable.chmod(0o755)
    env = dict(os.environ, PATH=str(fakebin) + os.pathsep + os.environ["PATH"],
               PYTHONPATH=str(REPO / "scripts"), PYTHONDONTWRITEBYTECODE="1", HERDR_ENV="1", T095_SOURCE=str(observer))
    if case.get("outside_herdr"):
        env.pop("HERDR_ENV")
    argv = [sys.executable, str(entry), "--root", str(root), "--launch", launch_id]
    outputs, failure = [], None
    try:
        expected_states = case.get("sequence", [case["expected"]])
        for index, expected in enumerate(expected_states):
            if index and case.get("next_capture"):
                data = {key:copy.deepcopy(case["next_capture"][key]) for key in ("before", "after", "visible", "detection")}
                (observer / "source.json").write_text(json.dumps(data), encoding="utf-8")
            elif index:
                data.update(visible=frame("• Finished a synthetic task."), detection=frame("• Finished a synthetic task."))
                for target in ("before", "after"):
                    data[target]["agent_status"] = "done"
                (observer / "source.json").write_text(json.dumps(data), encoding="utf-8")
            # The command permits four reads at three seconds each. The runner
            # also permits interpreter startup, without changing that contract.
            result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=20)
            outputs.append(dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
            value = json.loads(result.stdout)
            assert value["state"] == expected, value
            assert value["launch"] == launch_id, value
            if not any(case.get(key) for key in ("missing_record", "corrupt_record", "outside_herdr", "prepared_only")):
                assert value["worker"] == agent_name, value
            assert result.returncode == (2 if expected == "unknown" else 0), outputs[-1]
            assert value["state_label"] == {"unknown": "未知", "working": "工作中", "idle": "空闲",
                                             "waiting_controller_answer": "等待主控回答"}[expected], value
            if expected in ("working", "waiting_controller_answer"):
                assert value["pane"] == pane and value["task"] == prepared["task"], value
                assert {item["source"] for item in value["evidence"]} == {"visible", "detection"}, value
        calls = [json.loads(line) for line in (observer / "calls.jsonl").read_text(encoding="utf-8").splitlines()] if (observer / "calls.jsonl").exists() else []
        assert all(a[:2] in (["agent", "get"], ["agent", "read"]) and a[2] == pane for a in calls), calls
        assert not (root / "records/.launches.lock").exists()
        assert sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()) == ([] if case.get("missing_record") else ["records/launches.jsonl"])
        if launches.exists() and not case.get("record_change"):
            assert launches.read_text(encoding="utf-8") == content
    except (AssertionError, KeyError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        failure = str(exc)
    return dict(case=case["name"], expected=case.get("sequence", [case["expected"]]),
                source=case.get("source", "synthetic contract"), argv=argv, outputs=outputs,
                status="PASS" if failure is None else "FAIL", failure=failure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", type=Path, default=REPO / "scripts/agent-status")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--panel-contract", action="store_true", help="核对两种真实面板都必须正判等待；不能用安全 unknown 通过")
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("报告已存在，保留旧证据；请使用新文件名")
    cases = [
        dict(name="working-thinking", expected="working"),
        dict(name="working-command-context", expected="working", screen=frame("• Running a synthetic command\n• Working (2m 4s • esc to interrupt)")),
        dict(name="tip-and-background-terminal", expected="working", screen=frame("• Working (3m 48s • esc to interrupt) · 1 background terminal running · /ps to view · /stop to close\n  └ Tip: synthetic interface tip")),
        dict(name="raw-working-is-insufficient", expected="unknown", screen="No readable interface\n"),
        dict(name="quoted-activity-is-not-current", expected="unknown", screen=frame("  └ • Working (14s • esc to interrupt)\n• Actual response finished.")),
        dict(name="quoted-panel-text-is-not-a-panel", expected="working", screen=frame("  └ Type your answer / Queued follow-up inputs\n• Working (14s • esc to interrupt)")),
        dict(name="unverified-panel-tail", expected="unknown", screen=frame("• Working (14s • esc to interrupt)\n• Queued follow-up inputs\n  Type your answer\n  ⇧→ main prompt")),
        dict(name="panel-exit-recomputes", expected="unknown", sequence=["unknown", "idle"], screen=frame("• Queued follow-up inputs\n  Type your answer\n  ⇧→ main prompt")),
        dict(name="draft-is-unknown", expected="unknown", screen=frame().replace("› Ask Codex to do anything", "› unsent draft")),
        dict(name="truncated-footer", expected="unknown", screen=frame().replace("  ? for shortcuts\n", "")),
        dict(name="model-footer-mismatch", expected="unknown", screen=frame().replace("GPT-6.1-Sol", "Other-Model")),
        dict(name="readings-disagree", expected="unknown", detection=frame("• Queued follow-up inputs\n  Type your answer")),
        dict(name="different-worker", expected="unknown", before={"name": "other-worker"}),
        dict(name="different-pane", expected="unknown", before={"pane_id": "wOther:p1"}),
        dict(name="different-terminal", expected="unknown", before={"terminal_id": "other-terminal"}),
        dict(name="presentation-revision-is-not-identity", expected="working", after={"revision": 3}),
        dict(name="isolated-session-without-herdr-native-id", expected="working", no_native_identity=True),
        dict(name="different-cwd", expected="unknown", after={"foreground_cwd": "/other"}),
        dict(name="native-changed-mid-read", expected="unknown", native_after=True),
        dict(name="bound-native-replaced", expected="unknown", bound=True, native_both=True),
        dict(name="bound-native-cannot-disappear", expected="unknown", bound=True,
             before={"agent_session":None}, after={"agent_session":None}),
        dict(name="state-changed-mid-read", expected="unknown", after={"state_change_seq": 72}),
        dict(name="native-row-swaps-worker", expected="unknown", latest_mutation=True),
        dict(name="malformed-initial-native", expected="unknown", invalid_initial_native=True),
        dict(name="empty-initial-native-is-not-unbound", expected="unknown", empty_initial_native=True),
        dict(name="launch-record-changed-mid-read", expected="unknown", record_change=True),
        dict(name="newer-launch-reuses-pane", expected="unknown", superseded=True),
        dict(name="unstarted-launch", expected="unknown", prepared_only=True),
        dict(name="missing-launch", expected="unknown", missing_record=True),
        dict(name="partial-launch-log", expected="unknown", corrupt_record=True),
        dict(name="herdr-read-failure", expected="unknown", fail_command=["agent", "read"]),
        dict(name="outside-herdr", expected="unknown", outside_herdr=True),
    ]
    visible = (EVIDENCE / "ordinary-working-visible.txt").read_text(encoding="utf-8")
    detection = (EVIDENCE / "ordinary-working-detection.txt").read_text(encoding="utf-8")
    cases.append(dict(name="captured-ordinary-working-screen", expected="working", screen=visible, detection=detection,
                      source="ordinary-working-source.json; existing worker screen, synthetic identity transport"))
    meta = json.loads((EVIDENCE / "real-panel-inputs.json").read_text(encoding="utf-8"))
    panel = "\n  独立哨兵问题，不匹配 T-095 或 A/B 文本。\n\n  › 2. 任意选项\n\n  enter submit   ⌃] skip   option 2/4   ⇧→ main prompt\n"
    cases.extend([
        dict(name="question-with-unseen-title-and-selection", expected="waiting_controller_answer", screen=panel),
        dict(name="question-despite-raw-blocked", expected="waiting_controller_answer", screen=panel, raw_state="blocked"),
        dict(name="question-quoted-in-transcript", expected="working", screen=frame("• Printed a synthetic quote:" + panel + "\n• Working (4s • esc to interrupt)")),
        dict(name="question-controls-truncated", expected="unknown", screen=panel.replace("   ⇧→ main prompt", "")),
        dict(name="question-title-truncated", expected="unknown", screen=panel.replace("  独立哨兵问题，不匹配 T-095 或 A/B 文本。\n", "")),
        dict(name="question-selection-disagrees-with-footer", expected="unknown", screen=panel.replace("option 2/4", "option 1/4")),
        dict(name="question-readings-disagree", expected="unknown", screen=panel, detection=frame()),
        dict(name="blocked-and-activity-alone-is-ambiguous", expected="unknown", raw_state="blocked"),
    ])
    recorded_cases = [dict(name="real-" + label, expected=expected,
                           recorded=dict(meta=meta, capture=meta["captures"][label]),
                           source=meta["source_archive"] + "/run.json; exact captured read payloads")
                      for label, expected in (("collapsed", "unknown"), ("expanded", "waiting_controller_answer"),
                                              ("cancelled", "working"), ("after-submit", "unknown"))]
    if args.panel_contract:
        cases = [dict(case, expected="waiting_controller_answer") for case in recorded_cases[:2]]
    else:
        cases.extend(recorded_cases)
        cases.append(dict(recorded_cases[1], name="real-question-then-manual-skip",
                          sequence=["waiting_controller_answer", "working"], next_capture=meta["captures"]["cancelled"]))
    directory = Path(tempfile.mkdtemp(prefix="t095-status-contract-", dir="/tmp"))
    reports = [run_case(args.entry.resolve(), directory / str(i), i, case) for i, case in enumerate(cases, 1)]
    passed = all(row["status"] == "PASS" for row in reports)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as file:
        json.dump(dict(status="PASS" if passed else "FAIL", scope="recorded panel contract" if args.panel_contract else "contract and replay; not live green acceptance",
                       command=[sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                       fixture=None if passed else str(directory), cases=reports), file, ensure_ascii=False, indent=2)
    if passed:
        shutil.rmtree(directory)
    print(json.dumps(dict(status="PASS" if passed else "FAIL", cases=len(reports),
                          failed=[row["case"] for row in reports if row["status"] != "PASS"], report=str(args.report)), ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
