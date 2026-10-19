#!/usr/bin/env python3
"""只读已指定的 2.1.302，记录信任字段及路径语义；不执行 CLI 或读取 auth。"""
import argparse
import json
import mmap
from pathlib import Path


TARGET = Path("/Users/luckye/.local/share/claude/versions/2.1.302")
SECTIONS = [
    ("trust_getter", 214971300, 214971600, b'function FWe(', 125),
    ("trust_key", 214971400, 214971800, b'function yR(', 95),
    ("trust_setter", 214975100, 214975600, b'function jm(', 200),
    ("trust_exact_lookup", 214974900, 214975300, b'function dNr(', 150),
    ("trust_parent_walk", 214974600, 214974950, b'function Wm(', 235),
    ("trust_repo_boundary", 214974200, 214974700, b'function Km(', 245),
    ("project_state_key", 215006900, 215007500, b'function $We(', 235),
    ("path_normalize_import", 213025700, 213030600, b'normalize as c', 100),
    ("path_normalize", 213030400, 213030800, b'function Xz(', 100),
    ("unicode_normalize", 211881400, 211881900, b'function $n(', 60),
    ("canonical_repo_key", 213337100, 213337500, b'function Jv(', 60),
    ("canonical_repo_root", 213262600, 213263000, b'function uN(', 90),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        raise SystemExit("输出必须是已有目录中的新文件。")
    observations = []
    with TARGET.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for name, begin, end, needle, length in SECTIONS:
            offset = data.find(needle, begin, end)
            if offset < 0 or data.find(needle, offset + 1, end) >= 0:
                raise SystemExit("指定片段缺失或不唯一，停止。")
            observations.append({"id": name, "offset": offset,
                                 "excerpt": data[offset:offset + length].decode("utf-8", "strict")})
        result = {"task": "T-093", "attempt": "a1", "status": "INCOMPLETE", "target": str(TARGET),
                  "bytes": len(data), "mtime_ns": TARGET.stat().st_mtime_ns, "version_selected": "2.1.302",
                  "target_executed": False, "real_auth_read": False, "observations": observations}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "sections": len(observations), "target_executed": False}))


if __name__ == "__main__":
    main()
