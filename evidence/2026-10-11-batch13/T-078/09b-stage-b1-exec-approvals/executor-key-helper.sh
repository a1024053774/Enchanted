#!/bin/sh
# usage: bk.sh <screen-id> <key> <purpose> <selected_label> <basis> [--dry-run]
# Executor-written: one key on ideation via run-09b-stage-b.py; approvals persisted in evidence.
set -eu
SCREEN=$1; KEY=$2; PURPOSE=$3; LABEL=$4; BASIS=$5; MODE=${6:-}
WT=/Users/luckye/Documents/Code/a2a-wt-t078
BASE=$WT/evidence/2026-10-11-batch13/T-078
P1=$BASE/09b-stage-b-ideation-p1-02
A5=/private/tmp/t078-2-09b-run-94_wksxv
SUF=run; [ "$MODE" = --dry-run ] && SUF=dry
D=$BASE/09b-stage-b1-exec-approvals/$SCREEN-$KEY-$SUF
mkdir -p $BASE/09b-stage-b1-exec-approvals; mkdir "$D"
python3 -B - "$SCREEN" "$KEY" "$PURPOSE" "$LABEL" "$BASIS" "$D" "$BASE" "$P1" "$A5" <<'PY'
import json,re,sys
from pathlib import Path
screen,key,purpose,label,basis,d,base,p1,a5=sys.argv[1:]
d,base,p1=Path(d),Path(base),Path(p1)
rows=[p for p in p1.rglob('screen.json') if json.loads(p.read_text()).get('screen_id')==screen]
assert len(rows)==1,(screen,[str(r) for r in rows])
sf=rows[0].with_name('screen.bin')
n=int(re.fullmatch(r'ideation-s([0-9]+)',screen).group(1))
man=json.loads((p1/'09b-stage-b1-ideation-04/process-manifest.json').read_text())
ref=f'主控 T-078 09B B1 {screen} {key}'
ska={'launch':man['launch'],'session':man['session'],'directory':a5+'/repo','key':key,'purpose':purpose,'screen_id':screen,
     'selected_label':label,'approved_by':'executor','approval_ref':ref,'basis':basis,'screen_file':str(sf)}
(d/'screen-key-approval.json').write_text(json.dumps(ska,ensure_ascii=False,indent=2)+'\n')
st=json.loads((base/'stage-b-ideation-approval-13.json').read_text())
st.update(approved_by='executor',approval_ref=ref,p1_phase='key',p1_args=['--reuse-stage-a','--reuse-api-root',a5+'/roles/ideation',
  '--reuse-readiness-file',str(base/'09b-stage-a-05/readiness.json'),'--launch-label','09b-stage-b1-ideation-04','--key',key,'--purpose',purpose,
  '--screen-id',screen,'--approval-file',str(d/'screen-key-approval.json'),'--screen-file',str(sf),'--next-screen-id',f'ideation-s{n+1}'])
(d/'stage-approval.json').write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
PY
ARGS="--materials $BASE/09b-executable-materials-05 --stage-a $BASE/09b-stage-a-05 --role ideation --phase B1 --approval $D/stage-approval.json --output $D/$SCREEN-$KEY-$SUF"
[ "$MODE" = --dry-run ] && ARGS="$ARGS --dry-run"
cd $WT; rc=0; python3 -B $BASE/run-09b-stage-b.py $ARGS || rc=$?; echo "runner rc=$rc"
