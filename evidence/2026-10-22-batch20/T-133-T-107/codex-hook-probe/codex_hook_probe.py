# T-133 probe: does a hook passed with -c (no bypass) run in Codex, prompt for trust, and where is trust saved?
# Runs Codex with an isolated CODEX_HOME under /tmp (auth.json copied only), never the user's ~/.codex.
import os, pty, sys, time, select, shutil, subprocess, json, re
home = sys.argv[1]; work = sys.argv[2]; out = sys.argv[3]; accept = sys.argv[4] == "accept"
os.makedirs(home, exist_ok=True); os.makedirs(work, exist_ok=True)
shutil.copy(os.path.expanduser("~/.codex/auth.json"), os.path.join(home, "auth.json"))
open(os.path.join(home, "config.toml"), "w").write("")
marker = os.path.join(work, "hook-ran.jsonl")
hook = f'[{{hooks=[{{type="command",command={json.dumps("cat >> " + marker)},timeout=10}}]}}]'
argv = [shutil.which("codex"), "--no-alt-screen", "-C", work, "-a", "never", "--sandbox", "read-only", "-m", "gpt-6.1-sol",
        "-c", 'model_reasoning_effort="low"', "-c", "check_for_update_on_startup=false",
        "-c", f'projects={{{json.dumps(work)}={{trust_level="trusted"}}}}', "-c", f"hooks.UserPromptSubmit={hook}"]
env = {**os.environ, "CODEX_HOME": home, "TERM": "xterm-256color"}
pid, fd = pty.fork()
if pid == 0:
    os.chdir(work); os.execve(argv[0], argv, env)
import fcntl, termios, struct
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 45, 160, 0, 0))
buf = b""
def pump(seconds):
    global buf
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: chunk = os.read(fd, 65536)
            except OSError: return
            buf += chunk
            # Answer the terminal queries Codex waits on (cursor position, colors, device attributes, kitty keyboard).
            if b"\x1b[6n" in chunk: os.write(fd, b"\x1b[1;1R")
            if b"\x1b]10;?" in chunk: os.write(fd, b"\x1b]10;rgb:ffff/ffff/ffff\x1b\\")
            if b"\x1b]11;?" in chunk: os.write(fd, b"\x1b]11;rgb:0000/0000/0000\x1b\\")
            if b"\x1b[c" in chunk: os.write(fd, b"\x1b[?62;22c")
            if b"\x1b[?u" in chunk: os.write(fd, b"\x1b[?0u")
pump(12)
open(out + "-screen-1.txt", "wb").write(buf)
if accept:
    os.write(fd, b"\x1b[B"); pump(1); os.write(fd, b"\r"); pump(4)
os.write(fd, b"say only the word ok"); pump(1); os.write(fd, b"\r"); pump(25)
open(out + "-screen-2.txt", "wb").write(buf)
os.kill(pid, 9)
print("hook_ran:", os.path.exists(marker))
print("config.toml after:\n" + open(os.path.join(home, "config.toml")).read())
