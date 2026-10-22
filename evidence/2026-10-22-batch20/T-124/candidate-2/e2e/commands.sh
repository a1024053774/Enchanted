#!/bin/zsh
# T-124 candidate 2 e2e evidence: run from workbench/. Each line writes one summary; an existing summary is never overwritten.
# Groups run three at a time (at most three Codex sessions). Usage: commands.sh green1 green2 green3 red1 ... red7
E=../evidence/2026-10-22-batch20/T-124/candidate-2/e2e
run() { python3 tests/test_t124_controller_e2e.py --summary $E/$1.json "${@:2}" > $E/$1.log 2>&1; print "$1 exit=$?" >> $E/exits.txt }
for group in "$@"; do case $group in
  green1) run green-01-release & run green-02-quota --end quota & run green-03-codex-monitor --monitor-cli codex & wait ;;
  green2) run green-04-restart-working --end restart-working & run green-05-restart-verified --end restart-verified &
          run green-06-restart-working-codex-monitor --end restart-working --monitor-cli codex & wait ;;
  green3) run green-07-codex-controller-gui --controller-cli codex --gui & run green-08-codex-controller-quota --controller-cli codex --end quota &
          run green-09-claude-controller-gui --gui & wait ;;
  red1) run red-01-parent --revision b25d44045 & run mutant-01-answer-as-user --mutant answer-as-user &
        run mutant-02-run-waits-for-score --mutant run-waits-for-score & wait ;;
  red2) run mutant-03-run-ignores-active --mutant run-ignores-active-controller & run mutant-04-unscored-without-reason --mutant unscored-without-reason &
        run mutant-05-quota-unread --mutant quota-unread & wait ;;
  red3) run mutant-06-monitor-writable --mutant monitor-writable & run mutant-07-issue-provider-codex --mutant issue-provider-codex &
        run mutant-08-snapshot-denies-privileged --mutant snapshot-denies-privileged & wait ;;
  red4) run mutant-09-codex-monitor-unbound --mutant codex-monitor-unbound --monitor-cli codex & run mutant-10-reclaim-monitor-repo --mutant reclaim-monitor-repo &
        run mutant-11-quota-stops-at-bad-line --mutant quota-stops-at-bad-line & wait ;;
  red5) run mutant-12-runs-not-resumed --mutant runs-not-resumed --end restart-verified & run mutant-13-gone-not-registered --mutant gone-not-registered --end restart-working &
        run mutant-14-monitor-not-restored --mutant monitor-not-restored --end restart-verified & wait ;;
  red6) run mutant-15-resume-without-redispatch --mutant resume-without-redispatch --end restart-working & run mutant-16-worker-asks-natively --mutant worker-asks-natively &
        run mutant-17-codex-reset-unread --mutant codex-reset-unread --controller-cli codex & wait ;;
  red7) run mutant-18-notice-not-rendered --mutant notice-not-rendered --gui ;;
  # The user's Codex install (~/.codex/packages) was removed during the first full run; green-03, green-06 and mutant-09
  # failed at attach with ENOENT (mutant-09 is therefore no red). Codex 0.163.0 was reinstalled at 07:23; rerun under new names.
  codex2) run green-03-codex-monitor-02 --monitor-cli codex & run green-06-restart-working-codex-monitor-02 --end restart-working --monitor-cli codex &
          run mutant-09-codex-monitor-unbound-02 --mutant codex-monitor-unbound --monitor-cli codex & wait ;;
  # mutant-16 first removed the flag from every Claude launch and was caught by the gate's reviewer boundary
  # (review_launch_boundary), not by the worker's tool list; mutant-17 first left `if (...)` before a `const`, so the
  # daemon did not start (no red). Both were narrowed and rerun under new names.
  red8) run mutant-16-worker-asks-natively-02 --mutant worker-asks-natively & run mutant-17-codex-reset-unread-02 --mutant codex-reset-unread --controller-cli codex & wait ;;
  # mutant-16-02 was still refused by the gate at review, before the tool-list check. The worker's list is now checked
  # right after its first question (worker_offered_no_native_question); green-01 reruns to show the new check passes.
  red9) run mutant-16-worker-asks-natively-03 --mutant worker-asks-natively & run green-01-release-02 & wait ;;
esac; done
