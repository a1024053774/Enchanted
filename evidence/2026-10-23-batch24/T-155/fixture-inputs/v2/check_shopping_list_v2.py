import json, re, sys
# 需求：只列库存为 0 的食材，且列表项必须为“- 食材名”；不得出现否定语义（如“无需购买”）或列表外的食材名。
pantry = json.load(open("pantry.json", encoding="utf-8"))
zero = [it["name"] for it in pantry if it["quantity"] == 0]
all_names = [it["name"] for it in pantry]
text = open("shopping-list.md", encoding="utf-8").read()
lines = text.splitlines()
errors = []
items = [m.group(1) for l in lines if (m := re.fullmatch(r"\s*[-*]\s+(.+?)\s*", l))]
if sorted(items) != sorted(zero):
    errors.append(f"列表项应为 {sorted(zero)}，实际 {sorted(items)}")
for l in lines:
    if re.fullmatch(r"\s*[-*]\s+.+", l):
        continue
    for n in all_names:
        if n in l:
            errors.append(f"列表外出现食材名 {n}：{l}")
for neg in ["无需", "不需要", "不用", "不要", "不买", "不缺", "没有", "并非"]:
    if neg in text:
        errors.append(f"出现否定语义“{neg}”")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("shopping-list v2 ok")
