"""Launch the reviewed package against only Terra v4 fixture state; save formal process identity first."""
from pathlib import Path
import json, os, subprocess, sys, time
from datetime import datetime, timezone
base=Path(__file__).resolve().parent
app=Path(sys.argv[1]); candidate=sys.argv[2]
root=Path('/private/tmp/t249-terra-20261108-04')
state=root/'state'
assert root.is_dir() and (state/'worktrees/terra/readonly/.git').is_file()
package=json.loads((app/'Contents/Resources/app/package.json').read_text())
assert package['a2a']['revision']==candidate and package['productName']=='Enchanted Test'
assert not (base/'terra-v4-launch.json').exists()
formal=[]
for pid in [37923,38234,42545,99586]:
    r=subprocess.run(['/bin/ps','-p',str(pid),'-o','pid=,ppid=,lstart=,comm='],capture_output=True,text=True)
    assert r.returncode==0 and r.stdout.strip(), 'Formal identity must be re-established before launch'
    formal.append(r.stdout.strip())
(base/'terra-v4-formal-processes-before.json').write_text(json.dumps(dict(time=datetime.now(timezone.utc).isoformat(),rows=formal),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('A2A_') and k!='ELECTRON_RUN_AS_NODE'}
argv=[str(app/'Contents/MacOS/Enchanted Test'),'--state',str(state),'--user-data',str(root/'ui')]
with (root/'gui.log').open('x') as log:
    p=subprocess.Popen(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
report=dict(candidate=candidate,app=str(app),root=str(root),state=str(state),argv=argv,pid=p.pid,status='STARTING')
(base/'terra-v4-launch.json').write_text(json.dumps(report,indent=2)+'\n')
deadline=time.monotonic()+45
while time.monotonic()<deadline and p.poll() is None and not (state.with_name('state-credentials')/'desktop-connection.json').exists():
    time.sleep(.2)
report['status']='BACKEND_DESCRIPTOR_READY' if (state.with_name('state-credentials')/'desktop-connection.json').exists() and p.poll() is None else 'INCOMPLETE'
(base/'terra-v4-launch.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert report['status']=='BACKEND_DESCRIPTOR_READY'
