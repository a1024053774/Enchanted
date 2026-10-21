#!/bin/zsh
# Usage: t121run.sh <app path> <port> <out dir> <model>. Isolated app state under /private/tmp; the
# terminal runs the user's own claude with the user's normal login, as in daily use.
set -u
APP=$1; PORT=$2; OUT=$3; MODEL=$4; S=${0:A:h}; SRC=$APP/Contents/Resources/app
F=$(mktemp -d /private/tmp/t121-ui-XXXX); mkdir -p $F/state $F/repos/demo $OUT
git -C $F/repos/demo init -q && git -C $F/repos/demo commit -q --allow-empty -m init
BIN="$APP/Contents/MacOS/${${APP:t}%.app}"
LOG=$F/app.log python3 -c 'import os,subprocess,sys; subprocess.Popen(sys.argv[1:], stdout=open(os.environ["LOG"],"w"), stderr=subprocess.STDOUT, start_new_session=True)' \
  $BIN --state $F/state --user-data $F/state/ui --remote-debugging-port=$PORT
for i in {1..100}; do [[ -S $F/state/control.sock && -f $F/state/desktop-connection.json ]] && break; sleep 0.2; done
node $S/../T-118/register.mts $F/state $F/repos/demo > $OUT/register.log 2>&1
node $S/t121drive.mjs $PORT $OUT $MODEL; RC=$?
node $S/readback.mts $F/state $SRC $OUT/readback.json
pkill -f "$BIN --state $F/state"
print "fixture=$F rc=$RC"
