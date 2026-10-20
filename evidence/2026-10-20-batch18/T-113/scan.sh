#!/bin/sh
# T-113 检索：站点与本票证据中不得出现凭据模式、本机用户目录或卷路径、邮箱地址。
# 用法：sh evidence/2026-10-20-batch18/T-113/scan.sh（在仓库根目录运行）；任一检索有命中则退出 1。
cd "$(dirname "$0")/../../.." || exit 2
status=0
run() {
  label=$1; shift
  if out=$(grep -rnIE "$@" docs evidence/2026-10-20-batch18/T-113 --exclude=scan.sh); then
    echo "HIT   $label"; echo "$out"; status=1
  else
    echo "CLEAN $label (grep exit $?)"
  fi
}
run '凭据模式' '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-(ant-)?[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|xox[abpr]-|[Bb]earer [A-Za-z0-9._-]{16,}|(api[_-]?key|secret|password|token)["'"'"' ]*[:=] *["'"'"'][^"'"'"']{8,})'
run '本机用户目录与卷路径' '(/Users/|/home/[a-z]|/Volumes/|[A-Za-z]:\\\\Users)'
run '邮箱地址' '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
run '真实会话与启动记录标识' '(launch-[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
exit $status
