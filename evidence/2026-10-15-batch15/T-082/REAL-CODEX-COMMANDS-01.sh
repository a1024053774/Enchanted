#!/bin/sh
# T-082 real-Codex run draft. Review-only by default; do not execute yet.
# This file intentionally has no provider invocation until the controller
# approves the exact fixture, hook authorization, and turn allocation.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)

cat <<EOF
T-082 real-run draft (review only)
root=$ROOT
planned real turns: <=4 (boundary proof + one delivery review)
model: gpt-6.1-sol
effort: xhigh
service_tier: default
codex_version: codex-cli 0.162.1

Before execution, the controller must provide:
  1. an explicit hook-authorization decision file for each turn;
  2. an isolated CODEX_HOME under /tmp containing only a copied auth.json;
  3. a frozen candidate commit and a minimal fixture-root allowlist;
  4. a fresh output directory and a cleanup/readback plan.

The eventual invocation must use:
  codex --no-daemon --no-alt-screen -C <candidate_workspace> -a never \\
    --sandbox workspace-write -m gpt-6.1-sol \\
    -c 'model_reasoning_effort="xhigh"' -c 'service_tier="default"' \\
    -c check_for_update_on_startup=false -c tui.notifications=false \\
    -c sandbox_workspace_write.network_access=false \\
    -c features.network_proxy=false \\
    -c sandbox_workspace_write.exclude_slash_tmp=true \\
    -c sandbox_workspace_write.exclude_tmpdir_env_var=true \\
    --dangerously-bypass-hook-trust

No real run is started by this draft.
EOF
exit 2
