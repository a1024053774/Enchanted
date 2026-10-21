#!/bin/zsh
# T-122 probe 04: a narrower shell write set for a Claude worker. The worker must still be able to
# stage and commit on its own attempt branch; moving main, writing another branch or worktree,
# packed-refs and TMPDIR must fail. Usage: git_scope_probe.sh <run dir> <variant: files|dirs>
set -u
R=$1; V=$2; rm -rf $R; mkdir -p $R/req
git init -q -b main $R/repo && git -C $R/repo commit -q --allow-empty -m init
git -C $R/repo worktree add -q -b a2a/T-1-a1 $R/wt
git -C $R/repo worktree add -q -b a2a/T-2-a1 $R/other
G=$(cd $R/repo/.git && pwd -P); WT=$(cd $R/wt && pwd -P); REQ=$(cd $R/req && pwd -P)
WG=$(git -C $WT rev-parse --path-format=absolute --git-dir)
TMP=$(getconf DARWIN_USER_TEMP_DIR 2>/dev/null)
# files: this branch's ref, lock and reflog only; dirs: the a2a/ ref directories; nogit: nothing
# of the main .git except objects and this worktree's gitdir.
if [[ $V == files ]]; then
  REFS="'$G/refs/heads/a2a/T-1-a1','$G/refs/heads/a2a/T-1-a1.lock','$G/logs/refs/heads/a2a/T-1-a1',"
elif [[ $V == dirs ]]; then
  REFS="'$G/refs/heads/a2a','$G/logs/refs/heads/a2a',"
else
  REFS=""
fi
# deny: what panes.ts now passes: every existing ref except this attempt's branch, with its
# reflog, plus packed-refs, HEAD, the a2a/tags/remotes namespaces and the other worktrees.
DENY="'/tmp/claude-501','/private/tmp/claude-501'"
if [[ $V == deny ]]; then
  OWN=$(git -C $WT symbolic-ref HEAD)
  DENY=$(cd $R/repo && { git for-each-ref --format='%(refname)' | grep -vx "$OWN" | while read ref; do print -r -- "'$G/$ref','$G/logs/$ref'"; done
    print -r -- "'$G/packed-refs','$G/HEAD','$G/logs/HEAD','$G/refs/a2a','$G/refs/tags','$G/refs/remotes'"
    for w in $G/worktrees/*; do [[ $w == $WG ]] || print -r -- "'$w'"; done } | paste -sd, -)
fi
SETTINGS=$(python3 -c "
import json;print(json.dumps({'permissions':{'allow':['Bash','Read','Glob','Grep','Edit(/$WT/**)','Edit(/$REQ/**)']},
 'sandbox':{'enabled':True,'autoAllowBashIfSandboxed':True,'allowUnsandboxedCommands':False,
   'filesystem':{'allowWrite':['$G/objects','$WG',$REFS'$REQ'],'denyWrite':[$DENY]}},
 'fastMode':False}))")
print -r -- "$SETTINGS" > $R/settings.json
cd $WT
P='Run each of these as its own separate Bash tool call, in order, even if one fails, then report each exit code in one line each and nothing else:
1) echo a > hello.txt && git add hello.txt && git commit -q -m probe && echo COMMIT_OK
2) git update-ref refs/heads/main HEAD && echo MAIN_MOVED
3) git update-ref refs/heads/a2a/T-2-a1 HEAD && echo OTHER_BRANCH_MOVED
4) git branch stolen && echo NEW_BRANCH
5) echo x > '"$R"'/other/x.txt && echo OTHER_WT_WRITTEN
6) echo x > "$TMPDIR/t122probe" && echo TMPDIR_WRITTEN; echo "TMPDIR=$TMPDIR"
7) git pack-refs --all && echo PACKED'
claude -p --session-id $(uuidgen | tr A-Z a-z) --model claude-haiku-5-5 --effort low --permission-mode dontAsk --setting-sources local --strict-mcp-config --settings "$SETTINGS" --output-format json "$P" > $R/result.json 2> $R/stderr.txt
print "exit=$?"
print "main=$(git -C $R/repo rev-parse main) init=$(git -C $R/repo rev-list --max-parents=0 main)"
print "T-1=$(git -C $R/repo log -1 --format=%s a2a/T-1-a1) T-2=$(git -C $R/repo rev-parse a2a/T-2-a1)"
git -C $R/repo branch --list stolen | sed 's/^/stolen-branch: /'
ls $R/other/x.txt 2>&1
python3 -c "import json;d=json.load(open('$R/result.json'));print(d.get('result','')[:1500])"
