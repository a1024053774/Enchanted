#!/bin/bash
# 执行主控运行：审查 P2 修复绿态，以及修复候选的完整回归与变异验证。
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
receipt_dir="$(mktemp -d "$evidence_dir/outside-review-green.XXXXXX")" || exit 2
prefix="$(basename -- "$receipt_dir")"
if ! git diff --exit-code 3386c4cd3a4e44b5b58d5a46a780fb99f9aa637a -- workbench/src workbench/tests acceptance > "$receipt_dir/source.diff"; then
  printf '%s\n' '源码或测试已偏离修复候选；停止，保留差异。' >&2
  exit 2
fi
runner="$evidence_dir/../run-acceptance.py"
manifest="$evidence_dir/mutants-02/manifest.json"
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
# 第一项就是原样重跑已取得业务红态的双命令中断反例。
run_case green-commands 0 "$python_bin" -B "$evidence_dir/run-git-check.py" commands "$prefix-green-commands" || exit 1
run_case green-cards 0 "$python_bin" -B "$repo_dir/workbench/tests/test_task_cards_e2e.py" --output "$evidence_dir/$prefix-green-cards" || exit 1
for suite in coop recovery run; do
  run_case "green-$suite" 0 "$python_bin" -B "$runner" "$suite" "card-2/$prefix-green-$suite" || exit 1
  run_case "count-$suite" 0 "$python_bin" -B "$evidence_dir/count-interventions.py" "$evidence_dir/$prefix-green-$suite" || exit 1
done
run_case green-window 0 "$python_bin" -B "$evidence_dir/run-git-check.py" window "$prefix-green-window" || exit 1
run_case green-cas 0 "$python_bin" -B "$evidence_dir/run-git-check.py" cas "$prefix-green-cas" || exit 1
# 以下五个变异体全部来自修复候选 3386c4c；原 mutants-01 不覆盖。
run_case card-mutants 0 "$python_bin" -B "$evidence_dir/run-card-mutants.py" --manifest "$manifest" --prefix "$prefix" || exit 1
run_case mutant-cas 1 "$python_bin" -B "$evidence_dir/run-git-check.py" cas "$prefix-mutant-cas" --mutant cas --mutant-manifest "$manifest" || exit 1
printf '原始收据：%s\n' "$receipt_dir"
printf '%s\n' '退出码相符仍须检查业务断言。独立审查不再重开；修复 diff 由执行主控审阅。'
