#!/bin/sh
# Reproduce the pre-existing T-076 launch-policy fixture failure from the
# main checkout, read-only, with output retained under this ticket.
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MAIN_ROOT=/Users/luckye/Documents/Code/a2a
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-08-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-08-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
PYTHONDONTWRITEBYTECODE=1 python3 -B "$MAIN_ROOT/workbench/tests/run_t076_launch_policy.py" \
  --output "$OUTPUT/t076-launch-policy-main" \
  > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt"
exit_code=$?
cat > "$OUTPUT/command.json" <<EOF2
{
  "main_root": "$MAIN_ROOT",
  "output": "$OUTPUT",
  "command": "python3 -B $MAIN_ROOT/workbench/tests/run_t076_launch_policy.py --output $OUTPUT/t076-launch-policy-main",
  "exit_code": $exit_code
}
EOF2
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$exit_code"
exit "$exit_code"
