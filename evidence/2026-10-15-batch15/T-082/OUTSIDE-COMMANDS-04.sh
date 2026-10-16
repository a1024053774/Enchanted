#!/bin/sh
# T-082-1 outside-command batch 04.
# Candidate T-082 evidence plus unchanged parent T-076 runs from the main
# checkout (which owns the historical T-076 source snapshot absent here).
# No real Codex sessions are started.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
MAIN_ROOT=/Users/luckye/Documents/Code/a2a
TMP_ROOT=/private/tmp
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-04-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-04-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"

before_q76="$OUTPUT/q76-before.txt"
after_q76="$OUTPUT/q76-after.txt"
find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$before_q76"
overall=0

run_step() {
  name=$1
  shift
  "$@" > "$OUTPUT/$name.stdout.txt" 2> "$OUTPUT/$name.stderr.txt"
  rc=$?
  cat > "$OUTPUT/$name.command.json" <<EOF
{
  "name": "$name",
  "argv": "$(printf '%s ' "$@" | sed 's/[[:space:]]*$//')",
  "exit_code": $rc
}
EOF
  if [ "$rc" -ne 0 ]; then overall=1; fi
}

# Candidate: new T-082 request/copy/start-boundary tracer and four mutants.
run_step candidate-t082-boundary \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/run_t082_boundary.py" \
  --source "$ROOT" --output "$OUTPUT/candidate-t082-boundary"

# Candidate: external change after reviewer result invalidates cleanup.
run_step candidate-end-check \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_t082_review_boundary_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/candidate-end-check" --case external_review_boundary_invalidated

# Candidate: T-077 reviewer worktree lifecycle regression.
run_step candidate-t077-review-worktree \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_review_worktree_lifecycle_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/candidate-t077-review-worktree"

# Parent revision: run unchanged T-076 scripts from the full main checkout.
run_step parent-t076-quality-green \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$MAIN_ROOT/workbench/tests/run_t076_quality_green.py" \
  --output "$OUTPUT/parent-t076-quality-green"

run_step parent-t076-launch-policy \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$MAIN_ROOT/workbench/tests/run_t076_launch_policy.py" \
  --output "$OUTPUT/parent-t076-launch-policy"

find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$after_q76"
new_q76="$OUTPUT/q76-new.txt"
comm -13 "$before_q76" "$after_q76" > "$new_q76"
if [ -s "$new_q76" ]; then
  tar -czf "$OUTPUT/q76-artifacts.tar.gz" -C "$TMP_ROOT" \
    $(sed "s#^$TMP_ROOT/##" "$new_q76") 2> "$OUTPUT/q76-archive.stderr.txt"
  rc=$?
  if [ "$rc" -ne 0 ]; then overall=1; fi
  while IFS= read -r path; do
    [ -n "$path" ] && rm -rf -- "$path"
  done < "$new_q76"
else
  : > "$OUTPUT/q76-artifacts.none"
fi

cat > "$OUTPUT/command.json" <<EOF
{
  "root": "$ROOT",
  "main_root": "$MAIN_ROOT",
  "output": "$OUTPUT",
  "tmp_root": "$TMP_ROOT",
  "real_codex_turns": 0,
  "exit_code": $overall
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$overall"
exit "$overall"
