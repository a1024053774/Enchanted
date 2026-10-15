#!/bin/sh
set -eu
ROOT=/Users/luckye/Documents/Code/a2a-wt-t078; BASE=$ROOT/evidence/2026-10-11-batch13/T-078; ROLE=${1:?role}; SCREEN=${2:?screen-id}; MODE=${3:-}; P1=$BASE/09b-stage-b-ideation-p1-02; ROOT5=$(python3 -c "import json;print(json.load(open('$BASE/09b-stage-a-05/readiness.json'))['root'])")
OUT_SUFFIX=run; [ "$MODE" = "--dry-run" ] && OUT_SUFFIX=dry-run
OUT=$BASE/09b-stage-b1-screen-${ROLE}-${SCREEN}-${OUT_SUFFIX}-04; [ ! -e "$OUT" ] || { echo "existing output: $OUT" >&2; exit 2; }
APPROVAL=$(mktemp /tmp/t078-stage-screen-approval.XXXXXX.json); trap 'rm -f "$APPROVAL"' EXIT
python3 -B - "$BASE" "$ROOT5" "$P1" "$ROLE" "$SCREEN" "$APPROVAL" <<'PY'
import json,sys
from pathlib import Path
base,root,p1,role,screen,approval=map(Path,sys.argv[1:]);source=json.loads((base/'stage-b-ideation-approval-13.json').read_bytes());source.update(approved_by='executor',approval_ref=f'{screen}-read-only',phase='B1',p1_phase='screen',p1_args=['--reuse-stage-a','--reuse-api-root',str(root/'roles'/role),'--reuse-readiness-file',str(base/'09b-stage-a-05/readiness.json'),'--launch-label','09b-stage-b1-ideation-04','--screen-id',screen]);approval.write_text(json.dumps(source,ensure_ascii=False,indent=2,default=str)+'\n')
PY
ARGS="--materials $BASE/09b-executable-materials-05 --stage-a $BASE/09b-stage-a-05 --role $ROLE --phase B1 --approval $APPROVAL --output $OUT"; [ "$MODE" = "--dry-run" ] && ARGS="$ARGS --dry-run"; python3 -B "$ROOT/evidence/2026-10-11-batch13/T-078/run-09b-stage-b.py" $ARGS
