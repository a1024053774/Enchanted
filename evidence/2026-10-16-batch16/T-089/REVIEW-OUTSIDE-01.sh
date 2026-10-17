#!/bin/zsh
# T-089 冻结候选独立审查；只写本票外置盘下本次新建的 review 目录。
set -u
set -o pipefail
REVIEW_SCRATCH=/private/tmp/t089-review-01-fg12j_8o
REVIEW_EXTERNAL=/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089
echo "[建立目录] 输出目录=$REVIEW_EXTERNAL/review-outside-01-<新建> 硬超时=10s"
REVIEW_OUT=$(python3 -B - "$REVIEW_EXTERNAL" <<'PY'
import subprocess, sys
code = "import os,sys,tempfile; assert os.path.ismount('/Volumes/WD-Elements'), '外置盘未挂载；不回退内置盘'; print(tempfile.mkdtemp(prefix='review-outside-01-',dir=sys.argv[1]))"
p = subprocess.Popen([sys.executable, '-B', '-c', code, sys.argv[1]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
try:
    stdout, stderr = p.communicate(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()
    try:
        p.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    print('建立目录硬超时 exit_code=124', file=sys.stderr)
    raise SystemExit(124)
print(stdout, end='')
print(stderr, end='', file=sys.stderr)
print('建立目录 exit_code='+str(p.returncode), file=sys.stderr)
raise SystemExit(0 if p.returncode==0 else 1)
PY
)
REVIEW_INIT_RC=$?
echo "[建立目录] 输出目录=$REVIEW_OUT exit_code=$REVIEW_INIT_RC"
if (( REVIEW_INIT_RC != 0 )); then exit "$REVIEW_INIT_RC"; fi

# 每段用独立进程硬超时；保存准确 argv、输出、退出码。产品 --timeout 另由 oracle 检查。
run_bounded() {
  local review_label=$1
  local review_seconds=$2
  shift 2
  echo "[$review_label] 输出目录=$REVIEW_OUT 硬超时=${review_seconds}s"
  python3 -B - "$REVIEW_OUT" "$review_label" "$review_seconds" "$@" <<'PY'
import json, os, signal, subprocess, sys, time
from pathlib import Path
out, label, seconds = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3])
argv = sys.argv[4:]
started = time.monotonic()
p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
watchdog = False
try:
    stdout, stderr = p.communicate(timeout=seconds)
except subprocess.TimeoutExpired:
    watchdog = True
    # 只回收本次 review 夹具写下的挂起进程；不操作其他服务或会话。
    for marker in (out / 'checks').glob('*/hung-pid'):
        try:
            os.kill(int(marker.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.killpg(p.pid, signal.SIGKILL)
    stdout, stderr = p.communicate(timeout=5)
row = dict(argv=argv, exit_code=p.returncode, hard_watchdog=watchdog,
           elapsed_seconds=time.monotonic()-started, stdout=stdout, stderr=stderr)
(out / (label+'.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(out / (label+'.stdout.txt')).write_text(stdout, encoding='utf-8')
(out / (label+'.stderr.txt')).write_text(stderr, encoding='utf-8')
print(stdout, end='')
print(stderr, end='', file=sys.stderr)
print('exit_code='+str(p.returncode)+' hard_watchdog='+str(watchdog))
raise SystemExit(124 if watchdog else (0 if p.returncode==0 else 1))
PY
  local review_rc=$?
  echo "[$review_label] 输出目录=$REVIEW_OUT wrapper_exit_code=$review_rc"
  return "$review_rc"
}

# 先将一次性候选、3 个单处变异 patch、独立 oracle 和本地证据保留到本次归档目录。
run_bounded source-snapshot 25 python3 -B -c 'import shutil,sys; shutil.copytree(sys.argv[1],sys.argv[2])' "$REVIEW_SCRATCH" "$REVIEW_OUT/reviewer-source"
REVIEW_COPY_RC=$?
if (( REVIEW_COPY_RC != 0 )); then exit "$REVIEW_COPY_RC"; fi

# 真外置盘：好候选、未挂载/冲突/截断/等长损坏/复制挂起，三处变异；另探测删除阶段挂起。
# 好候选先通过相同 oracle，再要求变异失败。delete-hang 是候选反例，发现违规时整段应退出 1。
run_bounded independent-entry-checks 75 python3 -B "$REVIEW_OUT/reviewer-source/review_checks.py" --external --root "$REVIEW_OUT/checks"
REVIEW_CHECK_RC=$?
echo "[完成] 输出目录=$REVIEW_OUT exit_code=$REVIEW_CHECK_RC"
exit "$REVIEW_CHECK_RC"
