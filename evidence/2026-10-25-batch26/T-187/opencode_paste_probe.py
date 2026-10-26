"""Real opencode in a PTY: when does a bracketed paste written after the first OSC 7501 idle land in the input box?
argv: delay_seconds out_file. Writes a paste 'reply with exactly PROBEWORD' + Enter after first idle + delay; records
whether a working report follows within 20 s."""
import os, pty, re, select, signal, struct, fcntl, termios, time, sys, tempfile, subprocess
delay, out_path = float(sys.argv[1]), sys.argv[2]
cursor = len(sys.argv) > 3  # paste at the first cursor-show after idle instead of after a delay
work = tempfile.mkdtemp(prefix='ocprobe-', dir='/private/tmp'); subprocess.run(['git', 'init', '-q', work], check=True)
pid, fd = pty.fork()
if pid == 0:
    os.chdir(work); env = dict(os.environ, TERM='xterm-256color', OPENCODE_CONFIG_CONTENT='{"model":"opencode/big-pickle"}')
    os.execve('/Users/luckye/.opencode/bin/opencode', ['opencode', '--standalone', '--auto', work], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 140, 0, 0))
out, t0, idle_at, sent_at, verdict = b'', time.time(), None, None, 'no_idle'
def reports(): return re.findall(rb'\x1b\]7501;([^\x07\x1b]*)', out)
while time.time() - t0 < 120:
    r, _, _ = select.select([fd], [], [], .1)
    if r:
        try: chunk = os.read(fd, 65536)
        except OSError: break
        out += chunk
        if b'\x1b[6n' in chunk: os.write(fd, b'\x1b[1;1R')
    if idle_at is None and any(x.startswith(b'state=idle') for x in reports()): idle_at = time.time()
    ready = (b'\x1b[?25h' in out[out.find(b'state=idle'):]) if cursor else (time.time() - idle_at >= delay if idle_at else False)
    if idle_at and sent_at is None and ready:
        mark = len(reports()); os.write(fd, b'\x1b[200~reply with exactly PROBEWORD\x1b[201~'); time.sleep(.3); os.write(fd, b'\r'); sent_at = time.time()
    if sent_at:
        if any(x.startswith(b'state=working') for x in reports()[mark:]): verdict = 'working'; break
        if time.time() - sent_at > 20: verdict = 'no_working_20s'; break
os.kill(pid, signal.SIGKILL); os.waitpid(pid, 0)
open(out_path, 'wb').write(out)
print(dict(cursor=cursor, gap=round(sent_at - idle_at, 2) if sent_at and idle_at else None, delay=delay, verdict=verdict, idle_after=round(idle_at - t0, 2) if idle_at else None, reports=[x[:30] for x in reports()][:8]))
subprocess.run(['rm', '-rf', work])
