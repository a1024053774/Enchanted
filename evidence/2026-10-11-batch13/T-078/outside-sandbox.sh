#!/bin/bash
set -eu
extra=()
case "${1:-p1-launch-08}" in
  p1-launch-08) phase=launch ;;
  p1-screen-08) phase=screen ;;
  p1-trust-08)
    phase=trust
    if [ "${2:-}" != Digit1 ]; then echo 'Digit1 must be explicitly supplied; no key sent' >&2; exit 2; fi
    extra=(--key "$2" --approval-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-08/trust-approval.json --screen-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-08/screen/screen.bin) ;;
  p1-continue-08)
    phase=continue
    extra=(--readiness-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-08/readiness.json) ;;
  p1-cleanup-08) phase=cleanup ;;
  *) echo 'Unknown stage; no process started' >&2; exit 2 ;;
esac
/usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-08 --phase "$phase" "${extra[@]}"
