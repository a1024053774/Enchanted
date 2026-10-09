#!/usr/bin/env python3
"""Check the ready_rev 2 catalog contract against preserved observations."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
before = json.loads((root / "catalog-baseline.json").read_text(encoding="utf-8"))
after = json.loads((root / "catalog-green-02.json").read_text(encoding="utf-8"))
inputs = json.loads((root / "catalog-inputs.json").read_text(encoding="utf-8"))
expected_changes = {"a2a_submit", "a2a_raise", "synara_e2e_review"}
accept_once = {"response": {"id": 19, "result": {"action": "accept", "content": None, "_meta": None}}, "pending": 0}
pending = {"response": None, "pending": 1}
assert before["inputSource"] == after["inputSource"] == inputs["source_revision"]
assert [r["tool"] for r in before["results"]] == [r["tool"] for r in after["results"]] == inputs["names"]
assert len(inputs["names"]) == len(set(inputs["names"])) == 116
changed = []
lines = ["# T-061：116 个工具前后逐项对照（ready_rev 2）", "", "输入目录固定于父修订 `" + inputs["source_revision"] + "`。预期来自 ticket ready_rev 2：三个既有数字名字修复，其余 113 个逐项不变；全部批准均为单次 accept，content/_meta 为 null，pending 为 0。", "", "| 工具 | 显式字段：前 | 显式字段：后 | 缺字段：前 | 缺字段：后 | 结论 |", "| --- | --- | --- | --- | --- | --- |"]
for old, new in zip(before["results"], after["results"]):
    tool = old["tool"]
    assert old["explicit"] == new["explicit"] == accept_once, tool
    assert new["native_message"] == accept_once, tool
    assert old["native_message"] == (pending if tool in expected_changes else accept_once), tool
    if old["native_message"] != new["native_message"]:
        changed.append(tool)
    lines.append(f"| `{tool}` | accept | accept | {'待确认' if tool in expected_changes else 'accept'} | accept | {'按修订要求修复' if tool in expected_changes else '一致'} |")
assert set(changed) == expected_changes
summary = {"status": "PASS", "tools": 116, "unchanged_tools": 113, "changed_tools": changed, "explicit_frames_unchanged": 116, "native_frames_accepted_after": 116}
with (root / "catalog-comparison-02.md").open("x", encoding="utf-8") as output:
    output.write("\n".join(lines) + "\n")
with (root / "catalog-comparison-02.json").open("x", encoding="utf-8") as output:
    output.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False))
