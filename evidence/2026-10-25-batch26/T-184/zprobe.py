import os, pty, sys, time, select
T = sys.argv[1]
env = dict(HOME=os.environ['HOME'], USER=os.environ['USER'], TERM='xterm-256color', SHELL='/bin/zsh', LANG='en_US.UTF-8',
           PATH='/usr/bin:/bin:/usr/sbin:/sbin', ZDOTDIR=T+'/zdotdir', A2A_TERMINAL_ZDOTDIR=T+'/zdotdir',
           A2A_TERMINAL_BIN=T+'/bin', A2A_TERMINAL_PLUGIN=T+'/plugin/enchanted-a2a')
pid, fd = pty.fork()
if pid == 0:
    os.execve('/bin/zsh', ['/bin/zsh', '-l', '-i'], env)
out = b''
def pump(t):
    global out
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: out += os.read(fd, 65536)
            except OSError: return
pump(6)
os.write(fd, b'print -r -- MARK; whence -a claude; print -r -- "hash=${commands[claude]}"; alias claude; whence -w claude; print -r -- ENDMARK\r')
pump(8)
os.write(fd, b'exit\r'); pump(1)
s = out.decode('utf-8', 'replace')
import re; s = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07", "", s); print("\n".join(l for l in s.splitlines() if re.search(r"claude|hash=|MARK|alias|not found", l))[-2000:])
