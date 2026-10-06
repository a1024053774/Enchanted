#!/usr/bin/env python3
"""Index one supplied Claude transcript without exporting thinking blocks."""

import argparse
from collections import Counter
import json
from pathlib import Path


SELECTED_LINES = {
    "C01": [273, 484],
    "C02": [7561, 7565, 7566, 7568],
    "C03": [8905, 8927],
    "C04": [3558, 8660],
    "C05": [10337, 10342, 10361],
    "C06": [5141, 5679, 8828],
    "C07": [5564, 6590],
    "C08": [6690, 7237, 7254, 7314],
    "C09": [1939, 5417],
    "C10": [7442, 7473, 7492, 7558],
    "C11": [8785, 8821, 10406, 10410, 10416, 10417, 10418],
    "C12": [10387, 10393],
}


def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(block.get("text", "") for block in value
                         if isinstance(block, dict) and block.get("type") == "text")
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    raw = source.read_bytes()
    lines = raw.splitlines()
    raw_types = Counter()
    tools = Counter()
    models = Counter()
    timestamps = []
    records = []
    excerpts = []
    selected = {line: group for group, group_lines in SELECTED_LINES.items() for line in group_lines}
    for number, line in enumerate(lines, 1):
        row = json.loads(line)
        kind = row.get("type")
        raw_types[kind] += 1
        if row.get("timestamp"):
            timestamps.append(row["timestamp"])
        if kind not in ("user", "assistant"):
            continue
        message = row.get("message", {})
        content = message.get("content", [])
        if kind == "assistant":
            models[message.get("model", "unknown")] += 1
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        selected_parts = []
        for position, block in enumerate(content):
            block_type = block.get("type")
            if block_type not in ("text", "tool_use", "tool_result"):
                continue
            record = {"line": number, "block": position, "timestamp": row.get("timestamp"),
                      "uuid": row.get("uuid"), "role": kind, "kind": block_type}
            if block_type == "tool_use":
                tools[block["name"]] += 1
                record.update(tool=block["name"], tool_id=block["id"])
                value = block.get("input", {})
                part = {"kind": block_type, "tool": block["name"], "tool_id": block["id"],
                        "description": value.get("description", value.get("summary")),
                        "text": value.get("command", value.get("message", value.get("content", "")))}
            elif block_type == "tool_result":
                record.update(tool_id=block.get("tool_use_id"), is_error=block.get("is_error", False))
                part = {"kind": block_type, "is_error": block.get("is_error", False),
                        "text": text_content(block.get("content"))}
            else:
                text = block.get("text", "")
                record["is_meta"] = row.get("isMeta", False)
                record["task_notification"] = text.lstrip().startswith("<task-notification>")
                part = {"kind": block_type, "text": text}
            records.append(record)
            if number in selected:
                part["partial"] = len(part["text"]) > 5000
                part["text"] = part["text"][:5000]
                selected_parts.append(part)
        if number in selected:
            excerpts.append({"case": selected[number], "source_line": number,
                             "timestamp": row.get("timestamp"), "role": kind,
                             "uuid": row.get("uuid"), "parts": selected_parts})
    manifest = {
        "source": str(source), "session_id": "a94ba246-5f01-45e5-b06b-4024882c4ff2",
        "source_bytes": len(raw), "source_lines": len(lines),
        "first_timestamp": min(timestamps), "last_timestamp": max(timestamps),
        "raw_record_types": dict(raw_types), "recorded_tool_calls": dict(tools),
        "assistant_record_models": dict(models), "index_records": len(records),
        "selected_records": len(excerpts),
        "limits": ["User-role records can contain agent-injected text or background notifications.",
                   "Tool calls and notifications are not business acceptance results.",
                   "Model fields are local records, not provider fulfillment evidence.",
                   "Thinking blocks are excluded from the index and excerpts."]
    }
    output.mkdir(parents=True, exist_ok=False)
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with (output / "record-index.jsonl").open("x", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    with (output / "excerpts.json").open("x", encoding="utf-8") as stream:
        json.dump({"source": str(source), "records": excerpts}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({key: manifest[key] for key in
                      ("source_bytes", "source_lines", "index_records", "selected_records")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
