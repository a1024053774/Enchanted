#!/bin/zsh
# Usage: t127run.sh <app path> <port> <out dir> <model>. Isolated app state under /private/tmp; the
# terminal runs the user's own claude with the user's normal login, as in daily use. The backend starts
# the Codex worker and reviewer with the user's codex in the user's own ~/.codex (T-127 product launch
# config; user 2026-10-22: "用我的 ~/.codex", "gpt-6.1-sol low").
set -u
APP=$1; PORT=$2; OUT=$3; MODEL=$4; S=${0:A:h}; SRC=$APP/Contents/Resources/app
F=$(mktemp -d /private/tmp/t127-ui-XXXX); mkdir -p $F/state $F/repos/demo $OUT
R=$F/repos/demo
git -C $R init -q -b main
print 'demo' > $R/README.md
# gui-05: the reviewer rightly refused an oracle that only checked the file exists; check the content.
print 'import pathlib, sys\np = pathlib.Path("hello.txt")\nsys.exit(0 if p.is_file() and not p.is_symlink() and p.read_bytes() == b"hello\\n" else 1)' > $R/check.py
git -C $R add README.md check.py && git -C $R commit -q -m init
BIN="$APP/Contents/MacOS/${${APP:t}%.app}"
LOG=$F/app.log python3 -c 'import os,subprocess,sys; subprocess.Popen(sys.argv[1:], stdout=open(os.environ["LOG"],"w"), stderr=subprocess.STDOUT, start_new_session=True)' \
  $BIN --state $F/state --user-data $F/state/ui --remote-debugging-port=$PORT
for i in {1..100}; do [[ -S $F/state/control.sock && -f $F/state/desktop-connection.json ]] && break; sleep 0.2; done
node $S/../../2026-10-21-batch19/T-118/register.mts $F/state $R > $OUT/register.log 2>&1
# The reviewer runs on its role setting, not the card; both roles use the model the user chose for this run.
for role in worker reviewer; do
  ELECTRON_RUN_AS_NODE=1 A2A_OPERATOR_CREDENTIAL=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["credential"])' $F/state/desktop-connection.json) \
    $BIN $SRC/src/gates/cli.ts --state $F/state execution_settings_save --role $role --model gpt-6.1-sol --effort low --fast false >> $OUT/settings.log 2>&1
done
# Files a2a must never write; the CLI's own ~/.claude.json and session transcripts are normal CLI use.
config_facts() { for f in ~/.claude/settings.json ~/.claude/settings.local.json ~/.codex/config.toml ~/.codex/rules/default.rules ~/.codex/hooks.json; do stat -f '%N %z %m' $f 2>/dev/null || print "$f absent"; done }
config_facts > $OUT/user-config-before.txt
START=$(date +%s)
# Codex itself may record TUI state in config.toml; the copy is kept outside the evidence (it holds the user's settings).
cp ~/.codex/config.toml $F/codex-config-before.toml
node $S/t127drive.mjs $PORT $OUT $MODEL $F/state $SRC $R; RC=$?
config_facts > $OUT/user-config-after.txt
cmp -s $OUT/user-config-before.txt $OUT/user-config-after.txt && print same > $OUT/user-config-compare.txt || print changed > $OUT/user-config-compare.txt
# Only the changed lines' section names and keys go into the evidence; a trust entry for the fixture would name $F.
diff $F/codex-config-before.toml ~/.codex/config.toml | grep -E '^[<>] *(\[|[A-Za-z_."-]+ *=)' | sed -E 's/=.*/= …/' > $OUT/codex-config-changed-keys.txt
grep -c "$F" ~/.codex/config.toml > $OUT/codex-config-fixture-mentions.txt
# The sessions this run left in the user's own ~/.codex: file name and the folder the session opened, nothing else.
python3 -c 'import json,sys,pathlib
for f in sorted(pathlib.Path.home().joinpath(".codex/sessions").rglob("*.jsonl")):
    if f.stat().st_mtime < float(sys.argv[2]): continue
    first = json.loads(f.open().readline() or "{}")
    cwd = (first.get("payload") or {}).get("cwd", "")
    if cwd.startswith(sys.argv[1]): print(f.name, cwd)' $F $START > $OUT/user-codex-sessions.txt
git -C $R log --format='%H %s%n%(trailers:key=A2A-Native-Session,key=A2A-Launch,key=A2A-Role,key=A2A-Model,key=A2A-Effort)' main > $OUT/git-main-log.txt
git -C $R ls-tree --name-only main > $OUT/git-main-files.txt
node $S/readback.mts $F/state $SRC $OUT/readback.json
pkill -f "$BIN --state $F/state"
print "fixture=$F rc=$RC"
