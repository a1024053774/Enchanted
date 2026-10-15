"""Bound 09B API reuse resolver; no network or process mutation."""
import json, shlex, subprocess, os
from pathlib import Path
from p1_processes import identity_from_ps

def process_command(pid):
    p=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,command='],capture_output=True,text=True,env={**os.environ,'LC_ALL':'C','LANG':'C'})
    return identity_from_ps(pid,p.returncode,p.stdout,p.stderr)

def resolve_reused_api(template, api_root, readiness_file, process_probe=process_command):
    ready=json.loads((Path(api_root)/'api-ready.json').read_bytes()); readiness=json.loads(Path(readiness_file).read_bytes())
    entry=next((item for item in readiness['api_processes'] if item['role']==template['preset']),None)
    if entry is None: raise ValueError('reused_api_role_missing')
    if ready.get('pid')!=entry['pid'] or ready.get('role')!=template['preset'] or ready.get('stage')!='A': raise ValueError('reused_api_ready_identity_mismatch')
    if ready!=entry.get('ready',{}): raise ValueError('reused_api_ready_changed')
    host,port=ready.get('host'),ready.get('port')
    if host!='127.0.0.1' or type(port) is not int or not 1<=port<=65535: raise ValueError('invalid_reused_api_endpoint')
    identity=process_probe(int(ready['pid']))
    if identity is None: raise ValueError('reused_api_missing')
    args=shlex.split(identity['command']); expected=entry['argv']
    if args[1:]!=expected[1:]: raise ValueError('reused_api_argv_mismatch')
    second=process_probe(int(ready['pid']))
    if second!=identity: raise ValueError('reused_api_lifetime_changed')
    if entry.get('lstart') and entry['lstart']!=identity['started']: raise ValueError('reused_api_lstart_mismatch')
    return {**template,'api_url':ready['api_url'],'reused_api_pid':ready['pid'],'reused_api_lstart':identity['started']}

def controller_start_args(task, runtime_input_path):
    if not isinstance(task, str) or not task: raise ValueError('controller_task_required')
    return ['controller_start', '--task', task, '--manifest', str(runtime_input_path)]
