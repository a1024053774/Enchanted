#!/bin/zsh
# Usage: run.sh <new dir> <hooks dir> <actions.py> [repo core.hooksPath]
set -u
D=${0:A:h}; R=$1; zsh $D/setup.sh $R $2 ${4:-}; source <(sed 's/ /\n/g' $R/paths.txt | sed 's/^/export /')
python3 -c 'import json,sys; G,H,R=sys.argv[1:]; json.dump({"GIT_CONFIG_COUNT":"1","GIT_CONFIG_KEY_0":"core.hooksPath","GIT_CONFIG_VALUE_0":H,
 "A2A_TASK":"T-1","A2A_ATTEMPT":"a1","A2A_SESSION":"s1","A2A_ROLE":"worker","A2A_TOOL":"probe","A2A_NATIVE_SESSION":"n1","A2A_LAUNCH":"L1","A2A_CLI":"Claude Code",
 "GIT_AUTHOR_NAME":"p","GIT_AUTHOR_EMAIL":"p@x","GIT_COMMITTER_NAME":"p","GIT_COMMITTER_EMAIL":"p@x"}, open(R+"/env.json","w"))' $G $HOOKS $R
python3 $3 $G $WT $R > $R/actions.json
PROBE_ENV=$R/env.json python3 $D/scripted.py $WT $R/settings.json $R/actions.json $R/home
echo "== outside dir after run:"; ls -la $R/outside
echo "== refs:"; git -C $R/repo for-each-ref --format='%(refname) %(objectname:short) %(subject)'
echo "== branch log:"; git -C $R/repo log --format='%h %s | task=%(trailers:key=A2A-Task,valueonly,separator=,)' main..a2a/T-1-a1
