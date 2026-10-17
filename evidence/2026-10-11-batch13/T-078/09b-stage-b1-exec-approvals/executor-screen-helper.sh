#!/bin/sh
# usage: bs.sh <screen-id>   read-only screen of ideation; executor-written approval kept in evidence
set -eu
SID=$1; BASE=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
D=$BASE/09b-stage-b1-exec-approvals/$SID-screen-run; mkdir "$D"
python3 - "$BASE" "$D" "$SID" <<'PY'
import json,sys
base,d,sid=sys.argv[1:]
st=json.load(open(base+'/stage-b-ideation-approval-13.json'))
a=st['p1_args'];a[a.index('--screen-id')+1]=sid
st.update(approved_by='executor',approval_ref=f'主控 T-078 09B B1 {sid} read-only screen (no key)',p1_args=a)
open(d+'/stage-approval.json','w').write(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
PY
cd /Users/luckye/Documents/Code/a2a-wt-t078; rc=0
python3 -B $BASE/run-09b-stage-b.py --materials $BASE/09b-executable-materials-05 --stage-a $BASE/09b-stage-a-05 --role ideation --phase B1 --approval $D/stage-approval.json --output $D/$SID-screen-run || rc=$?
echo "runner rc=$rc"; wc -c < $BASE/09b-stage-b-ideation-p1-02/$SID-screen-run/screen.bin
