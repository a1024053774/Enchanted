#!/bin/sh
set -eu
ROOT=/Users/luckye/Documents/Code/a2a-wt-t078
BASE=$ROOT/evidence/2026-10-11-batch13/T-078
ROLE=${1:?role}; SCREEN=${2:?screen-id}; KEY=${3:?key}; PURPOSE=${4:?purpose}; LABEL=${5:?selected-label}; BASIS=${6:?basis}; MODE=${7:-}
P1=$BASE/09b-stage-b-ideation-p1-02
ROOT5=$(python3 -c "import json;print(json.load(open('$BASE/09b-stage-a-05/readiness.json'))['root'])")
OUT_SUFFIX=run
[ "$MODE" = "--dry-run" ] && OUT_SUFFIX=dry-run
OUT=$BASE/09b-stage-b1-key-${ROLE}-${SCREEN}-${KEY}-${OUT_SUFFIX}-06
[ ! -e "$OUT" ] || { echo "existing output: $OUT" >&2; exit 2; }
APPROVAL=$(mktemp /tmp/t078-stage-key-approval.XXXXXX.json)
trap 'rm -f "$APPROVAL"' EXIT
python3 -B - "$ROOT5" "$BASE" "$P1" "$ROLE" "$SCREEN" "$KEY" "$PURPOSE" "$LABEL" "$BASIS" "$OUT" "$APPROVAL" <<'PY'
import json,re,subprocess,sys
from pathlib import Path
root,base,p1,out,approval_path=map(Path,[sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[10],sys.argv[11]])
role,screen,key,purpose,label,basis=sys.argv[4:10]
# Find the exact prior screen receipt; never guess a screen file.
rows=[]
for path in p1.rglob('screen.json'):
 try:
  data=json.loads(path.read_text())
  if data.get('screen_id')==screen: rows.append((path,data))
 except Exception: pass
assert len(rows)==1, {'screen_id':screen,'matches':[str(x[0]) for x in rows]}
screen_file=rows[0][0].with_name('screen.bin');assert screen_file.is_file()
m=re.fullmatch(re.escape(role)+r'-s([0-9]+)',screen);assert m
next_screen=f'{role}-s{int(m.group(1))+1}'
source=json.loads((base/'stage-b-ideation-approval-13.json').read_bytes());source.update(approved_by='executor',approval_ref=f'{screen}-{key}',phase='B1',p1_phase='key',p1_args=['--reuse-stage-a','--reuse-api-root',str(root/'roles'/role),'--reuse-readiness-file',str(base/'09b-stage-a-05/readiness.json'),'--launch-label','09b-stage-b1-ideation-04','--key',key,'--purpose',purpose,'--screen-id',screen,'--approval-file',str(approval_path),'--screen-file',str(screen_file),'--next-screen-id',next_screen,'--screen-basis',basis])
source['screen_approvals']=source['screen_approvals']
manifest=json.loads((p1/'09b-stage-b1-ideation-04/process-manifest.json').read_bytes())
source['screen_key_approval']={'launch':manifest['launch'],'session':manifest['session'],'directory':str(root/'repo'),'key':key,'purpose':purpose,'screen_id':screen,'selected_label':label,'approved_by':'executor','approval_ref':f'{screen}-{key}','basis':basis,'screen_file':str(screen_file.resolve())}
(approval_path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n'))
PY
ARGS="--materials $BASE/09b-executable-materials-05 --stage-a $BASE/09b-stage-a-05 --role $ROLE --phase B1 --approval $APPROVAL --output $OUT"
[ "$MODE" = "--dry-run" ] && ARGS="$ARGS --dry-run"
python3 -B "$ROOT/evidence/2026-10-11-batch13/T-078/run-09b-stage-b.py" $ARGS
python3 -B - "$OUT" "$SCREEN" "$KEY" "$OUT" <<'PY'
import json,sys
from pathlib import Path
out=Path(sys.argv[1]);(out/'command.json').write_text(json.dumps({'screen':sys.argv[2],'key':sys.argv[3],'dry_run':True},indent=2)+'\n')
PY
