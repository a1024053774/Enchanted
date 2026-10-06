#!/usr/bin/env python3
"""T-024 隔离探针；仅连接本次创建的 endpoint，默认会话只读。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
HERDR = shutil.which("herdr")
SESSION = "a2a-T-024-focus-probe"
STRIP = [key for key in os.environ if key.startswith("HERDR_")]
BASE_ENV = {key: value for key, value in os.environ.items() if key not in STRIP}
LOCK = threading.Lock()


def uint(value):
    if value < 251:
        return bytes([value])
    if value < 65536:
        return b"\xfb" + struct.pack("<H", value)
    if value < 4294967296:
        return b"\xfc" + struct.pack("<I", value)
    return b"\xfd" + struct.pack("<Q", value)


def string(value):
    data = value.encode("utf-8")
    return uint(len(data)) + data


class Decoder:
    def __init__(self, data):
        self.data, self.offset = data, 0

    def read(self, count):
        result = self.data[self.offset:self.offset + count]
        self.offset += count
        assert len(result) == count, "短帧"
        return result

    def uint(self):
        tag = self.read(1)[0]
        if tag < 251:
            return tag
        return int.from_bytes(self.read({251: 2, 252: 4, 253: 8}[tag]), "little")

    def string(self):
        return self.read(self.uint()).decode("utf-8")


class Probe:
    def __init__(self, output):
        self.output = output
        self.output.mkdir(parents=True, exist_ok=False)
        self.events = (output / "events.ndjson").open("a", encoding="utf-8")
        self.clients = []
        self.results = []
        self.env = dict(BASE_ENV)
        self.runtime = Path(tempfile.mkdtemp(prefix="a2a-T024-", dir="/tmp"))
        self.env.update(XDG_CONFIG_HOME=str(self.runtime / "c"),
                        XDG_STATE_HOME=str(self.runtime / "s"),
                        XDG_CACHE_HOME=str(self.runtime / "k"),
                        SHELL="/bin/sh", HERDR_DISABLE_SOUND="1")
        self.session_dir = self.runtime / "c/herdr/sessions" / SESSION
        self.client_socket = self.session_dir / "herdr-client.sock"
        self.api_socket = self.session_dir / "herdr.sock"
        self.server = None

    def log(self, event, **data):
        with LOCK:
            self.events.write(json.dumps({"time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                          "event": event, **data}, ensure_ascii=False) + "\n")
            self.events.flush()

    def command(self, args, default=False, required=True):
        argv = [HERDR, "--session", "default" if default else SESSION, *args]
        result = subprocess.run(argv, env=BASE_ENV if default else self.env,
                                text=True, capture_output=True, timeout=20)
        self.log("command", argv=argv, default_read_only=default,
                 stdout=result.stdout, stderr=result.stderr, returncode=result.returncode)
        if required:
            assert result.returncode == 0, result.stderr or result.stdout
        return result.stdout

    def check(self, name, actual, expected):
        okay = actual == expected
        self.results.append({"check": name, "actual": actual, "expected": expected, "pass": okay})
        self.log("check", **self.results[-1])
        assert okay, f"{name}: {actual!r} != {expected!r}"

    def default_state(self, phase):
        state = {"status": self.command(["status", "server"], default=True),
                 "controller": json.loads(self.command(["pane", "process-info", "--pane", "wF:pM"], default=True))}
        sessions = json.loads(self.command(["session", "list", "--json"], default=True))["sessions"]
        default = next(item for item in sessions if item["default"])
        pids = subprocess.run(["lsof", "-t", default["socket_path"]], capture_output=True, text=True, timeout=10)
        assert pids.returncode == 0, pids.stderr
        identities = subprocess.run(["ps", "-p", ",".join(pids.stdout.split()), "-o", "pid=,lstart=,command="],
                                    capture_output=True, text=True, check=True, timeout=10).stdout
        state["server_identity"] = identities.strip()
        (self.output / f"default-{phase}.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.log("default_state", phase=phase, **state)
        return state

    def start(self):
        config = self.runtime / "c/herdr/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text('onboarding = false\n[update]\nversion_check = false\nmanifest_check = false\n[terminal]\ndefault_shell = "/bin/sh"\n[ui]\npane_scrollbars = false\n', encoding="utf-8")
        assert not self.session_dir.exists(), "不得接管已有探针会话"
        argv = [HERDR, "--session", SESSION, "server"]
        self.log("start_server", argv=argv, removed_inherited_environment=STRIP,
                 overrides={key: self.env[key] for key in ["XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "SHELL", "HERDR_DISABLE_SOUND"]})
        self.server_log = (self.output / "server-stdio.txt").open("w", encoding="utf-8")
        self.server = subprocess.Popen(argv, env=self.env, stdin=subprocess.DEVNULL,
                                       stdout=self.server_log, stderr=subprocess.STDOUT)
        self.log("server_identity", pid=self.server.pid, session=SESSION, client_socket=str(self.client_socket))
        deadline = time.monotonic() + 10
        while not self.client_socket.exists():
            assert self.server.poll() is None, "探针 server 提前结束，见 server-stdio.txt"
            assert time.monotonic() < deadline, "探针 socket 未就绪"
            time.sleep(.05)
        self.check("probe_server_version", "version: 0.9.3" in self.command(["status", "server"]), True)

    def pane_read(self, pane):
        return self.command(["pane", "read", pane, "--source", "recent-unwrapped", "--lines", "200"])

    def wait_text(self, pane, text):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            output = self.pane_read(pane)
            if text in output.splitlines():
                return output
            time.sleep(.05)
        raise AssertionError(f"pane {pane} 未产生 {text!r}")

    def size(self, client, pane, label):
        marker = "T024_SIZE_" + label
        self.command(["pane", "run", pane, f"printf '\\n{marker}\\n'; stty size"])
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            output = self.pane_read(pane)
            lines = output.splitlines()
            for index, line in enumerate(lines):
                if line.strip() == marker and index + 1 < len(lines):
                    words = lines[index + 1].split()
                    if len(words) == 2 and all(word.isdigit() for word in words):
                        size = [int(word) for word in words]
                        self.log("stty_size", expected_viewer=client.name, pane=pane, label=label,
                                 entry_point="public CLI pane run (does not claim geometry)", rows_cols=size)
                        return size
            time.sleep(.05)
        raise AssertionError(f"{pane} 未报告 stty size")

    def stop(self):
        for client in self.clients:
            client.close()
        if self.server is not None:
            if self.server.poll() is None:
                self.command(["session", "stop", SESSION, "--json"])
                self.check("probe_server_exit", self.server.wait(timeout=10), 0)
            else:
                self.log("already_exited_probe", returncode=self.server.returncode)
            self.server_log.close()
            sessions = json.loads(self.command(["session", "list", "--json"]))["sessions"]
            self.check("probe_session_stopped", next(item for item in sessions if item["name"] == SESSION)["running"], False)
            self.check("probe_socket_removed", self.client_socket.exists() or self.api_socket.exists(), False)
        for path in self.runtime.rglob("*"):
            if path.is_file() and not path.is_symlink():
                target = self.output / "runtime" / path.relative_to(self.runtime)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        self.log("runtime_archived", original=str(self.runtime), archive=str(self.output / "runtime"))


class Client:
    def __init__(self, probe, name, cols, rows):
        self.probe, self.name = probe, name
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(str(probe.client_socket))
        self.sock.settimeout(.2)
        self.snapshot = None
        self.responses = {}
        self.welcome = None
        self.surfaces = 0
        self.error = None
        self.running = True
        self.thread = threading.Thread(target=self.receive, daemon=True)
        self.thread.start()
        probe.clients.append(self)
        hello = dict(generation=1, cell_width_px=8, cell_height_px=16,
                     surface_size=dict(cols=cols, rows=rows), pixel_mouse=False,
                     direct_graphics=False, endpoint_keybindings=False, mouse_capture=False,
                     snapshot_codecs=["shell.snapshot.v1"], surface_codecs=["shell.surface.v1"],
                     input_codecs=["shell.input.semantic.v1"], blob_codecs=["shell.blob.v1"])
        self.send(20, string("endpoint.hello.v1") + string(json.dumps(hello)), hello=hello)
        self.wait(lambda: self.welcome and self.snapshot and self.surfaces)
        probe.check(name + "_generation", self.welcome["generation"], 1)
        probe.check(name + "_endpoint_version", self.welcome["server_version"], "0.9.3")
        assert not self.welcome.get("error"), self.welcome

    def send(self, tag, data=b"", **details):
        payload = uint(tag) + data
        self.probe.log("client_send", client=self.name, tag=tag, **details)
        self.sock.sendall(struct.pack("<I", len(payload)) + payload)

    def receive(self):
        pending = bytearray()
        try:
            while self.running:
                try:
                    chunk = self.sock.recv(65536)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                pending.extend(chunk)
                while len(pending) >= 4:
                    length = struct.unpack("<I", pending[:4])[0]
                    assert 0 < length <= 2 * 1024 * 1024, length
                    if len(pending) < length + 4:
                        break
                    data = bytes(pending[4:length + 4])
                    del pending[:length + 4]
                    self.message(data)
        except Exception:
            self.error = traceback.format_exc()
            self.probe.log("client_reader_failure", client=self.name, traceback=self.error)

    def message(self, data):
        dec = Decoder(data)
        tag = dec.uint()
        details = {"client": self.name, "tag": tag, "bytes": len(data)}
        if tag == 20:
            kind, text = dec.string(), dec.string()
            value = json.loads(text)
            details.update(kind=kind, data=value)
            if kind == "endpoint.welcome.v1":
                self.welcome = value
            elif kind == "shell.snapshot.v1":
                self.snapshot = value
        elif tag == 18:
            boot, request_id = dec.string(), dec.string()
            final = bool(dec.read(1)[0])
            chunk = dec.read(dec.uint())
            buffered = self.responses.setdefault(request_id, {"chunks": b"", "final": False})
            buffered["chunks"] += chunk
            buffered["final"] = final
            details.update(boot_id=boot, request_id=request_id, final=final,
                           response=chunk.decode("utf-8"))
        elif tag == 13:
            boot, projection, revision = dec.string(), dec.uint(), dec.uint()
            symbols = []
            for _ in range(dec.uint()):
                symbols.append(dec.string())
                dec.uint(); dec.uint(); dec.uint(); dec.read(1)
                if dec.read(1)[0]:
                    dec.uint()
            cols, rows = dec.uint(), dec.uint()
            assert len(symbols) == cols * rows
            text = "\n".join("".join(symbols[row * cols:(row + 1) * cols]).rstrip() for row in range(rows)).rstrip()
            details.update(boot_id=boot, projection_revision=projection, surface_revision=revision,
                           cols=cols, rows=rows, text=text)
            self.surfaces += 1
        elif tag == 15:
            details["error"] = dec.string()
        self.probe.log("server_message", **details)

    def wait(self, condition):
        deadline = time.monotonic() + 8
        while not condition():
            assert not self.error, self.error
            assert time.monotonic() < deadline, f"客户端 {self.name} 等待超时"
            time.sleep(.02)

    def request(self, method, params):
        request_id = self.name + "-" + str(time.monotonic_ns())
        request = dict(id=request_id, method=method, params=params)
        self.send(15, string(self.snapshot["boot_id"]) + string(json.dumps(request)), request=request)
        self.wait(lambda: self.responses.get(request_id, {}).get("final"))
        response = json.loads(self.responses[request_id]["chunks"])
        assert "error" not in response, response
        return response

    def focus(self, workspace):
        self.request("workspace.focus", {"workspace_id": workspace})
        self.wait(lambda: self.snapshot["focused_workspace_id"] == workspace)

    def resize(self, cols, rows):
        self.send(12, uint(8) + uint(16) + uint(cols) + uint(rows) + b"\x00", cols=cols, rows=rows)

    def input(self, pane, text):
        paste = uint(3) + string(text)
        enter = uint(0) + uint(1) + b"\x00" + uint(0) + uint(1) + b"\x00" * 5
        self.send(13, string(pane) + uint(2) + paste + enter, pane=pane, text=text)

    def close(self):
        if self.running:
            self.send(4)
            self.running = False
            self.thread.join(timeout=2)
            self.sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert os.environ.get("HERDR_ENV") == "1", "必须在 Herdr 受管 pane 中执行"
    probe = Probe(args.output.resolve())
    before = probe.default_state("before")
    verdict = "INCOMPLETE"
    try:
        probe.start()
        a = json.loads(probe.command(["workspace", "create", "--label", "T024-project-A", "--cwd", str(probe.runtime), "--no-focus"]))["result"]
        b = json.loads(probe.command(["workspace", "create", "--label", "T024-project-B", "--cwd", str(probe.runtime), "--no-focus"]))["result"]
        wa, wb = a["workspace"]["workspace_id"], b["workspace"]["workspace_id"]
        pa, pb = a["root_pane"]["pane_id"], b["root_pane"]["pane_id"]
        left, right = Client(probe, "A", 101, 31), Client(probe, "B", 73, 19)
        left.focus(wa)
        right.focus(wb)
        probe.check("client_focus_independent", [left.snapshot["focused_workspace_id"], right.snapshot["focused_workspace_id"]], [wa, wb])
        probe.check("same_engine_boot", left.snapshot["boot_id"], right.snapshot["boot_id"])
        probe.check("different_project_geometry", [probe.size(left, pa, "initial_A"), probe.size(right, pb, "initial_B")], [[31, 101], [19, 73]])
        left.resize(119, 37)
        probe.check("resize_A_keeps_B", [probe.size(left, pa, "resize_A_A"), probe.size(right, pb, "resize_A_B")], [[37, 119], [19, 73]])
        right.resize(67, 23)
        probe.check("resize_B_keeps_A", [probe.size(left, pa, "resize_B_A"), probe.size(right, pb, "resize_B_B")], [[37, 119], [23, 67]])
        nonce = str(time.monotonic_ns())
        ma, mb = "T024_ONLY_A_" + nonce, "T024_ONLY_B_" + nonce
        left.input(pa, f"printf '{ma}\\n'")
        right.input(pb, f"printf '{mb}\\n'")
        output_a, output_b = probe.wait_text(pa, ma), probe.wait_text(pb, mb)
        probe.check("input_A_exclusive", [ma in output_a, ma in output_b], [True, False])
        probe.check("input_B_exclusive", [mb in output_a, mb in output_b], [False, True])
        foreign = "T024_REJECT_FOREIGN_" + nonce
        left.input(pb, f"printf '{foreign}\\n'")
        barrier = "T024_BARRIER_" + nonce
        left.focus(wa)
        right.input(pb, f"printf '{barrier}\\n'")
        output_b = probe.wait_text(pb, barrier)
        probe.check("foreign_pane_input_rejected", foreign in output_b, False)
        third = left.request("tab.create", {"workspace_id": wa, "label": "T024-task-A2", "focus": True})["result"]
        left.wait(lambda: left.snapshot["focused_tab_id"] == third["tab"]["tab_id"])
        probe.check("A_task_navigation_keeps_B_project", right.snapshot["focused_workspace_id"], wb)
        # 负面对照：公开 CLI focus 的契约是会话级广播，独立焦点断言必须拒绝它。
        probe.command(["workspace", "focus", wa])
        right.wait(lambda: right.snapshot["focused_workspace_id"] == wa)
        actual = [left.snapshot["focused_workspace_id"], right.snapshot["focused_workspace_id"]]
        independent = actual == [wa, wb]
        probe.log("negative_control", operation="public CLI workspace focus", actual=actual,
                  independent_focus_oracle_accepts=independent, expected_independent=[wa, wb])
        probe.check("global_focus_counterexample_rejected", independent, False)
        left.focus(wa)
        right.focus(wb)
        # 同一标签页共享 PTY；用户输入迁移该标签页的尺寸控制权。
        right.focus(wa)
        pc = third["root_pane"]["pane_id"]
        left.request("tab.focus", {"tab_id": third["tab"]["tab_id"]})
        right.request("tab.focus", {"tab_id": third["tab"]["tab_id"]})
        probe.check("same_tab_B_geometry", probe.size(right, pc, "same_tab_B"), [23, 67])
        activity = "T024_A_CLAIM_" + nonce
        left.input(pc, f"printf '{activity}\\n'")
        probe.wait_text(pc, activity)
        probe.check("same_tab_A_activity_claims_geometry", probe.size(left, pc, "same_tab_A"), [37, 119])
        right.focus(wb)
        probe.check("restore_separate_projects", [left.snapshot["focused_workspace_id"], right.snapshot["focused_workspace_id"]], [wa, wb])
        probe.check("restored_B_geometry", probe.size(right, pb, "restored_B"), [23, 67])
        for pane in [pa, pb, pc]:
            (probe.output / (pane.replace(":", "-") + "-read.txt")).write_text(probe.pane_read(pane), encoding="utf-8")
        right.close()
        probe.check("survivor_client_focus", left.snapshot["focused_workspace_id"], wa)
        # 只剩一个活跃客户端时 resize 会作用于全部标签页，包括无人查看的项目。
        left.resize(113, 29)
        probe.check("survivor_size", probe.size(left, pc, "survivor"), [29, 113])
        probe.check("single_client_resizes_background_project", probe.size(right, pb, "background_after_detach"), [29, 113])
        output_b = probe.pane_read(pb)
        (probe.output / "background-after-detach-read.txt").write_text(output_b, encoding="utf-8")
        probe.check("client_readers_healthy", [client.error for client in probe.clients], [None, None])
        verdict = "PASS"
    except Exception:
        probe.log("failure", traceback=traceback.format_exc())
        print(traceback.format_exc(), flush=True)
    finally:
        try:
            probe.stop()
        except Exception:
            verdict = "INCOMPLETE"
            probe.log("cleanup_failure", traceback=traceback.format_exc())
            print(traceback.format_exc(), flush=True)
        try:
            after = probe.default_state("after")
            probe.check("default_server_identity_preserved", after["server_identity"], before["server_identity"])
            probe.check("default_server_status_preserved", after["status"], before["status"])
            probe.check("controller_process_preserved", after["controller"], before["controller"])
        except Exception:
            verdict = "INCOMPLETE"
            probe.log("default_verification_failure", traceback=traceback.format_exc())
            print(traceback.format_exc(), flush=True)
        summary = {"status": verdict, "session": SESSION, "checks": probe.results,
                   "runtime": str(probe.runtime), "repository": str(ROOT)}
        (probe.output / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        probe.events.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
