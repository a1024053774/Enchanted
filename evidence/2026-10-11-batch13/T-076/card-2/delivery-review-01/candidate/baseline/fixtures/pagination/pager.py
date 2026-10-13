"""Deliberately faulty starter: ignores ordering and cursor; used to preserve red evidence."""
import json
import sys

request = json.load(sys.stdin)
print(json.dumps({"items": request["items"][:request["limit"]], "next_cursor": None}))
