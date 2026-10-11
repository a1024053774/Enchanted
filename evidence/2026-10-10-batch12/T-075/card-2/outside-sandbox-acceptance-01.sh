#!/bin/bash
# 由执行主控运行。只跑 T-075-2 隔离验收，不联网，不改正式数据。
set -u
set -o pipefail

evidence_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$evidence_dir/../../../.." && pwd)"
cd -- "$repo_dir" || exit 2
python_bin=/opt/homebrew/bin/python3.11
if [[ ! -x "$python_bin" ]]; then
  printf '%s\n' '缺少已核对的 Python 3.11；停止，不安装或回退。' >&2
  exit 2
fi
unset PYTHONPATH PYTHONHOME NODE_COMPILE_CACHE
unset COOP_SCRIPT COOP_NATIVE_ENTRY COOP_E2E_ARTIFACT_ROOT COOP_E2E_TRACE
unset A2A_MUTANT_CLI A2A_MUTANT_CORE
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
receipt_dir="$(mktemp -d "$evidence_dir/outside-acceptance.XXXXXX")" || exit 2
receipt_name="$(basename -- "$receipt_dir")"
runner="$evidence_dir/../run-acceptance.py"
printf 'case\texpected_exit\tactual_exit\n' > "$receipt_dir/summary.tsv"
run_case() {
  local name="$1" expected="$2" status
  shift 2
  printf '%q ' "$@" > "$receipt_dir/$name.command.sh"
  printf '\n' >> "$receipt_dir/$name.command.sh"
  if "$@" > "$receipt_dir/$name.stdout.txt" 2> "$receipt_dir/$name.stderr.txt"; then
    status=0
  else
    status=$?
  fi
  printf '%s\n' "$status" > "$receipt_dir/$name.exit-code.txt"
  printf '%s\t%s\t%s\n' "$name" "$expected" "$status" >> "$receipt_dir/summary.tsv"
  printf '%s expected=%s actual=%s\n' "$name" "$expected" "$status"
  [[ "$status" -eq "$expected" ]]
}
for suite in coop recovery run; do
  run_case "green-$suite" 0 "$python_bin" -B "$runner" "$suite" "card-2/$receipt_name-green-$suite" || exit 1
  run_case "count-$suite" 0 "$python_bin" -B "$evidence_dir/count-interventions.py" "$evidence_dir/$receipt_name-green-$suite" || exit 1
done
# 新窗口的起点红态是任务卡入口缺失；绿态必须到达真实 SIGKILL 边界。
run_case red-window 1 "$python_bin" -B "$evidence_dir/run-git-check.py" window "$receipt_name-red-window" --baseline || exit 1
run_case green-window 0 "$python_bin" -B "$evidence_dir/run-git-check.py" window "$receipt_name-green-window" || exit 1
run_case green-cas 0 "$python_bin" -B "$evidence_dir/run-git-check.py" cas "$receipt_name-green-cas" || exit 1
run_case mutant-cas 1 "$python_bin" -B "$evidence_dir/run-git-check.py" cas "$receipt_name-mutant-cas" --mutant cas || exit 1
printf '原始收据：%s\n' "$receipt_dir"
printf '%s\n' '退出码符合预期仍须核对业务断言、注入边界与环境错误；本脚本不宣布本卡完成。'
