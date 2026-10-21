#!/bin/bash
# 主控在沙箱外运行；只打包并检查清理结果，不安装、不启动 GUI、不生成证据文件。
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - "$@" <<'PY'
import datetime, json, os, pathlib, re, subprocess, sys

slot=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().strftime('local-%Y%m%dT%H%M%S')
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',slot), 'Invalid slot'
env=dict(os.environ)
env.update(TMPDIR='/private/tmp',TMP='/private/tmp',TEMP='/private/tmp')
for key in ['npm_config_cache','electron_config_cache','ELECTRON_OVERRIDE_DIST_PATH','ELECTRON_RUN_AS_NODE']:
    env.pop(key,None)
argv=['npm','run','package:mac','--','--slot',slot]
print('COMMAND:', ' '.join(argv),flush=True)
p=subprocess.run(argv,env=env,text=True,capture_output=True)
print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
assert p.returncode==0, '打包失败，保留本次临时构建目录'
result=json.loads(p.stdout.strip().splitlines()[-1])
root=pathlib.Path('/private/tmp')/('a2a-build-'+slot)
app=root/'Enchanted.app'
assert pathlib.Path(result['app'])==app and app.is_dir()
assert sorted(p.name for p in root.iterdir())==['Enchanted.app'], '构建目录仍有中间产物'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(app)],check=True)
print(f'PASS: {root} 中只剩 Enchanted.app；签名校验通过。')
print(f'APP: {app}')
PY
