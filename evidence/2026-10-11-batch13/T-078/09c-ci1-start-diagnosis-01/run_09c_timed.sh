#!/bin/bash
# 主控 #354：09C 计时段（C-I1 Enter 起）。每步机械核对，任一不符立即停、不按键。
set -o pipefail
T=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
I=$T/09c-c1-b1-ideation-p1-01/phases
E=$T/09c-c1-b1-executor-p1-01/phases
S=/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad
THREAD=829c9920-a05f-438e-9734-a155b00ed323
log() { echo "[$(date +%T)] $*"; }
die() { log "STOP: $*"; exit 1; }
run() { # run <cmd-file> <alarm-seconds> ; echo last line; require status in $3 (regex)
  local r; r=$(perl -e "alarm $2; exec @ARGV" bash "$1" 2>&1 | tail -1); log "$(basename $(dirname $1))/$(basename $1): ${r:0:200}"
  echo "$r" | grep -Eq "\"status\": \"($3)\"" || die "$(basename $1) status not $3"
}
jget() { python3 -c "import json,sys;d=json.load(open(sys.argv[1]),strict=False);v=d
for k in sys.argv[2].split('.'): v=v.get(k) if isinstance(v,dict) else None
print(v)" "$@"; }

# ---- C-I1：签许可、预检、单 Enter（停止条目在此创建，计时开始）
cd $I/C-I1 || die cd
python3 $S/sign_phase.py permission-approval-01.json "主控 #354 T-078 09C C-I1 权限：完整读屏 16074 字节与 dispatch-01 原屏 cmp 0；命令与 TOOL-COMMAND-PREVIEW argv 完全一致（inbox send --kind stop，thread ${THREAD}）；❯ 1. Yes 一次性（用户授权代签 09C 各阶段）" >/dev/null || die sign-CI1
run PERMISSION-CHECK-COMMAND.txt 300 PASS
run PERMISSION-ENTER-COMMAND.txt 400 'PASS|READY_FOR_EXECUTOR|PENDING|DELIVERED|[A-Z_]+'
STOP=$(python3 -c "import json;d=json.load(open('execute-02/result.json'),strict=False);s=d.get('stop_entry') or {};print(s.get('id',''))")
STATUS1=$(jget execute-02/result.json status)
log "C-I1 settlement status=${STATUS1} stop=${STOP}"
[ -n "$STOP" ] || die "no stop id in C-I1 settlement"
run $T/09c-c1-preparation-01/CONTINUED-DEMAND-COMMAND.txt 120 '[A-Z_]+'

# ---- C-I2：必须在 stop 年龄 <120s 内拿到 stop_too_early
cd $I/C-I2 || die cd
run OBSERVE-PERMISSION-COMMAND.txt 200 READY_FOR_PERMISSION
perl -e 'alarm 200; exec @ARGV' bash PERMISSION-SCREEN-CMP-COMMAND.txt >/dev/null 2>&1; CMP=$?
log "C-I2 screen-cmp exit=${CMP}"; [ $CMP = 0 ] || die "C-I2 screen cmp exit ${CMP}"
run PREPARE-PERMISSION-COMMAND.txt 200 PASS
python3 - "permission-approval-01.json" "$THREAD" "$STOP" <<'PY' || exit 1
import json,sys
d=json.load(open(sys.argv[1])); c=d.get('bash_command','')
ok = (d.get('selected_line')=='❯ 1. Yes' and 'workbench/src/gates/cli.ts stop' in c
      and f'--thread {sys.argv[2]}' in c and f'--stop-id {sys.argv[3]}' in c
      and not any(x in c for x in (';','&&','||','|','`','$(')))
print('C-I2 auto-check', 'OK' if ok else 'FAIL', '|', c[-160:]); sys.exit(0 if ok else 1)
PY
python3 $S/sign_phase.py permission-approval-01.json "主控 #354 T-078 09C C-I2 权限：完整读屏 cmp 0；脚本核对命令为 gates/cli.ts stop --thread ${THREAD} --stop-id ${STOP}、无拼接命令、❯ 1. Yes（预期 stop_too_early；用户授权代签 09C 各阶段）" >/dev/null || die sign-CI2
run PERMISSION-CHECK-COMMAND.txt 300 PASS
run PERMISSION-ENTER-COMMAND.txt 400 PASS
run COLLECT-COMMAND.txt 300 PASS

# ---- C-I3：观察、比对，后台启动条件式驱动，核对模板后签字发布
cd $I/C-I3 || die cd
run OBSERVE-PERMISSION-COMMAND.txt 200 READY_FOR_PERMISSION
perl -e 'alarm 200; exec @ARGV' bash PERMISSION-SCREEN-CMP-COMMAND.txt >/dev/null 2>&1; CMP=$?
log "C-I3 screen-cmp exit=${CMP}"; [ $CMP = 0 ] || die "C-I3 screen cmp exit ${CMP}"
( perl -e 'alarm 400; exec @ARGV' bash CONDITIONAL-ENTER-COMMAND.txt > $S/09c-ci3-driver.log 2>&1; echo "rc=$?" >> $S/09c-ci3-driver.log ) &
DRV=$!
for i in $(seq 1 120); do [ -f execute-02-review/template.json ] && break; sleep 1; done
[ -f execute-02-review/template.json ] || die "C-I3 template not written in 120s"
log "C-I3 template ready"
REV=REVIEW-AND-PUBLISH-COMMANDS.txt
awk 'BEGIN{n=0} /^python3 -B - <<.PY.$/{n++} {if(n==1) print}' $REV | awk '/^PY$/{print; exit} {print}' > $S/09c-review-1.sh
awk 'BEGIN{n=0} /^python3 -B - <<.PY.$/{n++} {if(n==2) print}' $REV | awk '/^PY$/{print; exit} {print}' > $S/09c-review-2.sh
bash $S/09c-review-1.sh || die "draft copy failed"
python3 - "execute-02-review/approval-draft.json" "$THREAD" "$STOP" <<'PY' || exit 1
import json,sys
d=json.load(open(sys.argv[1])); s=json.dumps(d,ensure_ascii=False)
c=d.get('bash_command') or d.get('command') or ''
ok=('gates/cli.ts stop' in s and sys.argv[2] in s and sys.argv[3] in s and d.get('selected_line','❯ 1. Yes')=='❯ 1. Yes'
    and d.get('approved_by') is None and not any(x in c for x in (';','&&','||','|','`','$(')))
print('C-I3 template auto-check', 'OK' if ok else 'FAIL', '|', c[-160:]); sys.exit(0 if ok else 1)
PY
python3 $S/sign_phase.py execute-02-review/approval-draft.json "主控 #354 T-078 09C C-I3 条件式单 Enter 模板：脚本核对命令为 gates/cli.ts stop、thread ${THREAD}、stop ${STOP}、无拼接命令、❯ 1. Yes；驱动另在按键前完整读屏与模板逐项比对（用户 2026-10-16 授权代签 09C 并允许条件式自动单 Enter）" >/dev/null || die sign-CI3
bash $S/09c-review-2.sh || die "publish failed"
log "C-I3 approval published; waiting driver"
wait $DRV; tail -2 $S/09c-ci3-driver.log | cut -c1-300
grep -q '"status": "PASS"' $S/09c-ci3-driver.log || die "C-I3 driver not PASS"
run COLLECT-COMMAND.txt 300 PASS

# ---- C-I4、C-E1
cd $I/C-I4 && run COLLECT-COMMAND.txt 300 PASS
cd $E/C-E1 && run COLLECT-COMMAND.txt 300 PASS
log "09C timed segment complete"
