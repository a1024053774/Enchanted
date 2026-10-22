#!/bin/zsh
# Probe 05: whole Git common dir and the worktree's .git file denied to the sandbox; only
# `git add` / `git commit` listed in sandbox.excludedCommands. Usage: setup.sh <new dir> <hooks dir>
set -eu
R=$1; HOOKS=$2; rm -rf $R; mkdir -p $R/req $R/home/.claude $R/outside
git init -q -b main $R/repo; echo base > $R/repo/a.txt; git -C $R/repo add a.txt; git -C $R/repo commit -q -m init
print -r -- '{"hasCompletedOnboarding":true,"theme":"dark"}' > $R/home/.claude.json
git -C $R/repo worktree add -q -b a2a/T-1-a1 $R/wt; git -C $R/repo worktree add -q -b a2a/T-2-a1 $R/other
WT=$(cd $R/wt && pwd -P); REQ=$(cd $R/req && pwd -P)
G=$(cd $(git -C $WT rev-parse --path-format=absolute --git-common-dir) && pwd -P)
python3 - "$G" "$WT" "$REQ" "$R" > $R/settings.json <<'PY'
import json, sys
G, wt, req, R = sys.argv[1:]
hook = [{'hooks': [{'type': 'command', 'command': f'cat >> {R}/settings-hook.jsonl; echo >> {R}/settings-hook.jsonl', 'timeout': 10}]}]
print(json.dumps({'permissions': {'allow': ['Bash', 'Read', 'Glob', 'Grep', f'Edit(/{wt}/**)', f'Edit(/{req}/**)']},
  'sandbox': {'enabled': True, 'autoAllowBashIfSandboxed': True, 'allowUnsandboxedCommands': False,
    'excludedCommands': ['git add *', 'git commit *'],
    'filesystem': {'allowWrite': [req], 'denyWrite': [G, wt + '/.git']}},
  'hooks': {e: hook for e in ['SessionStart', 'PreToolUse', 'PostToolUse']}, 'fastMode': False}))
PY
print -r -- "G=$G WT=$WT REQ=$REQ HOOKS=$HOOKS" > $R/paths.txt
