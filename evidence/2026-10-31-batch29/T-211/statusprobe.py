"""T-211 第 5 项：真实 CLI 在私有 core 里经 OSC 7501 报什么状态。
用法：python3 -I statusprobe.py <socket> <out 目录> <场景,...>
每个场景打印一行 JSON：状态变化序列（相对秒数、state、kind、turn）与 reported。屏幕存到 out 目录，不打印。
"""
import json, os, re, socket, sys, time

SOCK, OUT = sys.argv[1], sys.argv[2]
A2A = "/Users/luckye/Documents/Code/a2a"
UNSET = ["/usr/bin/env", "-u", "XDG_STATE_HOME", "-u", "XDG_CONFIG_HOME"]


def call(method, params):
    s = socket.socket(socket.AF_UNIX)
    s.connect(SOCK)
    s.sendall(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode() + b"\n")
    buf = b""
    while b"\n" not in buf:
        buf += s.recv(65536)
    s.close()
    r = json.loads(buf.split(b"\n", 1)[0])
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


class Watch:
    def __init__(self, name):
        self.name, self.t0, self.seq, self.last = name, time.time(), [], None

    def poll(self):
        t = call("terminal.get", {"terminal": self.name})
        st = t.get("status") or {}
        cur = (st.get("state"), st.get("kind"), t.get("turn"), t["state"])
        if cur != self.last:
            self.seq.append([round(time.time() - self.t0, 1), *cur])
            self.last = cur
        return t

    def until(self, cond, seconds):
        end = time.time() + seconds
        while time.time() < end:
            t = self.poll()
            if cond(t):
                return t
            time.sleep(0.25)
        return None


def state(t):
    return (t.get("status") or {}).get("state")


def save_screen(name, tag):
    text = call("terminal.read", {"terminal": name, "lines": 200})["text"]
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<email>", text)  # agy prints the account email
    with open(f"{OUT}/screen-{tag}.txt", "w") as f:
        f.write(text)


def scenario(tag, argv, env, prompt, blocked_expected=False, ready_s=90, turn_s=120):
    name = "st-" + tag
    call("terminal.run", {"name": name, "argv": UNSET + argv, "cwd": A2A, "env": env})
    w = Watch(name)
    ready = w.until(lambda t: t.get("reported") and state(t) in ("idle", "done"), ready_s)
    result = {"tag": tag, "ready": bool(ready)}
    if ready:
        time.sleep(1)
        call("terminal.send", {"terminal": name, "text": prompt})
        if blocked_expected:
            got = w.until(lambda t: state(t) == "blocked", turn_s)
            result["blocked_kind"] = (got.get("status") or {}).get("kind") if got else None
            if got:
                save_screen(name, tag + "-blocked")
                call("terminal.keys", {"terminal": name, "keys": ["esc"]})
                w.until(lambda t: state(t) in ("idle", "done"), 30)
        else:
            w.until(lambda t: state(t) in ("idle", "done") and (t.get("turn") or 0) >= 1, turn_s)
    final = w.poll()
    save_screen(name, tag)
    result.update({"reported": final.get("reported"), "agent": final.get("agent"), "foreground": final.get("foreground"),
                   "app": (final.get("status") or {}).get("app"), "transitions": w.seq})
    call("terminal.kill", {"terminal": name})
    print(json.dumps(result, ensure_ascii=False), flush=True)


HAIKU = ["claude", "--model", "claude-haiku-5-5"]
SCENARIOS = {
    "claude-dontask": lambda: scenario("claude-dontask", HAIKU + ["--permission-mode", "dontAsk"], {},
                                       "Reply with exactly the word OK and nothing else."),
    "claude-default-perm": lambda: scenario("claude-default-perm", HAIKU, {},
                                            "Use the Bash tool to run exactly: touch /tmp/enc-probe-touch . Do nothing else.",
                                            blocked_expected=True),
    "claude-ask-perm": lambda: scenario("claude-ask-perm", HAIKU + ["--permission-mode", "default"], {},
                                        "Use the Bash tool to run exactly: touch /tmp/enc-probe-touch2 . Do nothing else.",
                                        blocked_expected=True),
    "agy": lambda: scenario("agy", ["agy"], {"AGY_CLI_OSC7501": "on"},
                            "Reply with exactly the word OK and nothing else. Do not use any tools.", ready_s=120, turn_s=180),
    "opencode": lambda: scenario("opencode", ["/Users/luckye/.opencode/bin/opencode", A2A], {},
                                 "Reply with exactly the word OK and nothing else. Do not use any tools.", ready_s=120, turn_s=180),
    "codex": lambda: scenario("codex", ["codex", "-c", "check_for_update_on_startup=false", "-m", "gpt-6.1-sol",
                                        "-c", "model_reasoning_effort=high"], {},
                              "Reply with exactly the word OK and nothing else. Do not run any commands.", ready_s=40, turn_s=120),
    "claude-title-empty": lambda: scenario("claude-title-empty", HAIKU + ["--permission-mode", "dontAsk"],
                                           {"CLAUDE_CODE_DISABLE_TERMINAL_TITLE": ""},
                                           "Reply with exactly the word OK and nothing else."),
    "claude-title-1": lambda: scenario("claude-title-1", HAIKU + ["--permission-mode", "dontAsk"],
                                       {"CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1"},
                                       "Reply with exactly the word OK and nothing else.", ready_s=25),
}

if __name__ == "__main__":
    for tag in sys.argv[3].split(","):
        try:
            SCENARIOS[tag]()
        except Exception as e:
            print(json.dumps({"tag": tag, "probe_error": repr(e)}), flush=True)
