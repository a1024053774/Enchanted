# T-133 Codex side, probe 04: which hook events Codex 0.163 sends, their payload fields, whether the hook's
# session_id equals CODEX_THREAD_ID seen by the model's shell commands, and what the ask-the-user tool looks like.
# Isolated CODEX_HOME under /tmp (auth.json copied only); never the user's ~/.codex.
import os, pty, sys, time, select, shutil, json
home, work, out = sys.argv[1], sys.argv[2], sys.argv[3]
events = sys.argv[4].split(",")
os.makedirs(home, exist_ok=True); os.makedirs(work, exist_ok=True)
shutil.copy(os.path.expanduser("~/.codex/auth.json"), os.path.join(home, "auth.json"))
open(os.path.join(home, "config.toml"), "w").write("")
marker = os.path.join(work, "hook-ran.jsonl")
command = "{ printf '{\"hook_env_thread\":\"%s\"}\\n' \"$CODEX_THREAD_ID\"; cat; echo; } >> " + marker
hook = f'[{{hooks=[{{type="command",command={json.dumps(command)},timeout=10}}]}}]'
argv = [shutil.which("codex"), "--no-alt-screen", "-C", work, "-a", "never", "--sandbox", "read-only", "-m", "gpt-6.1-sol",
        "-c", 'model_reasoning_effort="low"', "-c", "check_for_update_on_startup=false",
        "-c", f'projects={{{json.dumps(work)}={{trust_level="trusted"}}}}']
for event in events: argv += ["-c", f"hooks.{event}={hook}"]
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
            if b"\x1b[6n" in chunk: os.write(fd, b"\x1b[1;1R")
            if b"\x1b]10;?" in chunk: os.write(fd, b"\x1b]10;rgb:ffff/ffff/ffff\x1b\\")
            if b"\x1b]11;?" in chunk: os.write(fd, b"\x1b]11;rgb:0000/0000/0000\x1b\\")
            if b"\x1b[c" in chunk: os.write(fd, b"\x1b[?62;22c")
            if b"\x1b[?u" in chunk: os.write(fd, b"\x1b[?0u")
def send(text, wait):
    os.write(fd, text.encode()); pump(1); os.write(fd, b"\r"); pump(wait)
pump(12)
open(out + "-screen-1.txt", "wb").write(buf)
os.write(fd, b"\x1b[B"); pump(1); os.write(fd, b"\r"); pump(4)   # Trust all and continue
send("Run the shell command `echo THREAD=$CODEX_THREAD_ID` and reply with its output only.", 30)
send("Use your tool for asking the user a question (request_user_input) to ask me: red or blue? Offer the two options. Then reply with my choice only.", 30)
open(out + "-screen-2.txt", "wb").write(buf)
os.write(fd, b"\r"); pump(25)   # pick the first option if a question is shown
open(out + "-screen-3.txt", "wb").write(buf)
os.kill(pid, 9)
print("hooks:\n" + (open(marker).read() if os.path.exists(marker) else "(none)"))
print("config.toml after:\n" + open(os.path.join(home, "config.toml")).read())
