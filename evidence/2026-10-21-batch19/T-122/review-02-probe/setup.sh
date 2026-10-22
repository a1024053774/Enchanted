#!/bin/zsh
# Review-02: worker launch as panes.ts c6120a562 builds it (claudeArgv + workerGitDenied), all refs
# packed, user/project/local settings each with a marker hook; a later attempt worktree after launch.
set -eu
R=$1; rm -rf $R; mkdir -p $R/req $R/home/.claude $R/outside
git init -q -b main $R/repo; mkdir -p $R/repo/.claude
mk() { print -r -- "{\"hooks\":{\"SessionStart\":[{\"hooks\":[{\"type\":\"command\",\"command\":\"touch $R/marker-$1\"}]}],\"PreToolUse\":[{\"hooks\":[{\"type\":\"command\",\"command\":\"touch $R/marker-$1\"}]}]},\"permissions\":{\"allow\":[\"Write\",\"Edit\"]}}"; }
mk project > $R/repo/.claude/settings.json
echo base > $R/repo/a.txt; git -C $R/repo add a.txt .claude/settings.json; git -C $R/repo commit -q -m init
mk local > $R/repo/.claude/settings.local.json; mk user > $R/home/.claude/settings.json
print -r -- '{"hasCompletedOnboarding":true,"theme":"dark"}' > $R/home/.claude.json
git -C $R/repo worktree add -q -b a2a/T-1-a1 $R/wt; git -C $R/repo worktree add -q -b a2a/T-2-a1 $R/other
git -C $R/repo pack-refs --all
WT=$(cd $R/wt && pwd -P); REQ=$(cd $R/req && pwd -P)
G=$(cd $(git -C $WT rev-parse --path-format=absolute --git-common-dir) && pwd -P)
OWN=$(cd $(git -C $WT rev-parse --path-format=absolute --git-dir) && pwd -P)
python3 - "$G" "$OWN" "$(git -C $WT symbolic-ref HEAD)" "$WT" "$REQ" "$R" > $R/settings.json <<'EOF'
import json, os, subprocess, sys
G, own, br, wt, req, R = sys.argv[1:]
refs = [r for r in subprocess.check_output(['git', '-C', wt, 'for-each-ref', '--format=%(refname)'], text=True).split('\n') if r and r != br]
deny = [p for ref in refs for p in (os.path.join(G, ref), os.path.join(G, 'logs', ref))]
deny += [os.path.join(G, p) for p in ['packed-refs', 'HEAD', 'logs/HEAD', 'refs/a2a', 'refs/tags', 'refs/remotes']]
deny += [p for p in (os.path.join(G, 'worktrees', n) for n in os.listdir(os.path.join(G, 'worktrees'))) if p != own]
hook = [{'hooks': [{'type': 'command', 'command': f'cat >> {R}/settings-hook.jsonl; echo >> {R}/settings-hook.jsonl', 'timeout': 10}]}]
print(json.dumps({'permissions': {'allow': ['Bash', 'Read', 'Glob', 'Grep', f'Edit(/{wt}/**)', f'Edit(/{req}/**)']},
  'sandbox': {'enabled': True, 'autoAllowBashIfSandboxed': True, 'allowUnsandboxedCommands': False, 'filesystem': {'allowWrite': [req], 'denyWrite': deny}},
  'hooks': {e: hook for e in ['SessionStart', 'UserPromptSubmit', 'Stop', 'PermissionRequest', 'PreToolUse', 'PostToolUse']}, 'fastMode': False}))
EOF
git -C $R/repo worktree add -q -b a2a/T-3-a1 $R/later   # launched after this worker
