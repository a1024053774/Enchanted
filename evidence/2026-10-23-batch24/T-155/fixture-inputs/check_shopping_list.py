import json, sys
pantry = json.load(open("pantry.json", encoding="utf-8"))
text = open("shopping-list.md", encoding="utf-8").read()
need = {it["name"] for it in pantry if it["quantity"] == 0}
others = {it["name"] for it in pantry if it["quantity"] != 0}
missing = [n for n in need if n not in text]
extra = [n for n in others if n in text]
if missing or extra:
    print(f"缺少: {missing} 多余: {extra}"); sys.exit(1)
print("shopping-list ok")
