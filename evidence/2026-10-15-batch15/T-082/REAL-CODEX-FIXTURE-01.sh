#!/usr/bin/env bash
set -euo pipefail

# Build only an external-disk fixture. This script does not start a daemon or
# Codex. The product creates the worker/review/candidate workspaces later.
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
VOLUME=/Volumes/WD-Elements
BASE="$VOLUME/a2a-t082-real-fixtures"
[[ -d "$VOLUME" && ! -L "$VOLUME" ]] || { echo 'external volume is not mounted' >&2; exit 2; }
mkdir -p "$BASE"
seq=1
while [[ -e "$BASE/fixture-$(printf '%02d' "$seq")" ]]; do ((seq++)); done
ROOT="$BASE/fixture-$(printf '%02d' "$seq")"
PYTHON_BIN=$(command -v python3)
mkdir -p "$ROOT/repo/src" "$ROOT/repo/acceptance" "$ROOT/state"

git -C "$ROOT/repo" init -b main >/dev/null
git -C "$ROOT/repo" config user.name T082-fixture
git -C "$ROOT/repo" config user.email t082-fixture@example.invalid
printf 'wrong\n' > "$ROOT/repo/src/value.txt"
cat > "$ROOT/repo/acceptance/weak.py" <<'PY'
from pathlib import Path
assert Path('src/value.txt').read_text() == 'correct\n'
PY
cat > "$ROOT/repo/test-command.sh" <<'SH'
#!/bin/sh
exec python3 -I -B acceptance/weak.py
SH
chmod 755 "$ROOT/repo/test-command.sh"
git -C "$ROOT/repo" add src/value.txt acceptance/weak.py test-command.sh
git -C "$ROOT/repo" commit -m 'T-082 weak-review baseline' >/dev/null
BASELINE=$(git -C "$ROOT/repo" rev-parse HEAD)

cat > "$ROOT/reviewer-role-round1.md" <<'EOF'
你是 T-082 真实 reviewer。审查由门禁启动，候选副本是唯一可写目录。
按产品提示完成一次审查。边界证明时：在当前工作目录写 t082-reviewer-write.txt 并运行 candidate/test-command.sh；然后尝试写审查目录、worker worktree、共享仓库 .git，并运行 git update-ref 和网络请求，保留每次命令的原始错误。每项探针后打印一行 T082_DENY target=... error=...；副本写入和测试成功后打印 T082_PROBE candidate_write=PASS test=PASS。不要提交，不要集成，不要写请求文件之外的路径。最终按产品要求发起 review_submit。
EOF
cat > "$ROOT/reviewer-role-round2.md" <<'EOF'
你是 T-082 真实交付 reviewer。只在门禁提供的一次性候选副本里工作。
审查完成条件（含 oracle_paths）是否足以拒绝明显错误实现；在副本中构造 2～5 个变异，逐项运行完成条件或候选测试，报告每项改动、命令和结果。报告必须有“完成条件与变异检查”一节。不要提交、集成或改副本外路径，最后按产品要求发起 review_submit。
在发起最终 review_submit 前，把完整报告打印到终端，便于门禁 PTY 原始记录保留报告正文。
在 report 的“完成条件与变异检查”对象中，用 mutation_checks 数组记录每个变异的 id、change、command、result；完成条件充分性判断单独记录。门禁不判断你是否审对，按实际结果报告。
EOF
: > "$ROOT/.t082-trusted"
TASK="t082-real-$(printf '%02d' "$seq")"
cat > "$ROOT/task-card.json" <<EOF
{
  "id": "$TASK",
  "source": null,
  "goal": "交付 src/value.txt 的 correct 内容",
  "non_goals": ["不修改任务目录外的文件"],
  "paths": {"allow": ["src/", "acceptance/", "test-command.sh"], "deny": []},
  "oracle_paths": ["acceptance/weak.py"],
  "completion_conditions": [{"argv": ["$PYTHON_BIN", "-I", "-B", "acceptance/weak.py"]}],
  "red_commands": [],
  "task_type": "后端逻辑",
  "repair_target": null,
  "complexity": "L",
  "executor": {"cli": "Codex", "model": "gpt-6.1-sol", "effort": "xhigh"},
  "base_commit": null,
  "writer": null
}
EOF
python3 - "$ROOT/manifest.json" "$ROOT" "$TASK" "$BASELINE" <<'PY'
import json, sys
out, root, task, baseline = sys.argv[1:]
card = json.load(open(root + '/task-card.json', encoding='utf-8'))
card['goal'] = '交付 src/value.txt 内容 correct 加换行，并新增 src/details.txt 内容 ready 加换行；两项都必需。'
with open(root + '/task-card-round2.json', 'x', encoding='utf-8') as stream:
    json.dump(card, stream, ensure_ascii=False, indent=2)
json.dump({'fixture_root': root, 'task': task, 'repo': root + '/repo', 'state': root + '/state',
           'card': root + '/task-card.json', 'card_round2': root + '/task-card-round2.json',
           'role_round1': root + '/reviewer-role-round1.md',
           'role_round2': root + '/reviewer-role-round2.md', 'baseline': baseline,
           'trusted_marker': root + '/.t082-trusted'}, open(out, 'w', encoding='utf-8'), indent=2)
PY
printf 'fixture=%s\nmanifest=%s\nbaseline=%s\n' "$ROOT" "$ROOT/manifest.json" "$BASELINE"
