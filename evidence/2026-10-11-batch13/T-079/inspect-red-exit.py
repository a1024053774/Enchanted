#!/usr/bin/env python3
"""Extract only the executor's T-079 red invocation and its tool result."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) == 3 and sys.argv[1] == "--reproduce":
    with tempfile.TemporaryDirectory(prefix="a2a-t079-nomatch-", dir="/tmp") as directory:
        argv = ["zsh", "-f", "-c", 'ls "$1"/a2a-t079-codex-home-* 2>/dev/null', "t079-proof", directory]
        result = subprocess.run(argv, capture_output=True, text=True)
        with Path(sys.argv[2]).open("x", encoding="utf-8") as output:
            json.dump(dict(argv=argv, exit_code=result.returncode, stdout=result.stdout,
                           stderr=result.stderr, only_owned_empty_directory=True),
                      output, ensure_ascii=False, indent=2)
            output.write("\n")
    print(sys.argv[2])
    sys.exit(0 if result.returncode == 1 else 1)

source = Path("/Users/luckye/.claude/projects/-Users-luckye-Documents-Code-a2a/9a64ed90-d8e7-497a-803e-3ecdbc8fd69e.jsonl")
tool_id = "toolu_01Nui53e8UnP39Ys9B4Qr8nk"
selected = []
with source.open(encoding="utf-8") as stream:
    for number, line in enumerate(stream, 1):
        row = json.loads(line)
        content = row.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for part in content:
            if ((part.get("type") == "tool_use" and part.get("id") == tool_id)
                    or (part.get("type") == "tool_result" and part.get("tool_use_id") == tool_id)):
                selected.append(dict(source=str(source), line=number,
                                     timestamp=row.get("timestamp"), content=part))
if len(selected) != 2:
    raise SystemExit("调用与返回记录不完整，停止，不推断退出原因")
with Path(sys.argv[1]).open("x", encoding="utf-8") as output:
    json.dump(selected, output, ensure_ascii=False, indent=2)
    output.write("\n")
print(sys.argv[1])
