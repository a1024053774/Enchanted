#!/usr/bin/env python3
"""只读已指定的 2.1.302 文件；不执行 CLI，不读配置或 auth。"""
import argparse
import json
import mmap
from pathlib import Path
import shutil


TARGET = Path("/Users/luckye/.local/share/claude/versions/2.1.302")
SECTIONS = [
    ("production_api", 212195700, 212197000, b'BASE_API_URL:', 75),
    ("production_oauth", 212195700, 212197000, b'TOKEN_URL:', 85),
    ("oauth_resolver", 212198000, 212199500, b'function ln()', 230),
    ("state_suffix", 212194800, 212195100, b'function V9()', 195),
    ("legacy_state_choice", 212291400, 212291900, b'function Y_()', 225),
    ("state_file_path", 212291400, 212291900, b'function B()', 115),
    ("default_theme", 214968900, 214970200, b'function Ge()', 140),
    ("state_merge", 214978000, 214978600, b'{...Ge(),...h}', 100),
    ("onboarding_gate", 237981700, 237982400, b'if(S.hasCompletedOnboarding', 345),
    ("preflight_urls", 251996150, 251996700, b'let u=ln()', 390),
    ("preflight_parallel", 251996700, 251997700, b'Promise.all(t.map(v))', 120),
    ("onboarding_factors", 251999800, 252001000, b'function $t(', 255),
    ("onboarding_preflight_step", 252001000, 252003000, b'if(o&&!h)k.push', 200),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        raise SystemExit("输出必须为已存在目录中的新文件。")
    observations = []
    with TARGET.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for name, begin, end, needle, length in SECTIONS:
            offset = data.find(needle, begin, end)
            if offset < 0 or data.find(needle, offset + 1, end) >= 0:
                raise SystemExit("指定静态片段缺失或不唯一；不推断其他版本。")
            observations.append({"id": name, "offset": offset,
                                 "excerpt": data[offset:offset + length].decode("utf-8", "strict")})
        report = {"task": "T-093", "attempt": "a1", "status": "INCOMPLETE", "date": "2026-10-17",
                  "scope": "静态片段及其范围；不证明实际启动或所有网络路径", "target": str(TARGET),
                  "bytes": len(data), "mtime_ns": TARGET.stat().st_mtime_ns, "version_selected": "2.1.302",
                  "rea_cli_available": shutil.which("rea") is not None,
                  "target_executed": False, "real_auth_read": False, "observations": observations}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "sections": len(observations), "target_executed": False}))


if __name__ == "__main__":
    main()
