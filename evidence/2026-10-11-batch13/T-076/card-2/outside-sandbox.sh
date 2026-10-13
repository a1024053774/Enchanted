#!/bin/zsh
set -euo pipefail

# Controlled stages use no models. Real instances each require their own
# APPROVED.json: P-review slot 1, or the separate delivery slots 2-6.
if (( $# != 2 )); then
  print -u2 'usage: zsh outside-sandbox.sh <stage-1|stage-2|stage-3|focused-tracer|review-red|wide-green|review-green|legacy-green|launch-policy|p-review|real-delivery> <new-run-label>'
  exit 2
fi
typeset -r quality_card="${0:A:h}"
typeset -r quality_root="${quality_card:h:h:h:h}"
typeset -r quality_label="$2"
if [[ "$quality_label" != [A-Za-z0-9]* || "$quality_label" == *[^A-Za-z0-9._-]* ]]; then
  print -u2 'label must start with a letter/digit and contain only letters/digits/dot/dash/underscore'
  exit 2
fi
case "$1" in
  prepare-delivery-review)
    exec python3 -B "$quality_card/prepare-delivery-review.py" \
      --approval-file "$quality_card/delivery-review-01/APPROVED.json" \
      --output "$quality_card/outside-$quality_label"
    ;;
  archive-real-log)
    exec python3 -B "$quality_card/archive-real-log.py" \
      --output "$quality_card/outside-$quality_label"
    ;;
  real-delivery)
    if [[ "$quality_label" != real-delivery-02 ]]; then
      print -u2 'Delivery slots 2-6 are bound to real-delivery-02; another instance needs approval'
      exit 2
    fi
    exec python3 -B "$quality_root/workbench/tests/run_t076_quality_real.py" \
      --output "$quality_card/outside-real-delivery-02" \
      --approval-file "$quality_card/real-delivery-02/APPROVED.json"
    ;;
  launch-policy)
    exec python3 -B "$quality_root/workbench/tests/run_t076_launch_policy.py" \
      --output "$quality_card/outside-$quality_label"
    ;;
  p-review)
    if [[ "$quality_label" != p-review-02 ]]; then
      print -u2 'P-review slot 1 is bound to p-review-02; another instance needs separate approval'
      exit 2
    fi
    exec python3 -B "$quality_root/workbench/tests/run_p_review.py" \
      --output "$quality_card/outside-p-review-02" \
      --approval-file "$quality_card/p-review-02/APPROVED.json"
    ;;
  legacy-green)
    exec python3 -B "$quality_root/workbench/tests/run_t076_legacy_green.py" \
      --output "$quality_card/outside-$quality_label"
    ;;
  review-red|wide-green|review-green)
    exec python3 -B "$quality_root/workbench/tests/run_t076_quality_widen.py" \
      --phase "$1" --output "$quality_card/outside-$quality_label"
    ;;
  focused-tracer)
    exec python3 -B "$quality_root/workbench/tests/run_t076_quality_green.py" \
      --output "$quality_card/outside-$quality_label"
    ;;
  stage-1|stage-2|stage-3)
    exec python3 -B "$quality_root/workbench/tests/run_t076_quality_red.py" \
      --stage "$1" --output "$quality_card/outside-$quality_label"
    ;;
  *) print -u2 'choose a prepared stage; real P-review is not authorized'; exit 2 ;;
esac
