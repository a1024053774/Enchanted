#!/bin/zsh
# Candidate 3 of T-133 (Codex side, option A) and T-107 #3/#4 for Codex (code af838d77e; tests, README and copy as of ddee5f5e8).
# User 2026-10-22: "1. A 2. 一二都要." Run from a clean detached worktree:
#   git worktree add --detach /private/tmp/a2a-t133-c3 ddee5f5e8; ln -s <main checkout>/workbench/node_modules /private/tmp/a2a-t133-c3/workbench/node_modules
# Red runs use d0f89b48a, the commit before candidate 3. At most three runs at once.
set -u
W=/private/tmp/a2a-t133-c3
O=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-107/candidate-3/e2e
CODEX=$W/workbench/tests/test_t133_codex_terminal_controller_e2e.py
CLAUDE=$W/workbench/tests/test_t133_t107_terminal_controller_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $O/$name.json > $O/$name.log 2>&1; echo "$name exit=$?" >> $O/exits.txt; }
run codex-green $CODEX &
run codex-red-parent $CODEX --revision d0f89b48a &
run claude-green $CLAUDE &
wait
run codex-mutant-hooks-not-passed $CODEX --mutant hooks-not-passed &
run codex-mutant-accepted-ends-wait $CODEX --mutant accepted-ends-wait &
run codex-mutant-reply-as-message $CODEX --mutant reply-as-message &
wait
run claude-mutant-issue-not-waiting $CLAUDE --mutant issue-not-waiting &
run claude-red-parent $CLAUDE --revision d0f89b48a &
run t107-live-green $W/workbench/tests/test_t107_live_sidebar_e2e.py &
wait
run t133-t134-green $W/workbench/tests/test_t133_t134_records_metrics_e2e.py &
run t132-green $W/workbench/tests/test_t132_issues_panel_e2e.py &
run t124-codex-controller-green $W/workbench/tests/test_t124_controller_e2e.py --controller-cli codex &
wait
