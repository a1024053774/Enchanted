#!/bin/zsh
set -u

# 修前同场景基线；先运行，收到结果后 worker 才改产品提示词。
# 两个真实 Haiku 主控各 2 个根提示，合计预留 4/16。受管 worker 仅用本地脚本化接口。
# 读取精确 Claude 登录凭据至临时私有 HOME，不复制设置/MCP，不携带 refreshToken；
# 停止后删除该 HOME，只留原生 transcript、卡、脚本、截图。不会写用户全局配置。
cd /Users/luckye/Documents/Code/a2a-wt-t163 || exit 2
run_dir=$(mktemp -d /private/tmp/t163-outside-01.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-163
budget="$evidence/model-budget.jsonl"
print -r -- "RUN_DIR=$run_dir"

python3 workbench/tests/test_t163_controller_e2e.py --scenario c5 --revision e83a8a04e \
  --budget "$budget" --summary "$evidence/$tag-c5-baseline.json" > "$run_dir/c5.log" 2>&1
c5_rc=$?
cat "$run_dir/c5.log"

python3 workbench/tests/test_t163_controller_e2e.py --scenario oracle --revision e83a8a04e \
  --budget "$budget" --summary "$evidence/$tag-oracle-baseline.json" > "$run_dir/oracle.log" 2>&1
oracle_rc=$?
cat "$run_dir/oracle.log"

print -r -- "C5_EXIT=$c5_rc ORACLE_EXIT=$oracle_rc"
print -r -- "SUMMARIES=$evidence/$tag-c5-baseline.json $evidence/$tag-oracle-baseline.json"
print -r -- 'C5 有意保留 INCOMPLETE：请独立读 summary.cards 与 fixture/out/native-transcript.json，按 semantic_review_required 判定是否出现漏项、是否派发前自检。'
print -r -- 'oracle 只有业务 check 失败且无 error/cleanup_errors 才能算红态；启动/登录/权限/超时失败不算红态。'
print -r -- '若修前已满足要求，记录未复现，交回 worker；不要为了红态改场景或自动重试。'
print -r -- '请回传两个摘要路径、C5 独立判断和预算账本；原始 fixture 留给主控按 T-088 归档。'
# This is a baseline collector. Its zero exit means the commands ran; it is not an acceptance verdict.
exit 0
