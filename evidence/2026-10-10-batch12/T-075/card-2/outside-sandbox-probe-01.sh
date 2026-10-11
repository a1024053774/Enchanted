#!/bin/bash
# 由执行主控运行。只验证自建 /tmp 夹具，不联网，不改产品或正式数据。
set -u
set -o pipefail

evidence_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin=/opt/homebrew/bin/python3.11
if [[ ! -x "$python_bin" ]]; then
  printf '%s\n' '缺少已核对的 Python 3.11；停止，不安装或回退。' >&2
  exit 2
fi
unset PYTHONPATH PYTHONHOME NODE_COMPILE_CACHE
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
receipt_dir="$(mktemp -d "$evidence_dir/outside-probe.XXXXXX")" || exit 2
receipt_name="$(basename -- "$receipt_dir")"
label="probe-git-interrupt-$receipt_name"
command=("$python_bin" -B "$evidence_dir/probe-git-interrupt.py" --controller-run --label "$label")
printf '%q ' "${command[@]}" > "$receipt_dir/command.sh"
printf '\n' >> "$receipt_dir/command.sh"
if "${command[@]}" > "$receipt_dir/stdout.txt" 2> "$receipt_dir/stderr.txt"; then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$receipt_dir/exit-code.txt"
printf 'exit=%s\nreceipt=%s\nevidence=%s/%s\n' "$status" "$receipt_dir" "$evidence_dir" "$label"
printf '%s\n' '此脚本只跑三个 Git 中断窗口；退出码相符不替代原始断言和场景读回。'
exit "$status"
