"""Stop only the dev process tree whose recorded root and current argv are checked."""
import json, os, signal, subprocess, sys, time
from pathlib import Path
here=Path(__file__).resolve().parent
label=sys.argv[1]
start=json.loads((here/f'start-{label}.json').read_text())
root=start['pid']
ps=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True)
rows={int(parts[0]):parts for line in ps.splitlines()[1:] if len(parts:=line.split(None,3))==4}
assert root in rows and rows[root][3]=='bun run dev',rows.get(root)
owned={root}
while True:
    expanded=owned|{pid for pid,row in rows.items() if int(row[1]) in owned}
    if expanded==owned: break
    owned=expanded
record={'time':time.time(),'root':root,'processes':[rows[pid] for pid in sorted(owned)],'signal':'SIGTERM'}
with (here/f'stop-{label}-tree.json').open('x') as stream: json.dump(record,stream,indent=2);stream.write('\n')
for pid in sorted(owned,reverse=True):
    current=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout.strip()
    if current==rows[pid][3]:
        try: os.kill(pid,signal.SIGTERM)
        except ProcessLookupError: pass
print('Stopped checked T-044 dev tree:', sorted(owned))
