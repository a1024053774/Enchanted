#!/bin/zsh
set -euo pipefail

# Controller decision 01 approves prepare-commit-msg and the three native
# hooks for this card. Only real-two-turns starts Codex, with an isolated home;
# all other prepared phases use zero model turns.
# Real launch (later phase) must use the product's exact generated argv:
# codex --no-daemon --no-alt-screen -C <attempt-worktree> -a never
#   --sandbox workspace-write -m gpt-6.1-sol
#   -c 'model_reasoning_effort="xhigh"' -c 'service_tier="fast"'
#   -c 'check_for_update_on_startup=false' -c 'tui.notifications=false'
#   -c 'sandbox_workspace_write.network_access=false' -c 'features.network_proxy=false'
#   -c 'hooks.UserPromptSubmit=[{hooks=[{type="command",command="<node> <cli> --state <fixture-state> signal --launch <launch-id>",timeout=10}]}]'
#   -c 'hooks.Stop=[{hooks=[{type="command",command="<node> <cli> --state <fixture-state> signal --launch <launch-id>",timeout=10}]}]'
#   -c 'hooks.PermissionRequest=[{hooks=[{type="command",command="<node> <cli> --state <fixture-state> signal --launch <launch-id>",timeout=10}]}]'
#   --dangerously-bypass-hook-trust
# Per-process GIT_CONFIG_COUNT=1, GIT_CONFIG_KEY_0=core.hooksPath,
# GIT_CONFIG_VALUE_0=<source>/workbench/hooks; prepare-commit-msg -> hook.py.
# The later actual argv and environment must be saved, not inferred from this
# template. Controller decision 03 and #24 confirm all three real main turns
# are consumed. No further real launch is authorized; the budget ledger rejects it.

if (( $# != 2 )); then
  print -u2 'usage: zsh outside-sandbox.sh <red-focused|red-mutants|red-startup-shutdown|green-startup-shutdown|green-focused|green-attachments|green-checker-counterfactuals|real-two-turns|green-regression|green-mutants> <new-label>'
  exit 2
fi
typeset -r a2a_t076_card="${0:A:h}"
typeset -r a2a_t076_root="${a2a_t076_card:h:h:h:h}"
typeset -r a2a_t076_baseline='18235b2c53610c412b5f4ea53e0e6e5c56d35849'
typeset -r a2a_t076_label="$2"
if [[ "$a2a_t076_label" != [A-Za-z0-9]* || "$a2a_t076_label" == *[^A-Za-z0-9._-]* ]]; then
  print -u2 'label must start with a letter/digit and contain only letters/digits/dot/dash/underscore'
  exit 2
fi
case "$1" in
  red-focused)
    exec python3 -B "$a2a_t076_root/workbench/tests/run_t076_red.py" \
      --baseline "$a2a_t076_baseline" --phase focused \
      --output "$a2a_t076_card/$a2a_t076_label"
    ;;
  red-mutants)
    exec python3 -B "$a2a_t076_root/workbench/tests/run_t076_red.py" \
      --baseline "$a2a_t076_baseline" --phase mutants \
      --recorded "$a2a_t076_root/evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle" \
      --output "$a2a_t076_card/$a2a_t076_label"
    ;;
  red-startup-shutdown|green-startup-shutdown)
    exec python3 -B "$a2a_t076_root/workbench/tests/run_t076_startup_shutdown.py" \
      --mode "${1%%-*}" --output "$a2a_t076_card/$a2a_t076_label"
    ;;
  green-focused|green-attachments|green-checker-counterfactuals|green-regression|green-mutants)
    exec python3 -B "$a2a_t076_root/workbench/tests/run_t076_green.py" \
      --phase "${1#green-}" --output "$a2a_t076_card/$a2a_t076_label"
    ;;
  real-two-turns)
    exec python3 -B "$a2a_t076_root/workbench/tests/run_t076_real.py" \
      --output "$a2a_t076_card/$a2a_t076_label"
    ;;
  *) print -u2 'choose a prepared phase; real-two-turns is single-use and has no automatic retry'; exit 2 ;;
esac
