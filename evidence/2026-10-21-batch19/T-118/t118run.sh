#!/bin/zsh
# Usage: t118run.sh <app path> <port> <out dir>. Isolated state under /private/tmp; never the user's data.
set -u
APP=$1; PORT=$2; OUT=$3; S=${0:A:h}
F=$(mktemp -d /private/tmp/t118-ui-XXXX); mkdir -p $F/state $F/repos/demo $OUT
git -C $F/repos/demo init -q && git -C $F/repos/demo commit -q --allow-empty -m init
BIN="$APP/Contents/MacOS/${${APP:t}%.app}"
LOG=$F/app.log python3 -c 'import os,subprocess,sys; subprocess.Popen(sys.argv[1:], stdout=open(os.environ["LOG"],"w"), stderr=subprocess.STDOUT, start_new_session=True)' \
  $BIN --state $F/state --user-data $F/state/ui --remote-debugging-port=$PORT
for i in {1..100}; do [[ -S $F/state/control.sock && -f $F/state/desktop-connection.json ]] && break; sleep 0.2; done
node $S/register.mts $F/state $F/repos/demo > $OUT/register.log 2>&1
node $S/t118drive.mjs $PORT $OUT $S/frames.py; RC=$?
print "fixture=$F rc=$RC"
