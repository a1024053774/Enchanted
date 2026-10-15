#!/bin/sh
# T-082-1 outside-command batch 06.
# Uses only this worktree. It proves the T-076 controlled fixtures first,
# records the unchanged source-audit gate, then runs the candidate launch and
# T-077/T-082 checks. No MAIN_ROOT, remote, or real Codex session.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
TMP_ROOT=/private/tmp
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-06-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-06-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
before_q76="$OUTPUT/q76-before.txt"
find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$before_q76"
overall=0

run_step() {
  name=$1
  expected=$2
  shift 2
  "$@" > "$OUTPUT/$name.stdout.txt" 2> "$OUTPUT/$name.stderr.txt"
  rc=$?
  cat > "$OUTPUT/$name.command.json" <<EOF
{
  "name": "$name",
  "argv": "$(printf '%s ' "$@" | sed 's/[[:space:]]*$//')",
  "exit_code": $rc,
  "expected_exit": $expected
}
EOF
  if [ "$rc" -ne "$expected" ]; then overall=1; fi
}

# Fixture preflight: no source audit, no red/green claim yet.
run_step fixture-tracer 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_quality_tracer_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/fixture-tracer" --case tracer_success
run_step fixture-launch-policy 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_quality_tracer_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/fixture-launch-policy" --case tracer_launch_policy_reviewer

# The unchanged T-076 quality runner must reject this unfrozen dirty candidate
# at its own source-audit gate. Preserve that receipt; do not weaken the audit.
run_step t076-quality-source-audit 1 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/run_t076_quality_green.py" \
  --output "$OUTPUT/t076-quality-source-audit"
python3 -B - "$OUTPUT/t076-quality-source-audit/run.json" \
  > "$OUTPUT/t076-quality-audit-receipt.json" 2> "$OUTPUT/t076-quality-audit-receipt.stderr.txt" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding='utf-8'))
expected = "Source audit failed or original acceptance assertions changed."
if expected not in str(value.get('error')):
    raise SystemExit(json.dumps({'status': 'FAIL', 'error': value.get('error')}, ensure_ascii=False))
print(json.dumps({'status': 'PASS', 'audit_receipt': value.get('error')}, ensure_ascii=False, indent=2))
PY
if [ "$?" -ne 0 ]; then overall=1; fi

run_step t076-launch-policy-candidate 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/run_t076_launch_policy.py" \
  --output "$OUTPUT/t076-launch-policy-candidate"
run_step t077-review-worktree-candidate 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_review_worktree_lifecycle_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/t077-review-worktree-candidate"
run_step t082-boundary-candidate 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/run_t082_boundary.py" \
  --source "$ROOT" --output "$OUTPUT/t082-boundary-candidate"

find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$OUTPUT/q76-after.txt"
comm -13 "$before_q76" "$OUTPUT/q76-after.txt" > "$OUTPUT/q76-new.txt"
if [ -s "$OUTPUT/q76-new.txt" ]; then
  tar -czf "$OUTPUT/q76-artifacts.tar.gz" -C "$TMP_ROOT" \
    $(sed "s#^$TMP_ROOT/##" "$OUTPUT/q76-new.txt") 2> "$OUTPUT/q76-archive.stderr.txt"
  rc=$?
  if [ "$rc" -ne 0 ]; then overall=1; fi
  while IFS= read -r path; do
    [ -n "$path" ] && rm -rf -- "$path"
  done < "$OUTPUT/q76-new.txt"
else
  : > "$OUTPUT/q76-artifacts.none"
fi

cat > "$OUTPUT/command.json" <<EOF
{
  "root": "$ROOT",
  "output": "$OUTPUT",
  "real_codex_turns": 0,
  "audit_logic_modified": false,
  "d3_patch": "$SCRIPT_DIR/t076-assertion-changes.patch",
  "exit_code": $overall
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$overall"
exit "$overall"
