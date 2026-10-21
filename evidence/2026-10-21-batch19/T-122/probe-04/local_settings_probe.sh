#!/bin/zsh
# T-122 probe 04b: with --setting-sources local in a linked worktree, which .claude/settings.local.json
# does Claude Code load: the worktree's, the main checkout's, or both? Each file installs a
# SessionStart hook that leaves a marker. PROBE_SOURCES picks the --setting-sources value. Uses the local endpoint from effective_config.py.
set -u
R=$1; rm -rf $R; mkdir -p $R/req
git init -q -b main $R/repo && git -C $R/repo commit -q --allow-empty -m init
git -C $R/repo worktree add -q -b a2a/T-1-a1 $R/wt
for where in repo wt; do mkdir -p $R/$where/.claude
  print -r -- "{\"hooks\":{\"SessionStart\":[{\"hooks\":[{\"type\":\"command\",\"command\":\"touch $R/marker-$where\"}]}]}}" > $R/$where/.claude/settings.local.json; done
print -r -- '{"permissions":{"allow":["Read"]},"sandbox":{"enabled":true,"allowUnsandboxedCommands":false},"fastMode":false}' > $R/settings.json
python3 ${0:A:h}/effective_config.py $R $R/settings.json > $R/effective.json
ls $R/marker-* 2>&1
