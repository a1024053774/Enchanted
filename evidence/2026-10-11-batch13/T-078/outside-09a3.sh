#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t078
base=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
generation=${1:?explicit generation required}
test "$generation" = 09a3r || { echo 'Unknown current generation; historical approval cannot select a new launch' >&2; exit 2; }
case "${2:?clean or block required}" in
  clean) materials="$base/p1-materials-$generation" ;;
  block) materials="$base/p1-materials-$generation-block" ;;
  *) echo 'Unknown isolated variant' >&2; exit 2 ;;
esac
extra=()
case "${3:?explicit phase required}" in
  launch) phase=launch ;;
  screen) phase=screen; extra=(--label "screen-${4:?screen ID required}" --screen-id "$4") ;;
  key) phase=key; extra=(--label "key-${4:?screen ID required}" --screen-id "$4" --key "${5:?key required}" --purpose "${6:?purpose required}" --approval-file "$materials/approvals/$4.json" --screen-file "$materials/screen-$4/screen.bin") ;;
  continue) phase=continue-esc; extra=(--readiness-file "$materials/readiness.json" --actions-approval "$materials/actions-approval.json") ;;
  cleanup) phase=cleanup ;;
  slot-cleanup) exec /usr/bin/python3 -B workbench/tests/cleanup_t078_electron_slot.py --materials "$materials" ;;
  *) echo 'Unknown phase; no default launch or input' >&2; exit 2 ;;
esac
exec /usr/bin/python3 -B workbench/tests/run_t078_p1.py --materials "$materials" --phase "$phase" "${extra[@]}"
