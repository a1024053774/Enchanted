from pathlib import Path
import json, os, subprocess, sys, shutil, time
from datetime import datetime, timezone
base = Path(__file__).resolve().parent
manifest = json.loads((base / 'fixture-manifest.json').read_text())
root, state, app = (Path(manifest[k]) for k in ['root', 'state', 'app'])
assert root.parent == Path('/private/tmp') and root.name.startswith('t262-') and state.parent == root
assert manifest['revision'] == json.loads((app / 'Contents/Resources/app/package.json').read_text())['a2a']['revision']
env = {k:v for k,v in os.environ.items() if not k.startswith('A2A_')}
env['ELECTRON_RUN_AS_NODE'] = '1'
env['A2A_OPERATOR_CREDENTIAL'] = json.loads((state.with_name(state.name+'-credentials')/'desktop-connection.json').read_text())['credential']
argv = [str(app/'Contents/MacOS/Enchanted Test'),str(app/'Contents/Resources/app/src/gates/cli.ts'),'--state',str(state),'daemon_stop']
r = subprocess.run(argv,env=env,capture_output=True,text=True,timeout=30)
report = dict(time=datetime.now(timezone.utc).isoformat(),directory=str(root),daemon=dict(argv=argv,exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
assert r.returncode == 0 and json.loads(r.stdout)['ok'], report
identity = json.loads((state/'hc-runtime.json').read_text())
assert identity['session'].startswith('enchanted-') and identity['session'] != 'default'
core_env = dict(env, HC_SESSION=identity['session'],HC_SOCKET=identity['socket'],XDG_STATE_HOME=str(state/'hc/state'),XDG_CONFIG_HOME=str(state/'hc/config'))
r = subprocess.run([str(app/'Contents/Resources/app/hc/herdr-core'),'server','stop'],env=core_env,capture_output=True,text=True,timeout=20)
report['core'] = dict(identity=identity,exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
assert r.returncode == 0, report
sys.dont_write_bytecode = True
sys.path.insert(0,'/private/tmp/a2a-t262-package-20261108/workbench/tests')
from scripted_claude import fixture_processes
for i in range(20):
    remaining = fixture_processes(root)
    if not remaining: break
    time.sleep(.5)
assert not remaining, 'Owned fixture processes remain; retain directory'
files = [p for p in root.rglob('*') if p.is_file() and not p.is_symlink()]
report.update(files=len(files),bytes=sum(p.stat().st_size for p in files),processes_remaining=0)
(base/'cleanup-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.rmtree(root)
report['removed'] = not root.exists()
(base/'cleanup-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
