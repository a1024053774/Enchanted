#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t078
base=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
case "${1:?clean or block required}" in
  clean) materials="$base/p1-materials-09a3" ;;
  block) materials="$base/p1-materials-09a3-block" ;;
  *) echo 'Unknown isolated variant' >&2; exit 2 ;;
esac
extra=()
case "${2:?explicit phase required}" in
  launch) phase=launch ;;
  screen) phase=screen; extra=(--label "screen-${3:?screen ID required}" --screen-id "$3") ;;
  key) phase=key; extra=(--label "key-${3:?screen ID required}" --screen-id "$3" --key "${4:?key required}" --purpose "${5:?purpose required}" --approval-file "$materials/approvals/$3.json" --screen-file "$materials/screen-$3/screen.bin") ;;
  continue) phase=continue-esc; extra=(--readiness-file "$materials/readiness.json" --actions-approval "$materials/actions-approval.json") ;;
  cleanup) phase=cleanup ;;
  slot-cleanup) exec /usr/bin/python3 -B workbench/tests/cleanup_t078_electron_slot.py --materials "$materials" ;;
  *) echo 'Unknown phase; no default launch or input' >&2; exit 2 ;;
esac
exec /usr/bin/python3 -B workbench/tests/run_t078_p1.py --materials "$materials" --phase "$phase" "${extra[@]}"
