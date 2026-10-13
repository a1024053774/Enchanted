"""No-model probe: which per-session -c override clears the user's global service_tier="priority".

For each candidate override, start `codex app-server` over stdio, call initialize, config/read
(with layers) and an ephemeral thread/start (no turn is sent), and record the effective
serviceTier as reported by the CLI. Writes one JSON report; never touches ~/.codex.
"""
import json, subprocess, sys, time
from pathlib import Path

CODEX = "/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex"
out = Path(sys.argv[1])
cases = {"none": [], **{v: ["-c", f'service_tier="{v}"'] for v in ("default", "auto", "flex", "standard", "")}}
report = {"codex": subprocess.check_output([CODEX, "--version"], text=True).strip(), "cases": {}}

def rpc(proc, rid, method, params, wait=20):
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n"); proc.stdin.flush()
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line: break
        msg = json.loads(line)
        if msg.get("id") == rid: return msg
    return {"error": "no response"}

for name, extra in cases.items():
    argv = [CODEX, "app-server", "--listen", "stdio://", *extra]
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    row = {"argv": argv}
    try:
        row["initialize"] = "error" in rpc(proc, 1, "initialize", {"clientInfo": {"name": "a2a-tier-probe", "version": "1"}}) and "error" or "ok"
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialized"}) + "\n"); proc.stdin.flush()
        cfg = rpc(proc, 2, "config/read", {"includeLayers": True})
        res = cfg.get("result", {})
        row["config_read_error"] = cfg.get("error")
        row["config_service_tier"] = (res.get("config") or {}).get("service_tier", (res.get("config") or {}).get("serviceTier"))
        row["origin"] = (res.get("origins") or {}).get("service_tier")
        th = rpc(proc, 3, "thread/start", {"ephemeral": True, "model": "gpt-6.1-sol"})
        row["thread_start_error"] = th.get("error")
        r = th.get("result", {})
        row["thread_service_tier"] = r.get("serviceTier", r.get("service_tier"))
        row["thread_model"] = r.get("model")
    finally:
        proc.terminate()
        try: proc.wait(10)
        except subprocess.TimeoutExpired: proc.kill()
        row["stderr_tail"] = proc.stderr.read()[-600:]
    report["cases"][name] = row
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: {f: v.get(f) for f in ("config_service_tier", "thread_service_tier", "config_read_error", "thread_start_error")} for k, v in report["cases"].items()}, ensure_ascii=False, indent=1))
