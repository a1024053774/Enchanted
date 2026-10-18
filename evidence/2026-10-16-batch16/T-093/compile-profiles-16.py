"""主控沙箱外只编译真实 F profile；无应用沙箱、网络、CLI 或 auth 读取。"""
import argparse
import ctypes as C
import importlib.util
import json
import os
from pathlib import Path
import pwd
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--candidate',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();repo=args.source.resolve();output=args.output.resolve()
if Path('/private/tmp') not in output.parents or output.exists():parser.error('select a new output under /private/tmp')
if subprocess.check_output(['/usr/bin/git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()!=args.candidate:parser.error('frozen candidate mismatch')
if subprocess.run(['/usr/bin/git','-C',str(repo),'diff','--quiet','HEAD','--','workbench/src','workbench/tests']).returncode:parser.error('runtime source is dirty')
spec=importlib.util.spec_from_file_location('runtime',repo/'workbench/src/claudeLoginSession.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
library=C.CDLL('/usr/lib/libsandbox.1.dylib')
library.sandbox_compile_string.argtypes=[C.c_char_p,C.c_void_p,C.POINTER(C.c_char_p)];library.sandbox_compile_string.restype=C.c_void_p
library.sandbox_free_profile.argtypes=[C.c_void_p];library.sandbox_free_error.argtypes=[C.c_char_p]
rows=[]
for address in ('127.0.0.1','203.0.113.31'):
 session={'real_home':str(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()),'private_root':'/private/tmp/t093-compile16-private','credential_home':str(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()),'forward_port':54111,'upstream_port':443,'upstream_address':address,'forwarder_directory':'/private/tmp/t093-compile16-state/forwarder','metadata_directory':'/private/tmp/t093-compile16-state/metadata','manifest':{'state':'/private/tmp/t093-compile16-state','executable':'/usr/bin/true'}}
 policy=runtime.policies(session)['F'];error=C.c_char_p();compiled=library.sandbox_compile_string(policy.encode(),None,C.byref(error))
 rows.append({'address':address,'compiled':bool(compiled),'diagnostic':error.value.decode(errors='replace') if error.value else None,'profile':policy,'OS_host_filter':False,'OS_remote_ports':[443]})
 if compiled:library.sandbox_free_profile(compiled)
 if error.value:library.sandbox_free_error(error)
result={'status':'PASS' if all(row['compiled'] and '(remote tcp4 "*:443")' in row['profile'] for row in rows) else 'INCOMPLETE','candidate':args.candidate,'scope':'Compiler only; no network or permission enforcement proof. OS does not restrict destination host.','cases':rows,'real_auth_reads':0,'real_cli_starts':0,'real_upstream_requests':0,'model_turns':0}
with output.open('x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':result['status'],'output':str(output)}));raise SystemExit(0 if result['status']=='PASS' else 2)
