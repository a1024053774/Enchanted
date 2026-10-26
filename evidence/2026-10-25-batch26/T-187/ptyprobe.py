# Drive a real CLI in a pty: start, wait, type steps, save raw output. Usage: ptyprobe.py out.raw cwd -- argv...
# Steps come from env STEPS as JSON [[wait_seconds, text], ...]; text "\r" etc. are sent verbatim.
import json, os, pty, select, sys, time
out, cwd = sys.argv[1], sys.argv[2]; argv = sys.argv[sys.argv.index('--') + 1:]
steps = json.loads(os.environ.get('STEPS', '[]'))
pid, fd = pty.fork()
if pid == 0:
    os.chdir(cwd); os.execvpe(argv[0], argv, os.environ)
import fcntl, struct, termios
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 140, 0, 0))
buf = bytearray(); marks = []
def pump(seconds):
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: data = os.read(fd, 65536)
            except OSError: return False
            if not data: return False
            buf.extend(data)
            # answer terminal queries some TUIs wait on (cursor position, device attributes)
            if b'\x1b[6n' in data: os.write(fd, b'\x1b[1;1R')
            if b'\x1b[c' in data: os.write(fd, b'\x1b[?62;22c')
    return True
for wait, text in steps:
    if not pump(wait): break
    # never answer a CLI's own trust or permission prompt with a typed key (T-187 probe-01 incident)
    if b'7501;state=blocked:kind=permission' in bytes(buf[marks[-1][0] if marks else 0:]):
        marks.append([len(buf), 'STOPPED: permission prompt']); break
    marks.append([len(buf), text]); os.write(fd, text.encode())
pump(float(os.environ.get('TAIL', '5')))
try: os.kill(pid, 9)
except OSError: pass
open(out, 'wb').write(bytes(buf)); json.dump(marks, open(out + '.marks.json', 'w'))
