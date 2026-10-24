"""Read-only, selected facts for the T-164-2 report; never drive the run."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument("instance", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
db = sqlite3.connect(f"file:{args.instance}/state/state.sqlite3?mode=ro", uri=True)
cutoff = db.execute("select max(seq) from orchestration_events").fetchone()[0]
events = [dict(seq=s, time=t, type=k, launch=l, data=json.loads(d))
          for s, t, k, l, d in db.execute(
              "select seq,time,type,launch,data from orchestration_events where seq<=? order by seq", (cutoff,))]
launches = {l: json.loads(d) for l, d in db.execute("select id,data from launch_records")}
out = {"observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
       "cutoff_orchestration_seq": cutoff, "instance": str(args.instance),
       "launches": [], "codex_dispatches": [], "claude_roots": [], "a_timeline": []}
for lid, launch in launches.items():
    fields = ["task", "attempt", "session", "fence", "spec_rev", "role", "cli",
              "cli_version", "created_at", "model_requested", "effort_requested",
              "service_tier_requested", "base_commit", "code_revision", "worktree"]
    summary = {"launch": lid, **{k: launch.get(k) for k in fields}}
    records = [e for e in events if e["launch"] == lid]
    contexts = []
    for e in records:
        r = e["data"].get("record", {})
        if e["type"] == "native_record" and r.get("type") == "turn_context":
            p = r.get("payload", {})
            contexts.append({"seq": e["seq"], "timestamp": r.get("timestamp"),
                             **{k: p.get(k) for k in ["turn_id", "model", "effort", "reasoning_effort", "service_tier"]}})
    summary["codex_turn_contexts"] = contexts
    summary["turn_start_signal_count"] = sum(e["type"] == "turn_start_signal" for e in records)
    out["launches"].append(summary)
    if launch.get("cli") != "Codex":
        continue
    queued = {e["data"]["id"]: e for e in records if e["type"] == "dispatch_queued"}
    pending = None
    for e in records:
        if e["type"] == "turn_submitted":
            pending = e
        elif e["type"] == "turn_start_signal" and pending:
            q = queued[pending["data"]["dispatch"]]
            seconds = lambda start, end: round((dt.datetime.fromisoformat(end.replace("Z", "+00:00")) - dt.datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds(), 3)
            out["codex_dispatches"].append({
                "launch": lid, "role": launch.get("role"), "source": q["data"].get("source"),
                "message_label": q["data"].get("text", "").splitlines()[0],
                "queued_seq": q["seq"], "queued_at": q["time"],
                "submitted_seq": pending["seq"], "submitted_at": pending["time"],
                "started_seq": e["seq"], "started_at": e["time"],
                "submit_to_start_seconds": seconds(pending["time"], e["time"]),
                "queue_to_start_seconds": seconds(q["time"], e["time"]),
                "turn_id": e["data"].get("turn_id"), "model": e["data"].get("model")})
            pending = None

for directory in Path("/Users/luckye/.claude/projects").glob(f"*{args.instance.name}*"):
    for path in directory.glob("*.jsonl"):
        roots = []
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("type") != "user" or row.get("isMeta"):
                continue
            content = row.get("message", {}).get("content", [])
            if isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                continue
            roots.append({"uuid": row.get("uuid"), "timestamp": row.get("timestamp")})
        if roots:
            out["claude_roots"].append({"file": str(path), "count": len(roots), "roots": roots})
out["claude_root_count"] = sum(r["count"] for r in out["claude_roots"])
a = "c55be686-692e-4059-bf8e-031e1e66c9a1"
for e in events:
    if e["launch"] != a or e["type"] not in ["claude_prompt_queued", "user_prompt_unregistered", "turn_end_signal", "turn_start_signal", "pane_idle", "relay_processed"]:
        continue
    d = e["data"]
    selected = {k: d[k] for k in ["prompt_id", "input_seq", "hook_event_name", "request_id"] if k in d}
    if "prompt" in d and e["type"] in ["claude_prompt_queued", "user_prompt_unregistered"]:
        selected["prompt"] = d["prompt"]
    if e["type"] == "relay_processed":
        result = d.get("result", {})
        selected.update(ok=result.get("ok"), error=result.get("error"),
                        candidate_commit=result.get("task", {}).get("candidate_commit"))
    out["a_timeline"].append({k: e[k] for k in ["seq", "time", "type"]} | {"data": selected})
with args.output.open("x", encoding="utf-8") as result_file:
    result_file.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"output": str(args.output), "cutoff": cutoff,
                  "claude_root_count": out["claude_root_count"],
                  "codex_dispatches": out["codex_dispatches"]}, ensure_ascii=False, indent=2))
