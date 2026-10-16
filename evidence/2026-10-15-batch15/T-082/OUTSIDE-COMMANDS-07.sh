#!/bin/sh
# T-082-1 outside-command batch 07.
# Directly exercises the three T-076 quality properties on this candidate;
# it does not invoke the stale launch-policy baseline fixture or move its
# anchor. No real Codex sessions.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
TMP_ROOT=/private/tmp
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-07-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-07-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
before_q76="$OUTPUT/q76-before.txt"
find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$before_q76"

env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_quality_tracer_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/t076-property-tracer" \
  --case tracer_wrong_candidate \
  --case tracer_reused_native \
  --case tracer_writer_cannot_review \
  > "$OUTPUT/t076-property-tracer.stdout.txt" 2> "$OUTPUT/t076-property-tracer.stderr.txt"
exit_code=$?

find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$OUTPUT/q76-after.txt"
comm -13 "$before_q76" "$OUTPUT/q76-after.txt" > "$OUTPUT/q76-new.txt"
if [ -s "$OUTPUT/q76-new.txt" ]; then
  tar -czf "$OUTPUT/q76-artifacts.tar.gz" -C "$TMP_ROOT" \
    $(sed "s#^$TMP_ROOT/##" "$OUTPUT/q76-new.txt") 2> "$OUTPUT/q76-archive.stderr.txt"
  archive_exit=$?
  if [ "$archive_exit" -ne 0 ] && [ "$exit_code" -eq 0 ]; then exit_code=$archive_exit; fi
  while IFS= read -r path; do
    [ -n "$path" ] && rm -rf -- "$path"
  done < "$OUTPUT/q76-new.txt"
else
  : > "$OUTPUT/q76-artifacts.none"
fi

cat > "$OUTPUT/property-map.json" <<'EOF'
{
  "tracer_wrong_candidate": ["TRACER-REVIEW-CANDIDATE", "review_candidate_mismatch"],
  "tracer_reused_native": ["TRACER-REVIEW-REUSE", "review_native_session_reused"],
  "tracer_writer_cannot_review": ["TRACER-WRITER-REVIEW", "writer cannot deliver review_submit"]
}
EOF
cat > "$OUTPUT/command.json" <<EOF
{
  "root": "$ROOT",
  "output": "$OUTPUT",
  "real_codex_turns": 0,
  "t076_anchor_moved": false,
  "audit_logic_modified": false,
  "exit_code": $exit_code
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$exit_code"
exit "$exit_code"
