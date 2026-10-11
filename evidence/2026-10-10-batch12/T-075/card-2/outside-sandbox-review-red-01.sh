#!/bin/bash
# 执行主控运行：仅复现独立审查 P2，先保存红态，尚未修复源码。
set -u
set -o pipefail
evidence_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$evidence_dir/../../../.." && pwd)"
cd -- "$repo_dir" || exit 2
python_bin=/opt/homebrew/bin/python3.11
if [[ ! -x "$python_bin" ]]; then
  printf '%s\n' '缺少已核对的 Python 3.11；停止。' >&2
  exit 2
fi
unset COOP_SCRIPT COOP_NATIVE_ENTRY COOP_E2E_ARTIFACT_ROOT COOP_E2E_TRACE
unset A2A_MUTANT_CLI A2A_MUTANT_CORE PYTHONPATH PYTHONHOME NODE_COMPILE_CACHE
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
receipt_dir="$(mktemp -d "$evidence_dir/outside-review-red.XXXXXX")" || exit 2
prefix="$(basename -- "$receipt_dir")"
# 只对冻结候选的原始产品源码复现；不把测试自身的改动当修复。
if ! git diff --exit-code 1273b17e933cd0bb279a20e6b237dbbd2f054db3 -- workbench/src acceptance > "$receipt_dir/source.diff"; then
  printf '%s\n' '产品或原验收入口已偏离审查候选；停止，保留差异。' >&2
  exit 2
fi
command=("$python_bin" -B "$evidence_dir/run-git-check.py" commands "$prefix-red-commands")
printf '%q ' "${command[@]}" > "$receipt_dir/command.sh"
printf '\n' >> "$receipt_dir/command.sh"
if "${command[@]}" > "$receipt_dir/stdout.txt" 2> "$receipt_dir/stderr.txt"; then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$receipt_dir/exit-code.txt"
if [[ "$status" -ne 1 ]]; then
  printf '预期业务红态退出 1，实际 %s；停止核对。\n' "$status" >&2
  exit 1
fi
"$python_bin" - "$evidence_dir/$prefix-red-commands/trace.json" > "$receipt_dir/red-verdict.json" <<'PY_REVIEW'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
failed=[a for a in r['assertions'] if not a['pass']]
claim='Missing second-command exit is unknown, not the first zero'
assert r['errors']==0 and r['failures']>0, r['results']
assert any(a['claim']==claim and a['observed'].get('returncode')==0 for a in failed), failed
print(json.dumps({'status':'EXPECTED_BUSINESS_RED','failed_assertions':failed},ensure_ascii=False,indent=2))
PY_REVIEW
verdict_status=$?
printf 'receipt=%s\nresult=%s/%s-red-commands\nverdict_exit=%s\n' "$receipt_dir" "$evidence_dir" "$prefix" "$verdict_status"
exit "$verdict_status"
