#!/bin/zsh
# Candidate 4 of T-133 (Codex side) and T-107 #3 (code and tests d0c006ee1), after candidate 3's runs: the daemon's
# PostToolUse guard for Codex was dead (mutant survived) and is gone; the Claude test's after-answer check is fixed.
#   git -C /private/tmp/a2a-t133-c3 checkout --detach d0c006ee1   (node_modules linked to the main checkout's)
# Red runs use d0f89b48a, the commit before candidate 3. At most three runs at once. t132 and t124 ran green on
# candidate 3 and the code they exercise has not changed since; they are not rerun.
set -u
W=/private/tmp/a2a-t133-c3
O=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-107/candidate-4/e2e
CODEX=$W/workbench/tests/test_t133_codex_terminal_controller_e2e.py
CLAUDE=$W/workbench/tests/test_t133_t107_terminal_controller_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $O/$name.json > $O/$name.log 2>&1; echo "$name exit=$?" >> $O/exits.txt; }
run codex-green $CODEX &
run codex-red-parent $CODEX --revision d0f89b48a &
run claude-green $CLAUDE &
wait
run codex-mutant-hooks-not-passed $CODEX --mutant hooks-not-passed &
run codex-mutant-post-hook-passed $CODEX --mutant post-hook-passed &
run codex-mutant-reply-as-message $CODEX --mutant reply-as-message &
wait
run claude-mutant-issue-not-waiting $CLAUDE --mutant issue-not-waiting &
run claude-red-parent $CLAUDE --revision d0f89b48a &
run t107-live-green $W/workbench/tests/test_t107_live_sidebar_e2e.py &
wait
run t133-t134-green $W/workbench/tests/test_t133_t134_records_metrics_e2e.py
