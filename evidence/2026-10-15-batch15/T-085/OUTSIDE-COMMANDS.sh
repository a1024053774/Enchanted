#!/bin/bash
set -u

ROOT=/Users/luckye/Documents/Code/a2a-wt-t085
EVIDENCE="$ROOT/evidence/2026-10-15-batch15/T-085"
BASELINE=6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac
red_src=''
mutant_src=''

cleanup() {
  [[ -n "$red_src" && -d "$red_src" ]] && rm -rf "$red_src"
  [[ -n "$mutant_src" && -d "$mutant_src" ]] && rm -rf "$mutant_src"
}
trap cleanup EXIT

next_output_dir() {
  local prefix="$1"
  local number=1
  local candidate
  while :; do
    candidate="$EVIDENCE/$prefix-$(printf '%02d' "$number")"
    if [[ ! -e "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
    number=$((number + 1))
  done
}

cd "$ROOT"
red_dir=$(next_output_dir red)
green_dir=$(next_output_dir green)
mutant_dir=$(next_output_dir mutant)

echo '=== RED: baseline 6ba3bde4, unmodified recovery suite ==='
red_src=$(mktemp -d /tmp/t085-red-src.XXXXXX)
git archive "$BASELINE" | tar -x -C "$red_src"
ln -s "$ROOT/workbench/node_modules" "$red_src/workbench/node_modules"
set +e
python3 -B "$red_src/workbench/tests/test_daemon_recovery_e2e.py" --output "$red_dir"
red_exit=$?
set -e
echo "RED_OUTPUT=$red_dir"
echo "RED_EXIT=$red_exit"

echo '=== GREEN: fixed recovery suite with controlled reviewer completion ==='
set +e
python3 -B "$ROOT/workbench/tests/test_daemon_recovery_e2e.py" --output "$green_dir"
green_exit=$?
set -e
echo "GREEN_OUTPUT=$green_dir"
echo "GREEN_EXIT=$green_exit"

echo '=== MUTANT: target restart with empty configuration in a one-time copy ==='
mutant_src=$(mktemp -d /tmp/t085-mutant-src.XXXXXX)
git archive "$BASELINE" | tar -x -C "$mutant_src"
cp "$ROOT/workbench/tests/test_daemon_recovery_e2e.py" "$mutant_src/workbench/tests/test_daemon_recovery_e2e.py"
ln -s "$ROOT/workbench/node_modules" "$mutant_src/workbench/node_modules"
python3 - "$mutant_src/workbench/tests/test_daemon_recovery_e2e.py" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')
old = """argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', self.quality.control]"""
new = """review_control = self.quality.control
            if self._testMethodName == 'test_daemon_verify_interruption_and_operation_lock':
                review_control = self.root / 'empty-review-control'
                review_control.mkdir()
                (review_control / 'config.json').write_text('{}\\n', encoding='utf-8')
                (review_control / 'process-facts.json').write_text('{}\\n', encoding='utf-8')
            argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', review_control]"""
if source.count(old) != 1:
    raise SystemExit('mutation anchor count mismatch')
path.write_text(source.replace(old, new), encoding='utf-8')
PY
set +e
python3 -B "$mutant_src/workbench/tests/test_daemon_recovery_e2e.py" --output "$mutant_dir"
mutant_exit=$?
set -e
echo "MUTANT_OUTPUT=$mutant_dir"
echo "MUTANT_EXIT=$mutant_exit"

echo '=== EXIT CODES ==='
printf 'RED_EXIT=%s\n' "$red_exit"
printf 'GREEN_EXIT=%s\n' "$green_exit"
printf 'MUTANT_EXIT=%s\n' "$mutant_exit"

overall=0
[[ "$red_exit" -ne 1 ]] && overall=1
[[ "$green_exit" -ne 0 ]] && overall=1
[[ "$mutant_exit" -ne 1 ]] && overall=1
exit "$overall"
