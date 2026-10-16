#!/usr/bin/env python3
"""Check only the document corrections requested by the controller after audit 01."""

import json
from pathlib import Path
import re
import subprocess
import sys


root = Path(__file__).resolve().parents[4]
generated = subprocess.run(
    ["python3", "-B", "findings/generate_t087_graph.py"],
    cwd=root, text=True, capture_output=True, check=True,
).stdout
points = {}
edges = {}
for line in generated.splitlines():
    cells = [cell.strip() for cell in line.split("|")[1:-1]]
    if len(cells) == 4 and re.fullmatch(r"[ALHQR]\d+", cells[0]):
        points[cells[0]] = cells
    if len(cells) == 5 and re.fullmatch(r"[EI]\d+", cells[0]) and " → " in cells[1]:
        edges[cells[0]] = cells

checks = []


def record(name, passed):
    checks.append({"check": name, "status": "PASS" if passed else "NO_GO"})


quality = [ident for ident, cells in points.items() if "checkQualityEvidence" in cells[1]]
record("P2-01：质量证据核对为显式步骤", len(quality) == 1)
quality_id = quality[0] if len(quality) == 1 else "missing"
pairs = {cells[1] for cells in edges.values()}
record("P2-01：红态→规则→质量证据核对→尾注", all(pair in pairs for pair in (
    "Q5 → Q6", "Q6 → " + quality_id, quality_id + " → Q7",
)))
for ident in ("Q5", "Q6", quality_id):
    exits = [cells for cells in edges.values() if cells[1] == ident + " → R2"]
    record("P2-01：" + ident + " 的未知结果暂停且不增加打回计数", any(
        "verification_unknown" in " ".join(cells[2:4]) and
        "paused" in cells[3] and "不增加 delivery_rejected" in cells[3]
        for cells in exits
    ))

protocol_exits = [cells for cells in edges.values() if cells[1] == "Q8 → R2"]
record("P2-02：协议失败独立暂停且不增加打回计数", any(
    "review_protocol_failed" in cells[3] and "paused" in cells[3] and
    "不增加 delivery_rejected" in cells[3]
    for cells in protocol_exits
))
business = edges.get("E46", ["", "", "", "", ""])
record("P2-02：E46 仅有效需修复业务结论", business[1] == "Q8 → R1" and
       "有效" in business[2] and "需修复" in business[2] and "已知失败" not in business[2])
record("P2-02：拒收码表有 invalid_review_result", "`invalid_review_result`" in generated)
trailer = " ".join(points.get("Q7", []))
record("P3-01：尾注说明 unknown 模型例外", "unknown" in trailer and
       "不要求" in trailer and "交付模型" in trailer and "非空" in trailer)

result = {"status": "PASS" if all(check["status"] == "PASS" for check in checks) else "NO_GO",
          "scope": "主控 #3 所列文档修订的定向信号；不是独立来源语义抽查", "checks": checks}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result["status"] == "PASS" else 1)
