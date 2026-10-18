#!/bin/bash
# T-093 第二轮独立审查：由执行主控在沙箱外逐项执行。
# 每次只运行一个入口，exec 后不保留无保护的长期监督进程。
# 不读取真实凭据、不运行供应商 CLI、不调用模型、不写全局配置。
# 用法：bash REVIEW-OUTSIDE-03.sh MODE REPO [NEW_OUTPUT] [MATERIALS]
# MODE: profile-compile | none | primary | green | drop-first-record |
#       empty-credential-cases | scanner-zero | home-references-empty |
#       counts-always-match | t078-empty | t078-newline | t078-startup |
#       t078-epochs | t096-restore | t096-daemon | t096-probe |
#       verify-six | verify-rehearsal | verify-counts
# 所有输出必须是 /private/tmp 下不存在的新路径；失败现场不得覆盖或删除。
set -eu
mode=${1:?需要检查模式}
repo=${2:?需要源码目录}
candidate=630291ca7a07086d231e38a15fe1f1c9e6411bf0
output=${3:-}
case "$mode" in
  profile-compile)
    # 只调用编译器，不应用 profile，不发网络请求，不读 auth。
    # 对照 localhost 与文档用非 loopback IPv4；两者都必须可编译。
    exec /usr/bin/python3 -I -S -B - "$repo" "$candidate" "$output" <<'PY'
