#!/bin/sh
# usage: bs6.sh <screen-id>   A-07 ideation read-only screen; approvals kept in evidence (executor-written)
set -eu
. "$(dirname "$0")/a7.env"
SID=$1; D=$APPDIR/$SID-screen-run; mkdir -p $APPDIR; mkdir "$D"
python3 - "$SRCAPP" "$D" "$SID" "$ROOT" "$READY" "$LABEL" <<'PY'
import json,sys
src,d,sid,root,ready,label=sys.argv[1:]
st=json.load(open(src))
st.update(approved_by='executor',approval_ref=f'主控 T-078 09B A-07 B1 {sid} read-only screen (no key)',p1_phase='screen',
 p1_args=['--reuse-stage-a','--reuse-api-root',root+'/roles/ideation','--reuse-readiness-file',ready,'--screen-id',sid,'--launch-label',label])
open(d+'/stage-approval.json','w').write(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
PY
cd $WT; rc=0
python3 -B $BASE/run-09b-stage-b.py --materials $MAT --stage-a $STAGEA --role ideation --phase B1 --approval $D/stage-approval.json --output $D/$SID-screen-run || rc=$?
echo "runner rc=$rc"; wc -c < $P1/$SID-screen-run/screen.bin
