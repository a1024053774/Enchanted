import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import uuid

out = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fixture_api", out.parents[1] / "2026-10-09-batch8/T-055/fixture-api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
root = Path(sys.argv[1])
label = sys.argv[2]
folder = out / label
folder.mkdir()
f = api.Fixture(root)
seed = json.loads((root / "seed.json").read_text(encoding="utf-8"))
counter = 0

def save(name, value):
    with (folder / (name + ".json")).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def control(operation, **args):
    result = f.control(operation, **args)
    save("control-" + str(uuid.uuid4()), dict(operation=operation, args=args, result=result))
    return result

def mcp(token, name, **args):
    global counter
    request = dict(jsonrpc="2.0", id=counter, method="tools/call", params=dict(name=name, arguments=args))
    response = f.http("/mcp", request, token)
    save("mcp-" + str(counter), dict(request=request, response=response))
    counter += 1
    return json.loads(response["result"]["content"][0]["text"])

def read():
    result = f.gate("issues", task="t057")
    assert result["ok"], result
    return result

with tempfile.TemporaryDirectory(prefix="a2a-t057-mcp-rev3-", dir="/tmp") as secrets:
    attempt = seed["dispatched"]["attempt"]
    worker = attempt["thread_id"]
    control("controlled-session", thread=worker, active=True, turn="seed-turn", workspace=attempt["workspace"])
    worker_path = Path(secrets) / "worker"
    control("token", thread=worker, path=str(worker_path))
    wt = worker_path.read_text(encoding="utf-8")
    instructions = root / "rev3-controller.txt"
    instructions.write_text("隔离协议验证；无模型调用。\n", encoding="utf-8")
    attached = f.gate("attach", task="t057", role="controller", preset="executor", modelSelection=dict(provider="codex", model="gpt-6.1-sol"), runtimeMode="full-access", instructions=str(instructions))
    save("attach", attached)
    assert attached["ok"], attached
    controller = attached["attachment"]["thread_id"]
    time.sleep(.5)
    control("controlled-session", thread=controller, active=True, turn=str(uuid.uuid4()), workspace=seed["state"]["task"]["repo"])
    controller_path = Path(secrets) / "controller"
    control("token", thread=controller, path=str(controller_path))
    token = controller_path.read_text(encoding="utf-8")
    task_before = f.gate("status", task="t057")["task"]
    raised = mcp(wt, "a2a_raise", title="七动作 MCP 独立问题 Ω", body="保留原记录。", blocking=False)
    assert raised["ok"], raised
    issue = raised["id"]
    original = next(v["issue"] for v in read()["issues"] if v["issue"]["id"] == issue)
    checks = []
    for action, state, error in [
        ("close", "已关闭", None),
        ("needs-user", "等你决定", None),
        ("forward", "已转交", None),
        ("reopen", "已转交", "user_required"),
        ("snooze", "已转交", "user_required"),
        ("dismiss", "已转交", "user_required"),
        ("delivered", "已转交", "delivery_unconfirmed"),
    ]:
        before = read()
        result = mcp(token, "a2a_disposition", task="t057", issue=issue, action=action, reason="独立需求哨兵", basis="ticket:T-057")
        after = read()
        view = next(v for v in after["issues"] if v["issue"]["id"] == issue)
        assert view["issue"] == original, view
        assert view["state"] == state, view
        if error:
            assert result["error"] == error, result
            assert after["records"] == before["records"], after
        else:
            assert result["ok"], result
            added = [r for r in after["records"] if r["id"] not in {r["id"] for r in before["records"]}]
            assert len(added) == 1 and added[0]["action"] == action and added[0]["from"] == "executor", added
        checks.append(dict(action=action, expected_state=state, expected_error=error, response=result, before=before, after=after))
    blocking = mcp(wt, "a2a_raise", title="blocking 权限反例", blocking=True)
    before = read()
    refused = mcp(token, "a2a_disposition", task="t057", issue=blocking["id"], action="close", reason="不得关闭", basis="ticket:T-057")
    assert refused["error"] == "blocking_requires_user", refused
    assert read()["records"] == before["records"]
    # User actions keep their existing local-owner HTTP entry; MCP denial
    # must not manufacture a user role or append a disposition.
    for action, state in [("reopen", "等你决定"), ("snooze", "稍后"), ("dismiss", "已关闭")]:
        before = read()
        result = f.gate("disposition", task="t057", issue=issue, action=action)
        save("user-http-" + action, result)
        assert result["ok"], result
        assert len(result["records"]) == len(before["records"]) + 1
        assert next(v for v in result["issues"] if v["issue"]["id"] == issue)["state"] == state
    reopened = f.gate("disposition", task="t057", issue=issue, action="reopen")
    assert reopened["ok"], reopened
    answered = f.gate("answer_issue", task="t057", issue=issue, answer="真实 HTTP 用户答复 Ω")
    save("answer-delivery", answered)
    assert answered["ok"], answered
    before = read()
    delivered = mcp(token, "a2a_disposition", task="t057", issue=issue, action="delivered")
    after = read()
    assert delivered["ok"], delivered
    assert len(after["records"]) == len(before["records"]) + 1
    delivered_view = next(v for v in after["issues"] if v["issue"]["id"] == issue)
    assert delivered_view["state"] == "已送达" and delivered_view["issue"] == original
    assert delivered_view["disposition"]["message_id"] == delivered_view["answer"]["message_id"]
    assert f.gate("status", task="t057")["task"] == task_before
    save("oracle", dict(status="PASS", checks=checks, confirmed_delivered=delivered, blocking_close=refused, task_unchanged=True, new_model_turns=0,
        limitation="真实 MCP/HTTP/核心与持久化；原生 provider 活跃状态受控。reopen/snooze/dismiss 用户动作经 MCP 拒绝，HTTP 用户追加成功；delivered 先拒绝未确认送达，再成功追加已确认送达。"))
print("PASS: seven MCP action calls, immutable originals, append/state checks and credential refusals; no model calls")
