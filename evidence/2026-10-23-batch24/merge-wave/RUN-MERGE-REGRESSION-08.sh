#!/bin/zsh
# Batch24 wave regression before T-164: the 07 set plus offline T-156..T-165 tests (no vendor model turns; T-163 needs real Haiku and is excluded).
# Runs in a detached worktree of the given revision; each summary goes to a new directory.
set -u
REV=${1:?revision}
W=/Users/luckye/Documents/Code/a2a-merge-check
OUT=/Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch24/merge-wave/run-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$OUT" || exit 2
[ -d $W ] || { git -C /Users/luckye/Documents/Code/a2a worktree add --detach $W $REV && cp -cR /Users/luckye/Documents/Code/a2a/workbench/node_modules $W/workbench/node_modules; } || exit 2
git -C $W checkout -q --detach $REV || exit 2
cd $W || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-merge-pycache
run() { local name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; echo "$name exit=$?" | tee -a "$OUT/exits.txt"; }
run t140-green python3 workbench/tests/test_t140_extra_dirs_e2e.py --summary "$OUT/t140-green.json" &
run t091-migrated node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs --summary "$OUT/t091-migrated.json" &
run t078-migrated python3 evidence/2026-10-23-batch23/T-151/RUN-CHECKS-01.py --summary "$OUT/t078-migrated.json" &
run t146-green python3 workbench/tests/test_t146_session_state_e2e.py --summary "$OUT/t146-green.json" &
run t139-t143-candidate python3 workbench/tests/test_t139_t143_views_perf_e2e.py --summary "$OUT/t139-t143-candidate.json" &
wait
run t146-native-green python3 workbench/tests/test_t146_cli_exit_probe.py --summary "$OUT/t146-native-green.json" &
run t137 python3 workbench/tests/test_t137_reflect_e2e.py --summary "$OUT/t137.json" &
run t131 python3 workbench/tests/test_t131_parallel_workers_e2e.py --summary "$OUT/t131.json" &
wait
run t127 python3 workbench/tests/test_t127_codex_home_e2e.py --summary "$OUT/t127.json" &
run t107 python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary "$OUT/t107.json" &
run t133-t107 python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary "$OUT/t133-t107.json" &
wait
run t111 node workbench/tests/test_t111_flow.mjs "$OUT/t111.json" .
run t146-session-end node workbench/tests/test_t146_session_end.mjs "$OUT/t146-session-end.json" .
run t146-reviewer-hooks node workbench/tests/test_t146_reviewer_hooks.mjs "$OUT/t146-reviewer-hooks.json" .
run t143-retained-focus node workbench/tests/test_t143_retained_focus.mjs "$OUT/t143-retained-focus.json"
run t139-selection node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$OUT/t139-selection.json"
run t139-layout-store node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$OUT/t139-layout-store.json"
run t139-terminal-catalog node workbench/tests/test_t139_terminal_catalog.mjs "$OUT/t139-terminal-catalog.json"
run t140-project-events node workbench/tests/test_t140_project_events.ts
run t145-green python3 workbench/tests/test_t145_mouse_reports_e2e.py --summary "$OUT/t145-green.json"
run t145-protocol node workbench/tests/test_t145_protocol_input.mjs "$OUT/t145-protocol.json"
run t146-ended-projection node workbench/tests/test_t146_ended_projection.mjs "$OUT/t146-ended-projection.json" .
run t144-green python3 workbench/tests/test_t144_flow_page_e2e.py --summary "$OUT/t144-green.json"
run t144-projection node workbench/tests/test_t144_flow_projection.mjs "$OUT/t144-projection.json" .
run t146-release-visibility python3 workbench/tests/test_t146_release_visibility_e2e.py --summary "$OUT/t146-release-visibility.json"
run t146-released-projection node workbench/tests/test_t146_released_projection.mjs "$OUT/t146-released-projection.json" .
run t121 python3 workbench/tests/test_t121_role_request_e2e.py --summary "$OUT/t121.json"
run t141-green python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --summary "$OUT/t141-green.json"
run t141-launch-contract node workbench/tests/test_t141_launch_contract.mjs "$OUT/t141-launch-contract.json"
run t141-reviewer-contract node workbench/tests/test_t141_reviewer_contract.mjs "$OUT/t141-reviewer-contract.json"
run t141-startup-contract node workbench/tests/test_t141_startup_signal.mjs "$OUT/t141-startup-contract.json"
run t142-green python3 workbench/tests/test_t142_terminal_open_e2e.py --summary "$OUT/t142-green.json"
run t138-green python3 workbench/tests/test_t138_ime_e2e.py --summary "$OUT/t138-green.json"
run t156 python3 -B workbench/tests/test_t156_quality_host_credentials.py --output "$OUT/t156.json"
run t157-identity python3 -B workbench/tests/test_t157_turn_identity.py --summary "$OUT/t157-identity.json"
run t157-stop-input python3 -B workbench/tests/test_t157_stop_input_e2e.py --summary "$OUT/t157-stop-input.json"
run t157-recover python3 -B workbench/tests/test_t157_stale_turn_e2e.py --scenario recover --summary "$OUT/t157-recover.json"
run t157-expired python3 -B workbench/tests/test_t157_stale_turn_e2e.py --scenario expired --summary "$OUT/t157-expired.json"
run t158 python3 -B workbench/tests/test_t158_revise_retry_e2e.py --summary "$OUT/t158.json"
run t159 python3 -B workbench/tests/test_t159_split_e2e.py --summary "$OUT/t159.json"
run t160-idle python3 -B workbench/tests/test_t160_protocol_idle.py --summary "$OUT/t160-idle.json"
run t160-recovery python3 -B workbench/tests/test_t160_review_recovery_e2e.py --summary "$OUT/t160-recovery.json"
run t161 python3 -B workbench/tests/test_t161_readonly_role_e2e.py --summary "$OUT/t161.json"
run t162 python3 -B workbench/tests/test_t162_role_records_metrics_e2e.py --summary "$OUT/t162.json"
run t165 python3 -B workbench/tests/test_t165_queued_stop_e2e.py --summary "$OUT/t165.json"
run build node workbench/app/build.mjs --slot merge-check-$(date -u +%Y%m%dT%H%M%SZ)
echo "OUT=$OUT"
