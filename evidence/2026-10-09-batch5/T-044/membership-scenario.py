#!/usr/bin/env python3
"""Independent inputs for membership persistence and rejection checks."""
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

root = Path(__file__).resolve().parent
label, endpoint = sys.argv[1:3]
trace = root / (label + ".jsonl")
if trace.exists():
    raise SystemExit("Evidence label already exists")
fixture = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
def request(method, path, body=None, status=200):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(endpoint + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            actual, raw = response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        actual, raw = error.code, error.read().decode("utf-8")
    with trace.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"method": method, "path": path, "input": body,
                                "status": actual, "body": raw, "expected_status": status},
                               ensure_ascii=False) + "\n")
    assert actual == status, (actual, raw, status)
    return json.loads(raw)

task = {"taskId": fixture["task"], "projectId": fixture["project"],
        "title": "分页交付", "revision": fixture["revision"],
        "members": [{"threadId": fixture["worker"], "role": "worker"},
                    {"threadId": fixture["reviewer"], "role": "reviewer"}]}
saved = request("POST", "/api/a2a/membership", {"command": "save", "task": task})
assert saved["ok"] is True and saved["task"]["revision"] == fixture["revision"] + 1
assert saved["task"]["members"] == task["members"]
notes = {"taskId": fixture["unmanaged_task"], "projectId": fixture["project"],
         "title": "审查笔记", "revision": 0, "members": []}
assert request("POST", "/api/a2a/membership", {"command": "save", "task": notes})["ok"] is True
listed = request("GET", "/api/a2a/membership?project=" + fixture["project"])
assert {item["taskId"] for item in listed["tasks"]} == {task["taskId"], notes["taskId"]}
assert request("POST", "/api/a2a/membership", {"command": "save", "task": task}, status=409)["error"] == "stale_revision"

foreign = dict(notes, taskId=notes["taskId"] + "-foreign", projectId="unknown-project")
assert request("POST", "/api/a2a/membership", {"command": "save", "task": foreign}, status=400)["error"] == "unknown_project"
unknown = dict(notes, taskId=notes["taskId"] + "-unknown", members=[{"threadId": "unknown-thread", "role": "reviewer"}])
assert request("POST", "/api/a2a/membership", {"command": "save", "task": unknown}, status=400)["error"] == "unknown_thread"
duplicate = dict(notes, taskId=notes["taskId"] + "-duplicate", members=[task["members"][0], task["members"][0]])
assert request("POST", "/api/a2a/membership", {"command": "save", "task": duplicate}, status=400)["error"] == "duplicate_member"
badOrigin = urllib.request.Request(endpoint + "/api/a2a/membership", headers={"Origin": "https://untrusted.invalid"})
try:
    with urllib.request.urlopen(badOrigin, timeout=30) as response:
        raise AssertionError("Untrusted origin was accepted: " + str(response.status))
except urllib.error.HTTPError as error:
    assert error.code == 403
    with trace.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"input": {"Origin": "https://untrusted.invalid"}, "status": error.code,
                                "body": error.read().decode("utf-8"), "expected_status": 403}) + "\n")
print("PASS membership: two tasks, role grouping, stale revision, unknown identities, duplicate member, trusted origin")
