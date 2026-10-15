#!/bin/sh
# T-082-1 outside-command batch 02.
# Runs the controlled tracer and four launch-boundary mutants through the real
# daemon/CLI/Git/SQLite path. It starts no real Codex session.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-02-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-02-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"

TMP_ROOT=/private/tmp
before_q76="$OUTPUT/q76-before.txt"
after_q76="$OUTPUT/q76-after.txt"
find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$before_q76"

PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/run_t082_boundary.py" \
  --source "$ROOT" --output "$OUTPUT/controlled" \
  > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt"
exit_code=$?

find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$after_q76"
new_q76="$OUTPUT/q76-new.txt"
comm -13 "$before_q76" "$after_q76" > "$new_q76"
if [ -s "$new_q76" ]; then
  tar -czf "$OUTPUT/controlled-artifacts.tar.gz" -C "$TMP_ROOT" $(sed "s#^$TMP_ROOT/##" "$new_q76") 2> "$OUTPUT/archive.stderr.txt"
  archive_exit=$?
  if [ "$archive_exit" -ne 0 ] && [ "$exit_code" -eq 0 ]; then exit_code=$archive_exit; fi
  while IFS= read -r path; do
    [ -n "$path" ] && rm -rf -- "$path"
  done < "$new_q76"
else
  : > "$OUTPUT/controlled-artifacts.none"
fi

cat > "$OUTPUT/command.json" <<EOF
{
  "command": "PYTHONDONTWRITEBYTECODE=1 python3 -B workbench/tests/run_t082_boundary.py --source $ROOT --output $OUTPUT/controlled",
  "root": "$ROOT",
  "output": "$OUTPUT",
  "real_codex_turns": 0,
  "exit_code": $exit_code
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$exit_code"
exit "$exit_code"
