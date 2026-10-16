#!/usr/bin/env bash
# 主控在核对交付后执行；worker 未运行。只在该隔离 worktree 内操作，不 push。
# 先由主控处理 findings/README.md 索引权限与补丁，再运行本文件。
set -euo pipefail

task_root=/Users/luckye/Documents/Code/a2a-wt-t087
cd "$task_root"

# 不接管调用者已有的暂存工作。
if ! git diff --cached --quiet; then
  echo 'INCOMPLETE: 暂存区已有修改，请主控先核对；本脚本未暂存任何文件。' >&2
  exit 1
fi

python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
python3 findings/generate_t087_graph.py > /tmp/t087-controller-regenerated.md
diff -u findings/ticket-gates-graph-2026-10-16.zh-CN.md /tmp/t087-controller-regenerated.md
python3 findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md
git diff --check

git add -- findings/generate_t087_graph.py findings/ticket-gates-graph-2026-10-16.zh-CN.md evidence/2026-10-16-batch16/T-087 .project-map/inbox/20261016T083546Z-worker:s16-t087-issue-001.md .project-map/inbox/20261016T083842Z-worker:s16-t087-issue-001.md
# 若主控已应用那一行索引补丁，应在核对后另行 git add -- findings/README.md。
# 此处只展示已暂存交付，避免自动提交尚未审阅或没有自动尾注的主控提交。
git diff --cached --stat
git diff --cached --check
echo 'INCOMPLETE: 交付已暂存；请核对索引改动、独立抽查和提交尾注后提交。未提交、未集成。'
# 核对后由主控在本任务的正确提交环境执行；不要手写 A2A-* 尾注：
# git commit -m 'docs: 显式展示 ticket 生命周期与门禁检查串'
