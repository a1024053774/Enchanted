import json, re, sys
pantry = json.load(open("pantry.json", encoding="utf-8"))
text = open("pantry-summary.md", encoding="utf-8").read()
cats = {}
for it in pantry:
    k, q = cats.get(it["category"], (0, 0))
    cats[it["category"]] = (k + 1, q + it["quantity"])
total_kinds = len(pantry)
total_qty = sum(it["quantity"] for it in pantry)
errors = []
for cat, (k, q) in cats.items():
    lines = [l for l in text.splitlines() if cat in l]
    if not any(str(k) in l and str(q) in l for l in lines):
        errors.append(f"类别 {cat} 缺少种类数 {k} 与件数 {q} 同行")
if not any("总计" in l and str(total_kinds) in l and str(total_qty) in l for l in text.splitlines()):
    errors.append(f"缺少总计行：种类 {total_kinds}，件数 {total_qty}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("pantry-summary ok")
