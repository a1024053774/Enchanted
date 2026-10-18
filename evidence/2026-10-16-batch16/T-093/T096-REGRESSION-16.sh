#!/bin/bash
# 仅执行主控在沙箱外运行；每场初始化仍须逐屏批准。模型与 POST 预算 0。
# 不自动按键、不登录、不设置 onboarding/trust 内部字段。
set -eu
mode=${1:?MODE REPO FULL_FROZEN_SHA CLAUDE_2_1_302 APPROVAL_REF NEW_LABEL}
repo=${2:?repo};candidate=${3:?candidate};cli=${4:?cli};approval=${5:?approval};label=${6:?new label}
case "$label" in ''|*[!a-z0-9_-]*) echo 'invalid new label' >&2;exit 2;; esac
test "$(git -C "$repo" rev-parse HEAD)" = "$candidate"
git -C "$repo" diff --quiet HEAD -- workbench/src workbench/tests
/usr/bin/python3 -I -S -B -c 'import os,sys; sys.exit(0 if os.path.ismount("/Volumes/WD-Elements") else 2)'
test ! -e "$repo/evidence/2026-10-16-batch16/T-096/$label.run.json"
output=/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-093/$label
test ! -e "$output"
extra=();panes=1
case "$mode" in
 tracer) extra=(--check-close);;
 three) panes=3;extra=(--check-close);;
 missing-argv) extra=(--fault missing-argv);;
 version-mismatch) extra=(--fault version-mismatch);;
 missing-session) extra=(--fault missing-session);;
 isolation) panes=3;extra=(--fault missing-argv);;
 empty-reopen) panes=3;extra=(--check-close --check-empty-reopen);;
 *) echo 'unknown T096 regression mode' >&2;exit 2;;
esac
# 原 runner 在 T-096 目录写本次新 label 的小型 run/archive 摘要；不覆盖旧 attempt。
exec python3 "$repo/evidence/2026-10-16-batch16/T-096/run_restart.py" \
 --source "$repo" --output "$output" --label "$label" --approval-ref "$approval" \
 --claude "$cli" --claude-version 2.1.302 --panes "$panes" --expect restore \
 --startup-wait-seconds 600 "${extra[@]}"
