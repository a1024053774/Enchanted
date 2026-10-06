#!/usr/bin/env python3
"""Index project session records without exporting message or reasoning content."""

import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--codex-root", required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    codex = Path(args.codex_root).resolve()
    cutoff = timestamp(args.cutoff)
    output = Path(args.output).resolve()
    db = sqlite3.connect((codex / "state_5.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    columns = "id,rollout_path,cwd,source,model,reasoning_effort,cli_version,created_at"
    selected = {row["id"]: dict(row) for row in db.execute(
        "SELECT " + columns + " FROM threads WHERE (cwd=? OR cwd LIKE ?) AND created_at<?",
        (str(root), str(root) + "/%", cutoff.timestamp()))}
    edges = list(db.execute("SELECT parent_thread_id,child_thread_id FROM thread_spawn_edges"))
    while True:
        added = False
        for parent, child in edges:
            if parent in selected and child not in selected:
                row = db.execute("SELECT " + columns + " FROM threads WHERE id=? AND created_at<?",
                                 (child, cutoff.timestamp())).fetchone()
                if row is not None:
                    selected[child] = dict(row)
                    added = True
        if not added:
            break
    db.close()
    if not selected:
        raise RuntimeError("No project sessions matched the metadata query")

    # Only metadata determines scope. Unrelated message bodies are not inspected.
    paths = {Path(row["rollout_path"]) for row in selected.values()}
    first = datetime.fromtimestamp(min(row["created_at"] for row in selected.values()), timezone.utc)
    day = first.date() - timedelta(days=1)
    while day <= cutoff.date():
        folder = codex / "sessions" / day.strftime("%Y/%m/%d")
        paths.update(folder.glob("rollout-*.jsonl"))
        paths.update((codex / "archived_sessions").glob("rollout-" + day.isoformat() + "*.jsonl"))
        day += timedelta(days=1)
    scoped = []
    for path in sorted(paths):
        with path.open(encoding="utf-8") as stream:
            first_record = json.loads(stream.readline())
        meta = first_record.get("payload", {})
        cwd = meta.get("cwd", "")
        sid = meta.get("id")
        if not (cwd == str(root) or cwd.startswith(str(root) + "/") or sid in selected):
            continue
        if timestamp(first_record["timestamp"]) >= cutoff:
            continue
        scoped.append((path, meta))

    sessions = []
    records = []
    for path, meta in scoped:
        sid = meta["id"]
        entry = {"session_id": sid, "path": str(path), "cwd": meta.get("cwd"),
                 "indexed": sid in selected, "metadata": selected.get(sid),
                 "first_timestamp": None, "last_timestamp": None,
                 "included_lines": 0, "included_bytes": 0}
        types = Counter()
        tools = Counter()
        configurations = []
        with path.open("rb") as stream:
            for line_number, raw in enumerate(stream, 1):
                row = json.loads(raw)
                if timestamp(row["timestamp"]) >= cutoff:
                    break
                entry["included_lines"] = line_number
                entry["included_bytes"] += len(raw)
                entry["first_timestamp"] = entry["first_timestamp"] or row["timestamp"]
                entry["last_timestamp"] = row["timestamp"]
                payload = row.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                if row["type"] == "turn_context":
                    configuration = {key: payload.get(key) for key in ("model", "effort", "cwd")}
                    if configuration not in configurations:
                        configurations.append(configuration)
                if row["type"] != "response_item":
                    continue
                kind = payload.get("type")
                if kind in ("reasoning", "compaction"):
                    continue
                if kind == "message" and payload.get("role") not in ("user", "assistant"):
                    continue
                if kind not in ("message", "custom_tool_call", "custom_tool_call_output",
                                "function_call", "function_call_output", "agent_message"):
                    continue
                types[kind] += 1
                record = {"session_id": sid, "line": line_number, "timestamp": row["timestamp"],
                          "kind": kind}
                for key in ("role", "name", "call_id"):
                    if key in payload:
                        record[key] = payload[key]
                if kind in ("custom_tool_call", "function_call"):
                    tools[payload.get("name", "unknown")] += 1
                    if payload.get("name") == "spawn_agent":
                        arguments = json.loads(payload["arguments"])
                        record["delegation"] = {key: arguments[key] for key in
                                                ("task_name", "agent_type", "fork_turns", "model",
                                                 "reasoning_effort") if key in arguments}
                records.append(record)
        entry.update(response_types=dict(types), top_level_tools=dict(tools), configurations=configurations)
        sessions.append(entry)

    sessions.sort(key=lambda entry: (entry["first_timestamp"], entry["session_id"]))
    for number, entry in enumerate(sessions, 1):
        entry["label"] = "S%02d" % number
    labels = {entry["session_id"]: entry["label"] for entry in sessions}
    for record in records:
        record["label"] = labels[record["session_id"]]
    manifest = {"scope": str(root), "cutoff_exclusive": args.cutoff,
                "source_database": str(codex / "state_5.sqlite"), "database_read_only": True,
                "indexed_sessions": len(selected), "matched_files": len(sessions),
                "total_included_bytes": sum(entry["included_bytes"] for entry in sessions),
                "index_records": len(records), "session_records": sessions,
                "limits": ["Metadata is a local configuration record, not provider fulfillment.",
                           "The index excludes reasoning, system instructions, and message bodies.",
                           "Tool calls are wrapper calls, not counts of subprocesses or failures.",
                           "The cutoff excludes the retrospective itself."]}
    output.mkdir(parents=True, exist_ok=False)
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with (output / "record-index.jsonl").open("x", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps({key: manifest[key] for key in
                      ("indexed_sessions", "matched_files", "total_included_bytes", "index_records")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
