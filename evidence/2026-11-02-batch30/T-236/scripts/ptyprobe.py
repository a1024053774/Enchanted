import os, pty, select, sys, time, re, struct, fcntl, termios
argv=sys.argv[2:]; secs=float(sys.argv[1])
pid,fd=pty.fork()
if pid==0:
    os.chdir('/private/tmp/a2a-cu/project'); os.environ['TERM']='xterm-256color'
    os.execv(argv[0],argv)
fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',int(os.environ.get('R','40')),int(os.environ.get('C','120')),0,0))
buf=b''; end=time.time()+secs
while time.time()<end:
    r,_,_=select.select([fd],[],[],0.2)
    if r:
        try: d=os.read(fd,65536)
        except OSError: break
        buf+=d
os.kill(pid,9)
print(len(buf)); print(repr(buf[:3000]))
