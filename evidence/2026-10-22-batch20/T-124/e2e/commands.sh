#!/bin/zsh
# T-124 e2e evidence: run from workbench/. Each line writes one summary; an existing summary is never overwritten.
E=../evidence/2026-10-22-batch20/T-124/e2e
run() { python3 tests/test_t124_controller_e2e.py --summary $E/$1.json "${@:2}" > $E/$1.log 2>&1; print "$1 exit=$?" >> $E/exits.txt }
case $1 in
  green) run green-01-release & run green-02-quota --end quota & run green-03-codex-monitor --monitor-cli codex & wait ;;
  red1) run red-01-parent --revision b25d44045 & run mutant-01-answer-as-user --mutant answer-as-user & run mutant-02-run-waits-for-score --mutant run-waits-for-score & wait ;;
  red2) run mutant-03-run-ignores-active --mutant run-ignores-active-controller & run mutant-04-unscored-without-reason --mutant unscored-without-reason & run mutant-05-quota-unread --mutant quota-unread & wait ;;
  red3) run mutant-06-monitor-writable --mutant monitor-writable & run mutant-07-issue-provider-codex --mutant issue-provider-codex & run mutant-08-snapshot-denies-privileged --mutant snapshot-denies-privileged & wait ;;
  red4) run mutant-09-codex-monitor-unbound --mutant codex-monitor-unbound --monitor-cli codex ;;
esac
