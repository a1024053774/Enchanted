"""T-211 hc 事实探针。用法：python3 -I hcprobe.py <hc 二进制> <scratch 目录> <runtime 目录> <项目>

每一项打印 JSON 一行：{"item": ..., "observed": ...}。只记观察到的事实，不下结论。
后台起的 core 用独立 HC_SESSION、XDG_STATE_HOME、XDG_CONFIG_HOME、XDG_RUNTIME_DIR，不碰用户自己的 core。
"""
import json, os, socket, struct, subprocess, sys, time

HC, SCRATCH, RUNTIME = sys.argv[1], sys.argv[2], sys.argv[3]
SESSION = "probe"
ENV = dict(os.environ, HC_SESSION=SESSION, XDG_STATE_HOME=f"{SCRATCH}/state",
           XDG_CONFIG_HOME=f"{SCRATCH}/config", XDG_RUNTIME_DIR=RUNTIME)
SOCK = f"{RUNTIME}/herdr-core/{SESSION}.sock"
OUT = f"{SCRATCH}/out"
os.makedirs(OUT, exist_ok=True)


def say(item, observed):
    print(json.dumps({"item": item, "observed": observed}, ensure_ascii=False), flush=True)


def hc(*args, check=True):
    r = subprocess.run([HC, *args], env=ENV, capture_output=True, text=True, timeout=120)
    if check and r.returncode != 0:
        raise RuntimeError(f"hc {args}: {r.stdout} {r.stderr}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.stdout


class Rpc:
    """Plain mode, then optional framed mode."""

    def __init__(self):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.connect(SOCK)
        self.buf = b""
        self.id = 0
        self.framed = False

    def call(self, method, params):
        self.id += 1
        msg = json.dumps({"jsonrpc": "2.0", "id": self.id, "method": method, "params": params}).encode()
        if self.framed:
            self.frame(0, 0, msg)
            while True:
                ch, kind, payload = self.read_frame()
                if ch == 0 and kind == 0:
                    reply = json.loads(payload)
                    if reply.get("id") == self.id:
                        return reply
                else:
                    self.pending.append((ch, kind, payload))
        self.s.sendall(msg + b"\n")
        while b"\n" not in self.buf:
            self.buf += self.s.recv(65536)
        line, self.buf = self.buf.split(b"\n", 1)
        return json.loads(line)

    def go_framed(self):
        r = self.call("hello", {"generation": 1, "framed": True})
        self.framed = True
        self.pending = []
        return r

    def frame(self, ch, kind, payload):
        self.s.sendall(struct.pack("<IBI", ch, kind, len(payload)) + payload)

    def read_frame(self, timeout=10):
        self.s.settimeout(timeout)
        while len(self.buf) < 9:
            self.buf += self.s.recv(65536)
        ch, kind, n = struct.unpack("<IBI", self.buf[:9])
        while len(self.buf) < 9 + n:
            self.buf += self.s.recv(65536)
        payload, self.buf = self.buf[9:9 + n], self.buf[9 + n:]
        return ch, kind, payload

    def drain(self, seconds):
        got = []
        end = time.time() + seconds
        while time.time() < end:
            try:
                got.append(self.read_frame(timeout=max(0.05, end - time.time())))
            except (socket.timeout, TimeoutError):
                break
        return got


def run(name, argv=None, line=None, **extra):
    params = {"name": name, "cwd": SCRATCH, **extra}
    if argv:
        params["argv"] = argv
    if line:
        params["line"] = line
    r = Rpc().call("terminal.run", params)
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def get(t):
    return Rpc().call("terminal.get", {"terminal": t})["result"]


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def item_env():
    out = f"{OUT}/env.txt"
    run("envdump", line=f"env > {out}; sleep 1")
    time.sleep(2)
    env = dict(l.split("=", 1) for l in open(out).read().splitlines() if "=" in l)
    say("2-env-inherited", {k: env.get(k) for k in ("A2A_LEAK", "CLAUDE_CODE_DISABLE_TERMINAL_TITLE", "HC_SESSION", "HC_TERMINAL_ID", "HC_SCOPE", "TERM", "XDG_STATE_HOME")})
    out2 = f"{OUT}/env2.txt"
    run("envdump2", line=f"env > {out2}; sleep 1", env={"A2A_LEAK": "", "EXTRA": "x"})
    time.sleep(2)
    env2 = dict(l.split("=", 1) for l in open(out2).read().splitlines() if "=" in l)
    say("2-env-override-empty", {"A2A_LEAK_present": "A2A_LEAK" in env2, "A2A_LEAK": env2.get("A2A_LEAK"), "EXTRA": env2.get("EXTRA")})


def item_survival():
    t = run("ticker", line="i=0; while :; do echo tick $i; i=$((i+1)); sleep 1; done")
    time.sleep(2)
    pid = get(t["address"])["pid"]
    status = hc("server", "status", "--json")
    core_pid = status["pid"]
    hc("server", "restart", "--json")
    time.sleep(2)
    after_restart = {"program_alive": alive(pid), "core_pid_changed": hc("server", "status", "--json")["pid"] != core_pid}
    os.kill(hc("server", "status", "--json")["pid"], 9)
    time.sleep(3)
    st = hc("server", "status", "--json", check=False)
    after_kill = {"program_alive": alive(pid), "core_status_after_kill9": st if isinstance(st, dict) else str(st)[:200]}
    time.sleep(2)
    rec = get("ticker")
    screen = hc("read", "ticker", "--lines", "3")
    say("3-survival", {"after_server_restart": after_restart, "after_core_kill9": after_kill,
                        "record_state": rec["state"], "same_pid": rec["pid"] == pid, "screen_tail": str(screen).strip().splitlines()[-2:]})


def item_input():
    out = f"{OUT}/input.hex"
    # Raw mode: every byte reaches the program; it writes them as hex once it has N bytes.
    payload = "\x1b[200~中文 paste ok\x1b[201~\r\x1b\x03\x04x".encode()
    t = run("rawin", line=f"stty raw -echo; head -c {len(payload)} | od -An -tx1 > {out}; sleep 1")
    time.sleep(1)
    rpc = Rpc()
    rpc.go_framed()
    a = rpc.call("terminal.attach", {"terminal": "rawin", "cols": 100, "rows": 30})
    ch = a["result"]["channel"]
    rpc.drain(0.5)
    rpc.frame(ch, 0, payload)
    time.sleep(2)
    got = bytes.fromhex(open(out).read().replace("\n", " ").replace(" ", "")) if os.path.exists(out) else None
    say("4-input-bytes", {"sent_hex": payload.hex(), "got_hex": got.hex() if got else None, "identical": got == payload})
    # observe viewer: different size, try typing
    t2 = run("sizer", line="sleep 30")
    active = Rpc(); active.go_framed()
    ca = active.call("terminal.attach", {"terminal": "sizer", "cols": 90, "rows": 25})["result"]["channel"]
    active.drain(0.3)
    obs = Rpc(); obs.go_framed()
    r = obs.call("terminal.attach", {"terminal": "sizer", "observe": True, "cols": 40, "rows": 10})
    co = r["result"]["channel"]
    obs.drain(0.3)
    obs.frame(co, 3, struct.pack("<HH", 30, 8))
    obs.frame(co, 0, b"typed by observer")
    time.sleep(1)
    rec = get("sizer")
    say("4-observe-viewer", {"size_after_observe_resize": [rec["cols"], rec["rows"]], "observer_frames": [k for _, k, _ in obs.drain(0.5)]})


def item_notes():
    plog = f"{OUT}/parent.log"
    # A parent that reports idle (an agent that can take notes) and records what is typed into it.
    parent = run("parent", line=f"printf '\\033]7501;state=idle:app=probe-parent\\033\\\\'; stty -echo; cat -uv >> {plog}")
    time.sleep(1)
    child_line = ("printf '\\033]7501;state=working:app=probe-child\\033\\\\'; sleep 1; "
                  "printf '\\033]7501;state=blocked:kind=question:app=probe-child\\033\\\\'; sleep 3; "
                  "printf '\\033]7501;state=error:app=probe-child\\033\\\\'; sleep 3; echo child-last-line; exit 3")
    run("child", line=child_line, parent=parent["address"])
    quiet = run("quietchild", line="printf '\\033]7501;state=blocked:kind=question\\033\\\\'; sleep 3; exit 1",
                parent=parent["address"], no_notify=True)
    time.sleep(12)
    say("6-parent-notes", {"parent_received": open(plog).read() if os.path.exists(plog) else None,
                            "child_parent_field": get("child").get("parent")})
    # parent blocked: notes held?
    plog2 = f"{OUT}/parent2.log"
    p2 = run("parent2", line=f"printf '\\033]7501;state=blocked:kind=question:app=p2\\033\\\\'; stty -echo; (sleep 6; printf '\\033]7501;state=idle:app=p2\\033\\\\') & cat -uv >> {plog2}")
    time.sleep(1)
    run("child2", line="printf '\\033]7501;state=blocked:kind=permission\\033\\\\'; sleep 20", parent=p2["address"])
    time.sleep(3)
    held = open(plog2).read() if os.path.exists(plog2) else ""
    time.sleep(6)
    say("6-parent-blocked", {"while_parent_blocked": held, "after_parent_idle": open(plog2).read() if os.path.exists(plog2) else None})


def item_sweep():
    # Each variant leaves its session and is orphaned to launchd: only HC_SCOPE in its environment can find it.
    variants = {"apple_sleep": "['sleep','300']",
                "node": "['node','-e','setTimeout(()=>{},300000)']",
                "conda_python": "['/opt/miniconda3/bin/python3','-c','import time; time.sleep(300)']"}
    got = {}
    for tag, argv in variants.items():
        pidfile = f"{OUT}/detached-{tag}.pid"
        name = "sp-" + tag.replace("_", "-")
        run(name, line=(f"python3 -c \"import subprocess; p=subprocess.Popen({argv}, start_new_session=True); "
                        f"open('{pidfile}','w').write(str(p.pid))\"; sleep 300"))
        time.sleep(2)
        dpid = int(open(pidfile).read())
        before = alive(dpid)
        hc("kill", name)
        time.sleep(4)
        got[tag] = {"alive_before_kill": before, "alive_after_kill": alive(dpid), "pid": dpid}
    say("8-sweep", got)


def count_lines(text):
    import re
    nums = [int(m) for m in re.findall(r"line (\d+)", text)]
    return {"found": len(set(nums)), "min": min(nums) if nums else None, "max": max(nums) if nums else None}


def read_all(t):
    r = Rpc().call("terminal.read", {"terminal": t, "lines": 1000})["result"]
    return r["text"], r.get("complete"), r.get("why")


def attach_history(t, n):
    rpc = Rpc(); rpc.go_framed()
    ch = rpc.call("terminal.attach", {"terminal": t, "observe": True, "history": n, "cols": 100, "rows": 30})["result"]["channel"]
    data = b"".join(p for c, k, p in rpc.drain(1.5) if c == ch and k == 0)
    return count_lines(data.decode("utf-8", "replace"))


def item_history():
    run("counter", line="i=0; while [ $i -lt 200 ]; do echo line $i; i=$((i+1)); done; sleep 600")
    time.sleep(2)
    snap = {}
    text, complete, why = read_all("counter")
    snap["before"] = {**count_lines(text), "complete": complete, "why": why, "attach_history": attach_history("counter", 300)}
    hc("server", "restart", "--json")
    time.sleep(2)
    text, complete, why = read_all("counter")
    snap["after_restart"] = {**count_lines(text), "complete": complete, "why": why, "attach_history": attach_history("counter", 300)}
    os.kill(hc("server", "status", "--json")["pid"], 9)
    time.sleep(2)
    hc("server", "status", "--json", check=False)
    time.sleep(2)
    text, complete, why = read_all("counter")
    snap["after_kill9"] = {**count_lines(text), "complete": complete, "why": why, "attach_history": attach_history("counter", 300)}
    say("3-history", snap)


def item_observe():
    out = f"{OUT}/observe.txt"
    run("obsin", line=f"stty raw -echo; cat -u > {out}")
    time.sleep(1)
    active = Rpc(); active.go_framed()
    ca = active.call("terminal.attach", {"terminal": "obsin", "cols": 90, "rows": 25})["result"]["channel"]
    active.drain(0.3)
    obs = Rpc(); obs.go_framed()
    co = obs.call("terminal.attach", {"terminal": "obsin", "observe": True, "cols": 40, "rows": 10})["result"]["channel"]
    obs.drain(0.3)
    obs.frame(co, 0, b"OBS")
    obs.frame(co, 3, struct.pack("<HH", 30, 8))
    active.frame(ca, 0, b"ACT")
    time.sleep(1.5)
    rec = get("obsin")
    say("4-observe-input", {"program_got": open(out).read() if os.path.exists(out) else None, "size": [rec["cols"], rec["rows"]]})
    hc("kill", "obsin")


if __name__ == "__main__":
    for step in sys.argv[4].split(","):
        try:
            globals()[f"item_{step}"]()
        except Exception as e:  # report and continue with the next item
            say(step, {"probe_error": repr(e)})
