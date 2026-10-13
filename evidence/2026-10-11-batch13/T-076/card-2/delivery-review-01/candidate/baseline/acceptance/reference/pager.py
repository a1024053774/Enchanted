"""Contract reference for validating the oracle, never used by the product or worker."""
import json
import sys
r = json.load(sys.stdin)
limit = r.get("limit")
cursor = r.get("after")
if type(limit) is not int or not 1 <= limit <= 100:
    result = {"error": "invalid_limit"}
elif cursor is not None and (not isinstance(cursor, list) or len(cursor) != 2 or
        type(cursor[0]) is not int or not isinstance(cursor[1], str)):
    result = {"error": "invalid_cursor"}
else:
    records = sorted(r["items"], key=lambda v: (v["ts"], v["id"]))
    eligible = [v for v in records if cursor is None or (v["ts"], v["id"]) > tuple(cursor)]
    page = eligible[:limit]
    result = {"items": page, "next_cursor":
              [page[-1]["ts"], page[-1]["id"]] if len(eligible) > limit else None}
print(json.dumps(result))
