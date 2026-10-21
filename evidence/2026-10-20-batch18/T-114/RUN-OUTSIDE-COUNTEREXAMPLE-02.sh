#!/bin/bash
# 原始 build-01 产物为已知坏候选，不运行主控临时修复过的安装副本。
set -euo pipefail
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
cd "$(dirname "$0")/../../.."
OLD_APP=/private/tmp/t114-build-proof-build-01/Enchanted.app
OUT="/private/tmp/t114-helper-counterexample-$(date -u +%Y%m%dT%H%M%SZ).json"
if node evidence/2026-10-20-batch18/T-114/check-packaged-start.mjs "$OLD_APP" "$OUT"; then
  echo 'NO_GO: 启动探针未拒绝已知坏候选'
  exit 1
fi
python3 - "$OUT" <<'PY'
import json, pathlib, sys
p=pathlib.Path(sys.argv[1])
r=json.loads(p.read_text(encoding='utf-8'))
assert r['status']=='NO_GO' and r['cleanup_complete'], r
log=pathlib.Path(str(p)+'.stderr.log').read_text(encoding='utf-8')
assert 'Unable to find helper app' in log, log
print('PASS: 同一启动探针拒绝原始候选；确认 helper 启动错误，且隔离进程与数据已清理')
print('EVIDENCE:', p)
PY
