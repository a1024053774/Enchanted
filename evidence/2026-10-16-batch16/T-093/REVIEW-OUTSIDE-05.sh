#!/bin/bash
# T-093 第四轮可选 OS 补证。仅主控在沙箱外运行；无 auth、CLI 或模型。
# 用法：bash REVIEW-OUTSIDE-05.sh compile|deny-port|all /绝对路径/a2a-wt-t093
# 现有 OS 原件与 r21/r22 七场覆盖本轮审查；无需为本报告重新跑七场。
# 本脚本仅作可选补证，未运行；不读取凭据，不启动供应商 CLI，不调用模型。
set -eu
mode=${1:?compile|deny-port|all}
repo=${2:?冻结候选仓库绝对路径}
case "$mode" in compile|deny-port|all) ;; *) exit 2;; esac
candidate=9373a9d448820d951bdd8539a49731136c204e68
test "$(git -C "$repo" rev-parse HEAD)" = "$candidate"
git -C "$repo" diff --quiet HEAD -- workbench/src workbench/tests
exec /usr/bin/python3 -I -S -B - "$mode" "$repo" "$candidate" <<'PY'
import ctypes as C
import errno
import importlib.util
import json
import os
from pathlib import Path
import pwd
import socket
import subprocess
import sys
import tempfile

mode, source, candidate = sys.argv[1:]
source = Path(source).resolve()
output = Path(tempfile.mkdtemp(prefix='t093-review04-os-', dir='/private/tmp'))
print(str(output), flush=True)
result = {'status':'INCOMPLETE','candidate':candidate,'mode':mode,'checks':[],
          'real_auth_reads':0,'real_cli_starts':0,'real_upstream_requests':0,'model_turns':0,
          'scope':'实际生成器、OS 编译；可选生产 F 拒绝非 443 端口。OS 不按主机限制。无 TLS 或真实上游证明。'}
spec = importlib.util.spec_from_file_location('review04_policy', source/'workbench/src/claudeLoginSession.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
home = str(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve())
session = {'real_home':home,'credential_home':home,'private_root':str(output/'private'),
           'forward_port':54119,'upstream_port':443,'upstream_address':'203.0.113.31',
           'forwarder_directory':str(output/'forwarder'),'metadata_directory':str(output/'metadata'),
           'manifest':{'state':str(output/'state'),'executable':'/usr/bin/true'}}
production = runtime.policies(session)
try:
    if mode in ('compile','all'):
        lib = C.CDLL('/usr/lib/libsandbox.1.dylib')
        lib.sandbox_compile_string.argtypes = [C.c_char_p,C.c_void_p,C.POINTER(C.c_char_p)]
        lib.sandbox_compile_string.restype = C.c_void_p
        lib.sandbox_free_profile.argtypes = [C.c_void_p]
        lib.sandbox_free_error.argtypes = [C.c_char_p]
        for port in (443,18443,39527):
            current = dict(session,upstream_port=port)
            profiles = runtime.policies(current)
            assert profiles['C']==production['C'] and profiles['D']==production['D']
            assert profiles['F'].replace('(remote tcp4 "*:'+str(port)+'")','(remote tcp4 "*:443")')==production['F']
            error = C.c_char_p()
            compiled = lib.sandbox_compile_string(profiles['F'].encode(),None,C.byref(error))
            diagnostic = error.value.decode(errors='replace') if error.value else None
            result['checks'].append({'case':'F_compile','port':port,'compiled':bool(compiled),'diagnostic':diagnostic})
            if compiled: lib.sandbox_free_profile(compiled)
            if error.value: lib.sandbox_free_error(error)
            assert compiled, '实际 F profile 必须可编译'
    if mode in ('deny-port','all'):
        listener = socket.socket()
        try:
            listener.bind(('127.0.0.1',0)); listener.listen(4)
            port = listener.getsockname()[1]
            assert port!=443
            control = socket.create_connection(('127.0.0.1',port),timeout=2); control.close()
            code = '''import errno,json,socket,sys
s=socket.socket();s.settimeout(3)
try:
 s.connect(('127.0.0.1',int(sys.argv[1])))
 print(json.dumps({'denied':False,'errno':None}));sys.exit(2)
except OSError as e:
 print(json.dumps({'denied':e.errno==errno.EPERM,'errno':e.errno}));sys.exit(0 if e.errno==errno.EPERM else 2)
finally:s.close()
'''
            argv=['/usr/bin/sandbox-exec','-p',production['F'],'/usr/bin/python3','-I','-S','-B','-c',code,str(port)]
            child=subprocess.run(argv,capture_output=True,text=True,timeout=10,
                                 cwd=output,env={'PATH':'/usr/bin:/bin','LANG':'C'})
            (output/'denial.stdout').write_text(child.stdout,encoding='utf-8')
            (output/'denial.stderr').write_text(child.stderr,encoding='utf-8')
            result['checks'].append({'case':'production_F_non443_denial','port':port,'control_connected':True,
                                     'exit':child.returncode,'profile':production['F']})
            assert child.returncode==0 and json.loads(child.stdout)=={'denied':True,'errno':errno.EPERM}, '活端口必须由生产 F 以 EPERM 拒绝'
        finally:
            listener.close()
    result['status']='PASS'
except Exception as error:
    result['error']={'type':type(error).__name__,'message':str(error)}
finally:
    with (output/'result.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':result['status'],'output':str(output)},ensure_ascii=False))
raise SystemExit(0 if result['status']=='PASS' else 2)
PY
