#!/bin/sh
# usage: bk6.sh <screen-id> <key> <purpose> <selected_label> <basis> [--dry-run]   A-07 ideation one key
set -eu
. "$(dirname "$0")/a7.env"
SCREEN=$1; KEY=$2; PURPOSE=$3; SEL=$4; BASIS=$5; MODE=${6:-}
SUF=run; [ "$MODE" = --dry-run ] && SUF=dry
D=$APPDIR/$SCREEN-$KEY-$SUF; mkdir -p $APPDIR; mkdir "$D"
python3 -B - "$SCREEN" "$KEY" "$PURPOSE" "$SEL" "$BASIS" "$D" "$P1" "$ROOT" "$SRCAPP" "$READY" "$LABEL" <<'PY'
import json,re,sys
from pathlib import Path
screen,key,purpose,sel,basis,d,p1,root,src,ready,label=sys.argv[1:]
d,p1=Path(d),Path(p1)
rows=[p for p in p1.rglob('screen.json') if json.loads(p.read_text()).get('screen_id')==screen]
assert len(rows)==1,(screen,[str(r) for r in rows])
sf=rows[0].with_name('screen.bin')
n=int(re.fullmatch(r'ideation-s([0-9]+)',screen).group(1))
man=json.loads((p1/label/'process-manifest.json').read_text())
ref=f'主控 T-078 09B A-07 B1 {screen} {key}'
ska={'launch':man['launch'],'session':man['session'],'directory':root+'/repo','key':key,'purpose':purpose,'screen_id':screen,
     'selected_label':sel,'approved_by':'executor','approval_ref':ref,'basis':basis,'screen_file':str(sf)}
(d/'screen-key-approval.json').write_text(json.dumps(ska,ensure_ascii=False,indent=2)+'\n')
st=json.load(open(src))
st.update(approved_by='executor',approval_ref=ref,p1_phase='key',p1_args=['--reuse-stage-a','--reuse-api-root',root+'/roles/ideation',
  '--reuse-readiness-file',ready,'--launch-label',label,'--key',key,'--purpose',purpose,
  '--screen-id',screen,'--approval-file',str(d/'screen-key-approval.json'),'--screen-file',str(sf),'--next-screen-id',f'ideation-s{n+1}'])
(d/'stage-approval.json').write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n')
PY
ARGS="--materials $MAT --stage-a $STAGEA --role ideation --phase B1 --approval $D/stage-approval.json --output $D/$SCREEN-$KEY-$SUF"
[ "$MODE" = --dry-run ] && ARGS="$ARGS --dry-run"
cd $WT; rc=0; python3 -B $BASE/run-09b-stage-b.py $ARGS || rc=$?; echo "runner rc=$rc"
