# Time open() of each path in a child process; prints ok/err and seconds. Usage: openprobe.py OUT PATH...
import json, os, subprocess, sys, time
out, paths = sys.argv[1], sys.argv[2:]
rows = []
for p in paths:
    t = time.time()
    try:
        r = subprocess.run([sys.executable, '-c', 'import sys; open(sys.argv[1],"rb").read(1)', p], capture_output=True, text=True, timeout=12)
        res = 'ok' if r.returncode == 0 else r.stderr.strip().splitlines()[-1]
    except subprocess.TimeoutExpired:
        res = 'timeout'
    rows.append({'path': p, 'result': res, 'seconds': round(time.time() - t, 3)})
    print(rows[-1], flush=True)
json.dump({'pid': os.getpid(), 'ppid': os.getppid(), 'rows': rows}, open(out, 'w'), ensure_ascii=False, indent=1)
