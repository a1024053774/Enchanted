#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE CLAUDE_CONFIG_DIR
# Existing auth-only onboarding probe: installed interactive CLI, copied login,
# pretrusted private cwd, protocol replies only, local sink, zero vendor turns.
# The probe refuses unknown startup behavior; it never approves a new screen.
/usr/bin/python3 -B workbench/tests/probe_t093_normal_login.py --run \
  --claude /Users/luckye/.local/bin/claude \
  --prepare-onboarding-state --trust-isolated-cwd \
  --output "${1:-/private/tmp/t108-version-probe-01.json}"
