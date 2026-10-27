import os, pty, sys, time, select, re
cwd, out, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
pid, fd = pty.fork()
if pid == 0:
    os.chdir(cwd); os.environ['TERM'] = 'xterm-256color'
    os.execvp('agy', ['agy', *extra])
buf = b''
def pump(sec):
    global buf
    end = time.time() + sec
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], .3)
        if r:
            try: buf += os.read(fd, 65536)
            except OSError: return
pump(12)
if b'trust' in buf.lower(): os.write(fd, b'\r'); pump(8)
os.write(fd, 'Call the MCP tool whoami of server enchanted and print its raw result. If no such tool exists, say NO_TOOL.'.encode()); time.sleep(1.5); os.write(fd, b'\r')
pump(90)
os.write(fd, b'\x03'); time.sleep(.5); os.write(fd, b'\x03'); pump(2)
text = re.sub(r'[\w.+-]+@[\w-]+(\.[\w-]+)+', '<email>', buf.decode('utf-8', 'replace'))
open(out, 'w').write(text)
