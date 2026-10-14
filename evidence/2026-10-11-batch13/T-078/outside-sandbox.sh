#!/bin/bash
set -eu
base=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-09a2
extra=()
case "${1:-p1-launch-09a2}" in
  p1-launch-09a2) phase=launch ;;
  p1-screen-09a2)
    phase=screen
    if [ -z "${2:-}" ]; then echo 'Explicit screen ID required' >&2; exit 2; fi
    extra=(--label "screen-$2" --screen-id "$2") ;;
  p1-key-09a2)
    phase=key
    if [ -z "${2:-}" ] || [ -z "${3:-}" ] || [ -z "${4:-}" ]; then echo 'Explicit screen ID, key and purpose required; no key sent' >&2; exit 2; fi
    extra=(--label "key-$2" --screen-id "$2" --key "$3" --purpose "$4" --approval-file "$base/approvals/$2.json" --screen-file "$base/screen-$2/screen.bin") ;;
  p1-continue-09a2) phase=continue-esc; extra=(--readiness-file "$base/readiness.json" --actions-approval "$base/actions-approval.json") ;;
  p1-cleanup-09a2) phase=cleanup ;;
  p1-slot-cleanup-09)
    /usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/cleanup_t078_electron_slot.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-09
    exit ;;
  p1-slot-cleanup-09a2)
    /usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/cleanup_t078_electron_slot.py --materials "$base"
    exit ;;
  *) echo 'Unknown stage; no process started' >&2; exit 2 ;;
esac
/usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials "$base" --phase "$phase" "${extra[@]}"
