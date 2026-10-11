#!/bin/bash
# 执行主控在沙箱外运行；只做 T-075-1 隔离验收，不联网。
set -u
set -o pipefail

evidence_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$evidence_dir/../../.." && pwd)"
cd -- "$repo_dir" || exit 2
python_bin=/opt/homebrew/bin/python3.11
if [[ ! -x "$python_bin" ]]; then
  printf '%s\n' '缺少已核对的 Python 3.11；停止，不安装或回退。' >&2
  exit 2
fi
# 禁止继承调用方的入口替换；每个反例由本脚本显式指定。
unset COOP_SCRIPT COOP_NATIVE_ENTRY COOP_E2E_ARTIFACT_ROOT COOP_E2E_TRACE
unset A2A_MUTANT_CLI A2A_MUTANT_CORE NODE_COMPILE_CACHE
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
receipt_dir="$(mktemp -d "$evidence_dir/outside-executor.XXXXXX")" || exit 2
prefix="$(basename -- "$receipt_dir")"
runner="$evidence_dir/run-acceptance.py"
cas_runner="$evidence_dir/run-cas.py"
mismatches=0

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
  if [[ "$status" -ne "$expected" ]]; then
    mismatches=$((mismatches + 1))
  fi
}

printf 'check\texpected_exit\tactual_exit\n' > "$receipt_dir/summary.tsv"
# HTTP 分支删除后，三套绿态均绑定最终本地 CLI。恢复套需 ps 核对自建子进程。
run_case green-coop 0 "$python_bin" -B "$runner" coop "$prefix-green-coop"
run_case green-recovery 0 "$python_bin" -B "$runner" recovery "$prefix-green-recovery"
run_case green-run 0 "$python_bin" -B "$runner" run "$prefix-green-run"
# 三个变异体使用删除 HTTP 后的独立源码副本；正常候选不被修改。
run_case mutant-fence 1 "$python_bin" -B "$runner" coop "$prefix-mutant-fence" --mutant fence --mutant-dir mutants-final
run_case mutant-cas 1 "$python_bin" -B "$cas_runner" "$prefix-mutant-cas" --mutant --mutant-dir mutants-final
run_case green-cas 0 "$python_bin" -B "$cas_runner" "$prefix-green-cas"
run_case mutant-lock 1 "$python_bin" -B "$runner" recovery "$prefix-mutant-lock" --mutant lock --mutant-dir mutants-final

printf '验收原始收据：%s\n' "$receipt_dir"
printf '%s\n' '退出码相符仍须检查业务失败与环境错误；本脚本不宣布门禁验收通过。'
if [[ "$mismatches" -ne 0 ]]; then
  exit 1
fi
