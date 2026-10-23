import sys
lines = [l.strip() for l in open("source-notes.md", encoding="utf-8").read().splitlines()]
if "数据来源：pantry.json" not in lines:
    print("缺少精确行：数据来源：pantry.json"); sys.exit(1)
print("source-notes ok")
