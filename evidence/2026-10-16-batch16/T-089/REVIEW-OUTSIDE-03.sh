#!/bin/zsh
# T-089 第三轮独立审查；只写本票下本次新建的 review 目录。
set -u
set -o pipefail
REVIEW_SCRATCH=/private/tmp/t089-review-03-xy2hcz72
REVIEW_EXTERNAL=/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089
echo "[建立目录] 输出目录=$REVIEW_EXTERNAL/review-outside-03-<新建> 硬超时=10s"
REVIEW_OUT=$(python3 -B - "$REVIEW_EXTERNAL" <<'PY'
import subprocess, sys
code = "import os,sys,tempfile; assert os.path.ismount('/Volumes/WD-Elements'), '外置盘未挂载；不回退内置盘'; print(tempfile.mkdtemp(prefix='review-outside-03-',dir=sys.argv[1]))"
p = subprocess.Popen([sys.executable, '-B', '-c', code, sys.argv[1]], stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, start_new_session=True)
try:
    stdout, stderr = p.communicate(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()
    try:
        p.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    print('建立目录 exit_code=124 硬超时', file=sys.stderr)
    raise SystemExit(124)
print(stdout, end='')
print(stderr, end='', file=sys.stderr)
print('建立目录 exit_code='+str(p.returncode), file=sys.stderr)
raise SystemExit(p.returncode)
PY
)
REVIEW_INIT_RC=$?
echo "[建立目录] 输出目录=$REVIEW_OUT exit_code=$REVIEW_INIT_RC"
if (( REVIEW_INIT_RC != 0 )); then exit "$REVIEW_INIT_RC"; fi

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
p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
                     env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
watchdog = False
try:
    stdout, stderr = p.communicate(timeout=seconds)
except subprocess.TimeoutExpired:
    watchdog = True
    # 只处理本次夹具记录的 PID，不操作用户服务或其他会话。
    markers = list((out / 'checks').glob('*/hung-pid'))
    markers += list((out / 'candidate-suite').glob('checks-*/*-pid'))
    markers += list((out / 'candidate-suite').glob('checks-*/hang-entered'))
    for marker in markers:
        try:
            pid = int(marker.read_text(encoding='utf-8'))
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.killpg(p.pid, signal.SIGKILL)
    stdout, stderr = p.communicate(timeout=3)
row = dict(argv=argv, exit_code=p.returncode, hard_watchdog=watchdog,
           elapsed_seconds=time.monotonic()-started, stdout=stdout, stderr=stderr)
with (out / (label+'.json')).open('x', encoding='utf-8') as f:
    json.dump(row, f, ensure_ascii=False, indent=2)
    f.write('\n')
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

# 保留冻结源码、独立 oracle、四个单处错误 patch、原始 T-086 输入及本地文本结果。
# 本地模拟的原始文件与归档留在 /tmp；外置盘场景重新产生自己的原件和归档。
run_bounded source-snapshot 25 python3 -B "$REVIEW_SCRATCH/copy_snapshot.py" "$REVIEW_SCRATCH" "$REVIEW_OUT/reviewer-source"
REVIEW_COPY_RC=$?
if (( REVIEW_COPY_RC != 0 )); then exit "$REVIEW_COPY_RC"; fi

# 好候选先通过每一项 oracle，再要求四个变异被同一 oracle 拒绝。
# 准备阶段：复制、核对、写清单失败/挂起须保全所有原件。
# 回收阶段：删除 EIO、挂起须 exit 1、INCOMPLETE、准确剩余列表和可恢复的归档。
run_bounded independent-entry-checks 50 python3 -B "$REVIEW_OUT/reviewer-source/review_checks.py" --external --root "$REVIEW_OUT/checks"
REVIEW_CHECK_RC=$?

# 运行候选自己已提交的真实入口测试，确认删除 EIO/删除挂起确有持续测试覆盖。
# 只改测试输出根目录；测试源码、归档命令和断言保持冻结原文。
run_bounded candidate-regression-checks 25 python3 -B "$REVIEW_OUT/reviewer-source/run_candidate_suite.py" "$REVIEW_OUT"
REVIEW_SUITE_RC=$?

# T-086 从冻结 git archive 输入重新解出，字节重建；S3 原函数与抽取函数同夹具对照。
run_bounded replay-and-s3-readback 50 python3 -B "$REVIEW_OUT/reviewer-source/supplemental.py" --external --root "$REVIEW_OUT/supplemental"
REVIEW_REPLAY_RC=$?

echo "[完成] 输出目录=$REVIEW_OUT independent=$REVIEW_CHECK_RC regression=$REVIEW_SUITE_RC supplemental=$REVIEW_REPLAY_RC"
if (( REVIEW_CHECK_RC != 0 || REVIEW_SUITE_RC != 0 || REVIEW_REPLAY_RC != 0 )); then exit 1; fi
exit 0
