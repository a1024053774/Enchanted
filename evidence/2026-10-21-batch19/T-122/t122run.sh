#!/bin/zsh
# Usage: t122run.sh <app path> <port> <out dir> <model>. Isolated app state under /private/tmp; the
# terminal runs the user's own claude with the user's normal login, as in daily use, and the backend
# starts the worker and reviewer with the user's claude and login (T-122 product launch config).
set -u
APP=$1; PORT=$2; OUT=$3; MODEL=$4; S=${0:A:h}; SRC=$APP/Contents/Resources/app
F=$(mktemp -d /private/tmp/t122-ui-XXXX); mkdir -p $F/state $F/repos/demo $OUT
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
node $S/../T-118/register.mts $F/state $R > $OUT/register.log 2>&1
# Files a2a must never write; the CLI's own ~/.claude.json and session transcripts are normal CLI use.
config_facts() { for f in ~/.claude/settings.json ~/.claude/settings.local.json ~/.codex/config.toml; do stat -f '%N %z %m' $f 2>/dev/null || print "$f absent"; done }
config_facts > $OUT/user-config-before.txt
node $S/t122drive.mjs $PORT $OUT $MODEL $F/state $SRC $R; RC=$?
config_facts > $OUT/user-config-after.txt
cmp -s $OUT/user-config-before.txt $OUT/user-config-after.txt && print same > $OUT/user-config-compare.txt || print changed > $OUT/user-config-compare.txt
git -C $R log --format='%H %s%n%(trailers:key=A2A-Native-Session,key=A2A-Launch,key=A2A-Role,key=A2A-Model,key=A2A-Effort)' main > $OUT/git-main-log.txt
git -C $R ls-tree --name-only main > $OUT/git-main-files.txt
node $S/readback.mts $F/state $SRC $OUT/readback.json
pkill -f "$BIN --state $F/state"
print "fixture=$F rc=$RC"
