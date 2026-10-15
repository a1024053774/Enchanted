#!/bin/sh
# T-082-1 outside-command batch 05.
# Build clean temporary candidate repositories so T-076's source audit remains
# unchanged. The old T-076 files run first; a separate D3-only patch is then
# applied in a second temporary candidate. No real Codex sessions.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
MAIN_ROOT=/Users/luckye/Documents/Code/a2a
TMP_ROOT=/private/tmp
BASE_PARENT=a7f4cc3033c16d5888de50d8352da516c941f8e9
PATCH_FILE="$SCRIPT_DIR/t076-assertion-changes.patch"
sequence=1
while [ -e "$SCRIPT_DIR/outside-command-05-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-05-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
TEMP_ROOT=$(mktemp -d "$TMP_ROOT/t082-t076-candidates.XXXXXX")
before_q76="$OUTPUT/q76-before.txt"
find "$TMP_ROOT" -maxdepth 1 -type d -name 'q76-*' -print 2>/dev/null | sort > "$before_q76"
overall=0

cleanup() {
  rm -rf -- "$TEMP_ROOT"
}
trap cleanup EXIT HUP INT TERM

make_candidate() {
  name=$1
  apply_d3=$2
  dest="$TEMP_ROOT/$name"
  mkdir -p "$dest"
  cp -R "$ROOT/workbench" "$dest/workbench"
  rm -rf -- "$dest/workbench/node_modules"
  ln -s "$ROOT/workbench/node_modules" "$dest/workbench/node_modules"
  cp -R "$ROOT/scripts" "$dest/scripts"
  cp -R "$ROOT/acceptance" "$dest/acceptance"
  ln -s "$ROOT/evidence" "$dest/evidence"
  if [ "$apply_d3" = yes ]; then
    (cd "$dest" && patch -p1 < "$PATCH_FILE") > "$OUTPUT/$name.patch.stdout.txt" 2> "$OUTPUT/$name.patch.stderr.txt"
    patch_rc=$?
    if [ "$patch_rc" -ne 0 ]; then return "$patch_rc"; fi
  fi
  git -C "$dest" init -q
  git -C "$dest" config user.email t082-fixture@example.invalid
  git -C "$dest" config user.name T082-fixture
  git -C "$dest" remote add parent "$MAIN_ROOT"
  git -C "$dest" fetch -q parent "$BASE_PARENT":refs/remotes/parent/base
  git -C "$dest" add workbench scripts acceptance
  tree=$(git -C "$dest" write-tree)
  commit=$(printf '%s\n' "$name candidate" | git -C "$dest" commit-tree "$tree" -p "$BASE_PARENT")
  git -C "$dest" reset -q --hard "$commit"
  printf '%s\n' "$dest"
}

run_step() {
  name=$1
  cwd=$2
  expected=$3
  shift 3
  "$@" > "$OUTPUT/$name.stdout.txt" 2> "$OUTPUT/$name.stderr.txt"
  rc=$?
  cat > "$OUTPUT/$name.command.json" <<EOF
{
  "name": "$name",
  "cwd": "$cwd",
  "argv": "$(printf '%s ' "$@" | sed 's/[[:space:]]*$//')",
  "exit_code": $rc
}
EOF
  if [ "$rc" -ne "$expected" ]; then overall=1; fi
}

old_root=$(make_candidate parent-old no)
run_step parent-t076-quality-green-old "$old_root" 1 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$old_root/workbench/tests/run_t076_quality_green.py" \
  --output "$OUTPUT/parent-t076-quality-green-old"
run_step parent-t076-launch-policy-old "$old_root" 1 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$old_root/workbench/tests/run_t076_launch_policy.py" \
  --output "$OUTPUT/parent-t076-launch-policy-old"

python3 -B - "$OUTPUT/parent-t076-quality-green-old/run.json" "$OUTPUT/parent-t076-launch-policy-old/run.json" \
  > "$OUTPUT/parent-d3-failure-validation.json" 2> "$OUTPUT/parent-d3-failure-validation.stderr.txt" <<'PY'
import json, sys
allowed = {'TRACER-READONLY-ARGV', 'TRACER-REVIEWER-DEFAULT-ARGV'}
rows = []
for path in sys.argv[1:]:
    value = json.load(open(path, encoding='utf-8'))
    failures = [case.get('failure_id') for case in value.get('cases', []) if case.get('failure_id')]
    unexpected = [failure for failure in failures if failure not in allowed]
    rows.append({'path': path, 'status': value.get('status'), 'failure_ids': failures, 'unexpected': unexpected})
if any(row['unexpected'] for row in rows):
    raise SystemExit(json.dumps({'status': 'FAIL', 'rows': rows}, ensure_ascii=False))
print(json.dumps({'status': 'PASS', 'rows': rows}, ensure_ascii=False, indent=2))
PY
if [ "$?" -ne 0 ]; then overall=1; fi

d3_root=$(make_candidate candidate-d3 yes)
run_step candidate-t076-quality-green-d3 "$d3_root" 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$d3_root/workbench/tests/run_t076_quality_green.py" \
  --output "$OUTPUT/candidate-t076-quality-green-d3"
run_step candidate-t076-launch-policy-d3 "$d3_root" 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$d3_root/workbench/tests/run_t076_launch_policy.py" \
  --output "$OUTPUT/candidate-t076-launch-policy-d3"

run_step candidate-t077-review-worktree "$ROOT" 0 \
  env PYTHONDONTWRITEBYTECODE=1 python3 -B "$ROOT/workbench/tests/test_review_worktree_lifecycle_e2e.py" \
  --source "$ROOT" --output "$OUTPUT/candidate-t077-review-worktree"

after_q76="$OUTPUT/q76-after.txt"
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
  "temporary_candidates": "$TEMP_ROOT",
  "parent_revision": "$BASE_PARENT",
  "d3_patch": "$PATCH_FILE",
  "real_codex_turns": 0,
  "exit_code": $overall
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$overall"
exit "$overall"
