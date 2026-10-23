# T-133 Codex side, probe 06: (a) a PreToolUse matcher limits the hook to the ask tool; (b) whether Esc during a
# turn sends Stop; (c) a second launch with the same hook definitions and the same CODEX_HOME asks for trust again or not.
# Isolated CODEX_HOME under /tmp (auth.json copied only); never the user's ~/.codex.
import os, pty, sys, time, select, shutil, json, re
home, work, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(home, exist_ok=True); os.makedirs(work, exist_ok=True)
shutil.copy(os.path.expanduser("~/.codex/auth.json"), os.path.join(home, "auth.json"))
open(os.path.join(home, "config.toml"), "w").write("")
marker = os.path.join(work, "hook-ran.jsonl")
command = "{ cat; echo; } >> " + marker
entry = lambda matcher: "[{" + (f"matcher={json.dumps(matcher)}," if matcher else "") + f'hooks=[{{type="command",command={json.dumps(command)},timeout=10}}]}}]'
hooks = {"UserPromptSubmit": None, "Stop": None, "PreToolUse": "request_user_input_async"}
def launch():
    argv = [shutil.which("codex"), "--no-alt-screen", "-C", work, "-a", "never", "--sandbox", "read-only", "-m", "gpt-6.1-sol",
            "-c", 'model_reasoning_effort="low"', "-c", "check_for_update_on_startup=false",
            "-c", f'projects={{{json.dumps(work)}={{trust_level="trusted"}}}}']
    for event, matcher in hooks.items(): argv += ["-c", f"hooks.{event}={entry(matcher)}"]
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(work); os.execve(argv[0], argv, {**os.environ, "CODEX_HOME": home, "TERM": "xterm-256color"})
    import fcntl, termios, struct
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 45, 160, 0, 0))
    return pid, fd
buf = b""
def pump(fd, seconds):
    global buf
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: chunk = os.read(fd, 65536)
            except OSError: return
            buf += chunk
            if b"\x1b[6n" in chunk: os.write(fd, b"\x1b[1;1R")
            if b"\x1b]10;?" in chunk: os.write(fd, b"\x1b]10;rgb:ffff/ffff/ffff\x1b\\")
            if b"\x1b]11;?" in chunk: os.write(fd, b"\x1b]11;rgb:0000/0000/0000\x1b\\")
            if b"\x1b[c" in chunk: os.write(fd, b"\x1b[?62;22c")
            if b"\x1b[?u" in chunk: os.write(fd, b"\x1b[?0u")
def text(raw):
    t = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>]', '', raw.decode('utf8', 'replace'))
    return re.sub(r'\s+', ' ', t)
pid, fd = launch(); pump(fd, 12)
first = text(buf); print("launch 1 asks for trust:", "Hooks need review" in first)
os.write(fd, b"\x1b[B"); pump(fd, 1); os.write(fd, b"\r"); pump(fd, 4)
os.write(fd, b"Run the shell command `echo hi`, then run `sleep 30`, then say done."); pump(fd, 1); os.write(fd, b"\r"); pump(fd, 15)
os.write(fd, b"\x1b"); pump(fd, 10)   # Esc while sleep runs
open(out + "-screen-1.txt", "w").write(text(buf))
os.kill(pid, 9); os.waitpid(pid, 0)
buf = b""
pid, fd = launch(); pump(fd, 12)
print("launch 2 asks for trust:", "Hooks need review" in text(buf))
open(out + "-screen-2.txt", "w").write(text(buf))
os.kill(pid, 9)
print("hooks:")
for line in (open(marker).read().splitlines() if os.path.exists(marker) else []):
    if line.strip():
        p = json.loads(line); print(p.get("hook_event_name"), p.get("tool_name"), p.get("turn_id"))
print("config.toml after:\n" + open(os.path.join(home, "config.toml")).read())