import ctypes as C
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(sys.argv[1]).resolve();candidate=sys.argv[2]
if subprocess.check_output(['/usr/bin/git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()!=candidate:
    raise SystemExit('INCOMPLETE: 源码候选不符')
if subprocess.run(['/usr/bin/git','-C',str(repo),'diff','--quiet','HEAD','--','workbench/src','workbench/tests']).returncode:
    raise SystemExit('INCOMPLETE: 运行源码有未提交修改')
out=Path(sys.argv[3]) if sys.argv[3] else Path(tempfile.mkdtemp(prefix='t093-r02-compile-',dir='/private/tmp'))/'result.json'
if Path('/private/tmp') not in out.resolve().parents or out.exists():raise SystemExit('INCOMPLETE: 需要新的临时输出路径')
spec=importlib.util.spec_from_file_location('runtime',repo/'workbench/src/claudeLoginSession.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
lib=C.CDLL('/usr/lib/libsandbox.1.dylib')
lib.sandbox_compile_string.argtypes=[C.c_char_p,C.c_void_p,C.POINTER(C.c_char_p)]
lib.sandbox_compile_string.restype=C.c_void_p
lib.sandbox_free_profile.argtypes=[C.c_void_p]
lib.sandbox_free_error.argtypes=[C.c_char_p]
rows=[]
for address in ('127.0.0.1','203.0.113.31'):
    session={'real_home':'/private/tmp/t093-r02-synthetic-home','private_root':'/private/tmp/t093-r02-private',
        'credential_home':'/private/tmp/t093-r02-synthetic-home','forward_port':54111,'upstream_port':443,
        'upstream_address':address,'forwarder_directory':'/private/tmp/t093-r02-state/forwarder',
        'metadata_directory':'/private/tmp/t093-r02-state/metadata',
        'manifest':{'state':'/private/tmp/t093-r02-state','executable':'/usr/bin/true'}}
    profile=runtime.policies(session)['F'];error=C.c_char_p()
    compiled=lib.sandbox_compile_string(profile.encode(),None,C.byref(error))
    diagnostic=error.value.decode(errors='replace') if error.value else None
    rows.append({'address':address,'compiled':bool(compiled),'diagnostic':diagnostic,'profile':profile})
    if compiled:lib.sandbox_free_profile(compiled)
    if error.value:lib.sandbox_free_error(error)
result={'status':'PASS' if all(row['compiled'] for row in rows) else 'NO_GO','candidate':candidate,
    'scope':'只编译候选真实 policies(F)，未应用沙箱，无网络、CLI 或凭据读取','cases':rows}
with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':result['status'],'output':str(out)},ensure_ascii=False))
raise SystemExit(0 if result['status']=='PASS' else 2)
PY
    ;;
  none|drop-first-record|empty-credential-cases|scanner-zero|home-references-empty|counts-always-match)
    : "${output:?需要新的临时 JSON 路径}"
    exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" \
      --source-revision "$candidate" --output "$output" --mutation "$mode"
    ;;
  primary|green)
    : "${output:?需要新的临时 JSON 路径}"
    exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" \
      --source-revision "$candidate" --output "$output" --rehearsal "$mode"
    ;;
  verify-six|verify-rehearsal|verify-counts)
    : "${output:?需要新的临时核对 JSON 路径}"
    shift 3
    # 其余参数为同一冻结候选的原始结果路径。禁止混用两代候选。
    case "$mode" in
      verify-six) exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/check_t093_chain_results.py" --candidate "$candidate" --output "$output" "$@" ;;
      verify-rehearsal) exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/check_t093_chain_results.py" --candidate "$candidate" --rehearsal --output "$output" "$@" ;;
      verify-counts) exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/check_t093_chain_results.py" --candidate "$candidate" --counts-only --output "$output" "$@" ;;
    esac
    ;;
  t078-empty|t078-newline|t078-startup|t078-epochs)
    : "${output:?需要新的临时输出目录}"
    # 既有测试只用本地 daemon/hook、替身 PTY 或已捕获材料，不调用模型。
    cd "$repo"
    case "$mode" in
      t078-empty) exec node "$repo/workbench/tests/test_t078_empty_declaration_entry.ts" "$output" ;;
      t078-newline) exec node "$repo/workbench/tests/test_t078_dispatch_newline_signal.ts" green "$output" ;;
      t078-startup) exec node "$repo/workbench/tests/test_t078_startup_pending.ts" "$output" "${4:?需要已核对的原始屏幕材料目录}" ;;
      t078-epochs) exec node "$repo/workbench/tests/test_t078_claude_epochs.ts" "$output" "${4:?需要已核对的原始 hook 材料目录}" ;;
    esac
    ;;
  t096-restore|t096-daemon|t096-probe)
    # 仅供主控已经另行建立的两票受管集成候选使用；本脚本不创建集成。
    # 必须显式指定集成 SHA；不得把本票候选缺文件算作红态或通过。
    : "${T093_REVIEW_INTEGRATION_SHA:?需要主控核对的两票受管集成 SHA}"
    : "${output:?需要新的临时 JSON 路径}"
    exec /usr/bin/python3 -I -S -B - "$mode" "$repo" "$output" "$T093_REVIEW_INTEGRATION_SHA" <<'PY'
import os
from pathlib import Path
import re
import subprocess
import sys
mode,repo,output,revision=sys.argv[1:]
if not re.fullmatch('[0-9a-f]{40}',revision) or subprocess.check_output(['/usr/bin/git','-C',repo,'rev-parse','HEAD'],text=True).strip()!=revision:
    raise SystemExit('INCOMPLETE: 集成候选不符')
if Path('/private/tmp') not in Path(output).resolve().parents or Path(output).exists():raise SystemExit('INCOMPLETE: 需要新的临时输出路径')
name={'t096-restore':'test_t096_restore.mjs','t096-daemon':'test_t096_daemon_restart.mjs','t096-probe':'test_t096_process_probe.py'}[mode]
path=Path(repo)/'workbench/tests'/name
if not path.is_file():raise SystemExit('INCOMPLETE: 集成测试不存在')
argv=['/usr/bin/python3','-B',str(path),output] if mode=='t096-probe' else ['/opt/homebrew/bin/node','--experimental-vm-modules',str(path),output]
os.chdir(repo);os.execv(argv[0],argv)
PY
    ;;
  *) echo 'INCOMPLETE: 未知检查模式' >&2; exit 2 ;;
esac
