#!/bin/zsh
set -u

# 由执行主控在沙箱外运行。只启动本探针创建的隔离实例；供应商模型调用为 0。
# 预期修前测试退出 1；只有 summary.red_reproduced=true 才是指定缺陷的红态。
# 未命中竞态或准备失败都保留现场，不自动重跑，不消耗真实 haiku 回合。
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t157-outside-01.XXXXXX)" || exit 2
print -r -- "RUN_DIR=$run_dir"
cd "$task_root" || exit 2
python3 -B workbench/tests/test_t157_stop_input_e2e.py \
  --revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1 \
  --summary "$run_dir/red.json" > "$run_dir/probe.log" 2>&1
probe_code=$?
print -r -- "TEST_EXIT=$probe_code"
print -r -- "SUMMARY=$run_dir/red.json"
print -r -- "LOG=$run_dir/probe.log"
if [[ -f "$run_dir/red.json" ]]; then
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1],encoding="utf-8")); print(json.dumps({k:r.get(k) for k in ("status","red_reproduced","fixture","errors")},ensure_ascii=False,indent=2))' "$run_dir/red.json"
fi
exit "$probe_code"
