import json, re, sys
# 需求：每类一行“- 类别：种类 N，件数 M”；文末一行“总计：种类 N，件数 M”；种类与件数由 pantry.json 逐条计算。
pantry = json.load(open("pantry.json", encoding="utf-8"))
expected = {}
for it in pantry:
    k, q = expected.get(it["category"], (0, 0))
    expected[it["category"]] = (k + 1, q + it["quantity"])
total = (len(pantry), sum(it["quantity"] for it in pantry))
lines = open("pantry-summary.md", encoding="utf-8").read().splitlines()
errors = []
bullets = [l for l in lines if l.startswith("- ")]
for cat, (k, q) in expected.items():
    hits = [l for l in bullets if l.startswith(f"- {cat}：")]
    if len(hits) != 1:
        errors.append(f"类别 {cat} 应恰好一行，实际 {len(hits)} 行")
        continue
    m = re.fullmatch(r"- " + re.escape(cat) + r"：种类 (\d+)，件数 (\d+)", hits[0])
    if not m or (int(m.group(1)), int(m.group(2))) != (k, q):
        errors.append(f"类别 {cat} 应为 种类 {k}，件数 {q}，实际行：{hits[0]}")
for b in bullets:
    if not any(b.startswith(f"- {c}：") for c in expected):
        errors.append(f"多余的类别行：{b}")
totals = [l for l in lines if l.startswith("总计")]
nonempty = [l for l in lines if l.strip()]
if len(totals) != 1:
    errors.append(f"总计行应恰好一行，实际 {len(totals)} 行")
elif nonempty[-1] != totals[0]:
    errors.append("总计行不在文末")
else:
    m = re.fullmatch(r"总计：种类 (\d+)，件数 (\d+)", totals[0])
    if not m or (int(m.group(1)), int(m.group(2))) != total:
        errors.append(f"总计应为 种类 {total[0]}，件数 {total[1]}，实际：{totals[0]}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("pantry-summary v2 ok")
