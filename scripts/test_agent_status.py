#!/usr/bin/env python3
"""T-095 命令入口合同检查；合成 Herdr 读数不代替真实面板红态。"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
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
if data.get('native_change') and a[:2] == ['agent','read'] and not (p/'native-shifted').exists():
    with pathlib.Path(data['native_log']).open('a',encoding='utf-8') as f:
        f.write(json.dumps({'type':'response_item','payload':{'type':'function_call_output','call_id':'question-call',
                      'output':json.dumps({'answers':{'q1':{'answers':['A']}}})}})+chr(10))
    (p/'native-shifted').write_text('explicit producer mutation')
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


def native_rows(session, cwd, mode="clear", question_count=1):
    result = [dict(type="session_meta", payload=dict(id=session, cwd=cwd, source="cli", cli_version="0.163.0")),
              dict(type="event_msg", payload=dict(type="task_started", turn_id="fixture-turn"))]
    if mode == "clear":
        return result
    asynchronous = mode in ("pending", "receipt", "publication-incomplete", "async-answered", "async-empty", "foreign-delivery", "uncorrelated-user", "invalid-receipt")
    request = dict(type="response_item", payload=dict(type="function_call", name="request_user_input_async" if asynchronous else "request_user_input",
        call_id="question-call", arguments=json.dumps({"questions":[{"title":f"fixture question {n}"} for n in range(question_count)] if asynchronous else [{"id":"q1","header":"fixture","question":"fixture question"}]}),
        internal_chat_message_metadata_passthrough=dict(turn_id="fixture-turn")))
    result.append(request)
    if asynchronous:
        result.append(dict(type="event_msg",payload=dict(type="item_completed",thread_id=session,turn_id="fixture-turn",
            item=dict(type="AgentMessage",id="question-call",delivery="async",questions=[{"title":f"fixture question {n}"} for n in range(question_count)]))))
        if mode != "publication-incomplete":
            result.append(dict(type="response_item",payload=dict(type="function_call_output",call_id="question-call",output='{"accepted":true}')))
        if mode in ("async-answered", "async-empty"):
            result.append(dict(type="response_item",payload=dict(type="function_call_output",call_id="question-call",
                output=json.dumps({"answers":{} if mode=="async-empty" else {"q1":{"answers":["A"]}}}))))
        if mode=="foreign-delivery": result[3]["payload"]["thread_id"]="foreign-session"
        if mode=="invalid-receipt": result[4]["payload"]["output"]='{"accepted":1}'
        if mode=="uncorrelated-user":
            result.append(dict(type="event_msg",payload=dict(type="item_completed",thread_id=session,turn_id="fixture-turn",
                item=dict(type="UserMessage",id="unmatched-user",content=[{"type":"text","text":"not interpreted as an answer"}]))))
    elif mode in ("answered", "empty-response", "orphan-response"):
        result.append(dict(type="response_item",payload=dict(type="function_call_output",call_id="other-call" if mode=="orphan-response" else "question-call",
            output=json.dumps({"answers":{} if mode=="empty-response" else {"q1":{"answers":["A"]}}}))))
    return result


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
    if recorded:
        native = meta["native_session"]
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
    if case.get("superseded"):
        other = dict(prepared, launch_id="launch-newer")
        rows.extend([other, dict(other, phase="started", pane=pane, agent=agent_name, herdr_result=started["herdr_result"])])
    if case.get("fail_command"):
        data["fail_command"] = case["fail_command"]
    if case.get("record_change"):
        data.update(record_change=True, record_path=str(root / "records/launches.jsonl"))
    native_log, native_store = root / "misleading-file-name.log", root / "native-index.sqlite"
    if case.get("native_change"):
        data.update(native_change=True,native_log=str(native_log))
    native_mode = case.get("native", "clear")
    events = native_rows(native, prepared["cwd"], native_mode, case.get("native_question_count", 1))
    if case.get("native_tail") == "output":
        events.append(dict(type="event_msg",payload=dict(type="item_completed",thread_id=native,turn_id="fixture-turn",
                      item=dict(type="AgentMessage",id="later-message",delivery="follow-up",text="still running"))))
    elif case.get("native_tail") == "completed":
        events.append(dict(type="event_msg",payload=dict(type="task_complete",turn_id="fixture-turn")))
    elif case.get("native_tail") == "next-turn":
        events.append(dict(type="event_msg",payload=dict(type="task_started",turn_id="next-fixture-turn")))
    if case.get("wrong_native_header"):
        events[0]["payload"]["id"]="foreign-session"
    content_native="".join(json.dumps(row)+"\n" for row in events)
    if case.get("partial_native"):
        content_native=content_native[:-1]
    if case.get("native_no_turn"):
        content_native=json.dumps(events[0])+"\n"
    if case.get("native_original"):
        content = Path(case["native_original"]).read_bytes()[:case["native_bytes"]]
        assert content.endswith(b"\n") and len(content) == case["native_bytes"]
        native_log.write_bytes(content)
    else:
        native_log.write_text(content_native,encoding="utf-8")
    db=sqlite3.connect(native_store)
    db.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, cwd TEXT, source TEXT)")
    db.execute("INSERT INTO threads VALUES (?,?,?,?)",("foreign-id" if case.get("wrong_index_id") else native,
               str(native_log),prepared["cwd"],"cli"))
    db.commit();db.close()
    if not case.get("native_unbound"):
        rows.append(dict(started,phase="native-session",native_session=native,native_store=str(native_store)))
    if case.get("latest_mutation"):
        rows[-1]["agent"]="other-worker"
    if case.get("missing_native_store"):
        native_store.unlink()
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
            if case.get("conflict"):
                assert value["conflicts"], value
        calls = [json.loads(line) for line in (observer / "calls.jsonl").read_text(encoding="utf-8").splitlines()] if (observer / "calls.jsonl").exists() else []
        assert all(a[:2] in (["agent", "get"], ["agent", "read"]) and a[2] == pane for a in calls), calls
        assert not (root / "records/.launches.lock").exists()
        expected_files={"misleading-file-name.log"}
        if not case.get("missing_native_store"): expected_files.add("native-index.sqlite")
        if not case.get("missing_record"): expected_files.add("records/launches.jsonl")
        assert {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()} == expected_files
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
    parser.add_argument("--archives-only", action="store_true", help="按主控 #115 的锚点合同回放三份真实归档，保留无锚点的 unknown")
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
    folded = "\n? 7 questions · age 2m 19s / arbitrary suffix\n"
    bar = "residual output\nanything ⌃] skip / unrelated decoration / ⇧→ main prompt tail\nmore output\n"
    cases.extend([
        dict(name="folded-anchor-blocked",expected="waiting_controller_answer",screen=folded,raw_state="blocked"),
        dict(name="folded-no-header-footer-or-arrow",expected="waiting_controller_answer",screen="? 1 question",raw_state="blocked"),
        dict(name="folded-suffix-is-unrestricted",expected="waiting_controller_answer",screen="  ? 12 questions🚀not-a-timer",raw_state="blocked"),
        dict(name="folded-native-count-not-a-third-vote",expected="waiting_controller_answer",screen=folded,raw_state="blocked",native="pending"),
        dict(name="folded-marker-only",expected="unknown",screen=folded,conflict=True),
        dict(name="blocked-only-even-with-native-question",expected="unknown",raw_state="blocked",native="pending",conflict=True),
        dict(name="blocked-only-clear-native",expected="unknown",raw_state="blocked",conflict=True),
        dict(name="blocked-empty-screen",expected="unknown",screen="",raw_state="blocked",conflict=True),
        dict(name="expanded-no-title-options-or-enter",expected="waiting_controller_answer",screen=bar,raw_state="blocked"),
        dict(name="expanded-unrelated-prefix-and-suffix",expected="waiting_controller_answer",screen="prefix\n"*30+bar+"suffix\n"*20,raw_state="blocked"),
        dict(name="expanded-markers-must-share-line",expected="unknown",screen="⌃] skip\n⇧→ main prompt",raw_state="blocked",conflict=True),
        dict(name="expanded-skip-only",expected="unknown",screen="⌃] skip",raw_state="blocked",conflict=True),
        dict(name="expanded-main-prompt-only",expected="unknown",screen="⇧→ main prompt",raw_state="blocked",conflict=True),
        dict(name="expanded-marker-only",expected="unknown",screen=bar,conflict=True),
        dict(name="expanded-idle-with-marker",expected="unknown",screen=bar,raw_state="idle",conflict=True),
        dict(name="marker-presence-disagrees-between-reads",expected="unknown",screen=folded,detection=frame(),raw_state="blocked",conflict=True),
        dict(name="presentation-can-change-between-reads",expected="waiting_controller_answer",screen=folded,detection=bar,raw_state="blocked"),
        dict(name="count-presentation-can-change",expected="waiting_controller_answer",screen=folded,detection="? 99 question · any",raw_state="blocked"),
        dict(name="old-folded-marker-above-bottom-region",expected="working",screen=frame("? 8 questions\n"+"historical output\n"*20+"• Working (8s • esc to interrupt)")),
        dict(name="nonpositive-count-is-not-an-anchor",expected="unknown",screen="? 0 questions",raw_state="blocked",conflict=True),
        dict(name="anchor-does-not-bypass-native-identity",expected="unknown",screen=bar,raw_state="blocked",wrong_native_header=True),
        dict(name="pending-against-ordinary-working-is-conflict",expected="unknown",native="pending",conflict=True),
        dict(name="accepted-receipt-does-not-resolve",expected="unknown",native="receipt",conflict=True),
        dict(name="matched-answer-returns-working",expected="working",native="answered"),
        dict(name="empty-answer-map-returns-working",expected="working",native="empty-response"),
        dict(name="correlated-async-answer-closes-request",expected="working",native="async-answered"),
        dict(name="correlated-async-empty-response-closes-request",expected="working",native="async-empty"),
        dict(name="foreign-thread-question-not-adopted",expected="unknown",native="foreign-delivery"),
        dict(name="plain-user-text-is-not-resolution",expected="unknown",native="uncorrelated-user"),
        dict(name="native-publication-incomplete",expected="unknown",native="publication-incomplete",raw_state="blocked"),
        dict(name="unmatched-answer-is-unknown",expected="unknown",native="orphan-response"),
        dict(name="partial-native-line",expected="unknown",partial_native=True),
        dict(name="index-selects-only-bound-id",expected="unknown",wrong_index_id=True),
        dict(name="missing-native-store",expected="unknown",missing_native_store=True),
        dict(name="native-session-unbound",expected="unknown",native_unbound=True),
        dict(name="numeric-receipt-is-not-true",expected="unknown",native="invalid-receipt",raw_state="blocked"),
        dict(name="native-turn-not-observed",expected="unknown",native_no_turn=True),
        dict(name="native-changes-during-screen-read",expected="unknown",screen=folded,native="pending",raw_state="blocked",native_change=True,conflict=True),
        dict(name="later-same-turn-output-is-not-resolution",expected="unknown",native="pending",native_tail="output",conflict=True),
        dict(name="turn-completion-is-not-question-resolution",expected="unknown",native="pending",native_tail="completed",conflict=True),
        dict(name="new-turn-does-not-resolve-question",expected="unknown",native="pending",native_tail="next-turn"),
    ])
    archived = []
    red = json.loads((EVIDENCE / "real-panel-inputs.json").read_text(encoding="utf-8"))
    red_native = json.loads((EVIDENCE / "real-native-inputs.json").read_text(encoding="utf-8"))
    red["native_session"] = red_native["records"][0]["payload"]["id"]
    for label in ("collapsed", "expanded", "cancelled"):
        archived.append(dict(name="archive-red-"+label,expected="waiting_controller_answer" if label=="expanded" else "unknown",
                             recorded=dict(meta=red,capture=red["captures"][label]),native_original=red_native["original"],
                             native_bytes=Path(red_native["original"]).stat().st_size,conflict=label!="expanded",
                             source=red["source_archive"]+"; current anchor contract; reconstructed launch binding from archived start reply and verified native header"))
    for prefix, filename in (("green","real-green-inputs.json"),("green-independent","real-independent-inputs.json")):
        saved=json.loads((EVIDENCE/filename).read_text(encoding="utf-8"))
        started=next(row for row in saved["launches"] if row["phase"]=="started")
        meta=dict(worker=saved["worker"],launch=saved["launch"],cwd=started["cwd"],cli_version=started["cli_version"],
                  model=started["model"],effort=started["effort"],code_revision=saved["source_revision"],start=started["herdr_result"],native_session=saved["native_session"])
        for label,capture in saved["captures"].items():
            values={key:capture[key] for key in ("visible","detection")}
            for key in ("before","after"):values[key]=json.loads(capture[key])["result"]["agent"]
            archived.append(dict(name="archive-"+prefix+"-"+label,expected="waiting_controller_answer" if label in ("collapsed","expanded") else "unknown",
                                 recorded=dict(meta=meta,capture=values),native_original=saved["native_archive"]["archive"],native_bytes=capture["native_bytes"],
                                 conflict=label not in ("collapsed","expanded"),source=saved["source_archive"]+"; exact captured surfaces and projection native-byte cutoff"))
    cases = archived if args.archives_only else cases + archived
    directory = Path(tempfile.mkdtemp(prefix="t095-status-contract-", dir="/tmp"))
    reports = [run_case(args.entry.resolve(), directory / str(i), i, case) for i, case in enumerate(cases, 1)]
    passed = all(row["status"] == "PASS" for row in reports)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as file:
        json.dump(dict(status="PASS" if passed else "FAIL", scope="anchor contract for three archived runs; not fresh live validation" if args.archives_only else "anchor, identity and conservative working contract; not fresh live validation",
                       command=[sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                       fixture=None if passed else str(directory), cases=reports), file, ensure_ascii=False, indent=2)
    if passed:
        shutil.rmtree(directory)
    print(json.dumps(dict(status="PASS" if passed else "FAIL", cases=len(reports),
                          failed=[row["case"] for row in reports if row["status"] != "PASS"], report=str(args.report)), ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
