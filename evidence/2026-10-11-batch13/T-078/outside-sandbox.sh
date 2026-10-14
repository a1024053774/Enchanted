#!/bin/bash
set -eu
extra=()
case "${1:-p1-launch-06}" in
  p1-archive-07)
    /usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/archive_t078_evidence.py --labels p1-materials-06
    exit 0 ;;
  p1-launch-07|p1-continue-07)
    echo 'BLOCKED: interactive hooks require a workspace-trust decision; see p1-trust-question-07.md. No CLI or API started.' >&2
    exit 2 ;;
  p1-launch-06) phase=launch ;;
  p1-continue-06)
    phase=continue
    extra=(--readiness-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-06/readiness.json) ;;
  p1-cleanup-06) phase=cleanup ;;
  *) echo 'Unknown P1 stage; no process started' >&2; exit 2 ;;
esac
if [ "$phase" = launch ]; then
  /usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/archive_t078_evidence.py --labels p1-materials-05
  /usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-check-materials-06.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-06/prelaunch-check.json
fi
/usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-06 --phase "$phase" "${extra[@]}"
