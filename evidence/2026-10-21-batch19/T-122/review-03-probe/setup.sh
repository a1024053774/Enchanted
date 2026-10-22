#!/bin/zsh
# Review 03: implementation's settings shape: denyWrite = [common dir] only, excludedCommands git add/commit.
# Usage: setup.sh <new dir> <hooks dir> [hooksPath-in-repo-config]
set -eu
R=$1; HOOKS=$2; RHP=${3:-}; rm -rf $R; mkdir -p $R/req $R/home/.claude $R/outside
git init -q -b main $R/repo; echo base > $R/repo/a.txt; git -C $R/repo add a.txt; git -C $R/repo -c user.name=p -c user.email=p@x commit -q -m init
[[ -n $RHP ]] && git -C $R/repo config core.hooksPath $RHP
print -r -- '{"hasCompletedOnboarding":true,"theme":"dark"}' > $R/home/.claude.json
printf '[user]\n\tname = p\n\temail = p@x\n[filter "lfs"]\n\tclean = git-lfs clean -- %%f\n\tsmudge = git-lfs smudge -- %%f\n\tprocess = git-lfs filter-process\n\trequired = true\n' > $R/home/.gitconfig
git -C $R/repo worktree add -q -b a2a/T-1-a1 $R/wt
WT=$(cd $R/wt && pwd -P); REQ=$(cd $R/req && pwd -P)
G=$(cd $(git -C $WT rev-parse --path-format=absolute --git-common-dir) && pwd -P)
python3 - "$G" "$WT" "$REQ" "$R" > $R/settings.json <<'PY'
import json, sys
G, wt, req, R = sys.argv[1:]
print(json.dumps({'permissions': {'allow': ['Bash', 'Read', 'Glob', 'Grep', f'Edit(/{wt}/**)', f'Edit(/{req}/**)']},
  'sandbox': {'enabled': True, 'autoAllowBashIfSandboxed': True, 'allowUnsandboxedCommands': False,
    'excludedCommands': ['git add *', 'git commit *'],
    'filesystem': {'allowWrite': [req], 'denyWrite': [G]}}, 'fastMode': False}))
PY
print -r -- "G=$G WT=$WT REQ=$REQ HOOKS=$HOOKS" > $R/paths.txt
