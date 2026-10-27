#!/bin/bash
# Known-bad variants of taskHistory.ts; each must make history_check.ts fail. Run from this directory.
S=/Users/luckye/Documents/Code/a2a/workbench/src/gates/taskHistory.ts
M=$(mktemp -d)
run() { sed "$2" "$S" > "$M/taskHistory.ts"; cmp -s "$S" "$M/taskHistory.ts" && { echo "$1 sed did not change the file"; return; }
  node history_check.ts "$M/taskHistory.ts" > "history-check-$1.json" 2>/dev/null; echo "$1 exit=$?"; }
run mutant-integration-c 's/commit: d.intent.M,/commit: d.intent.C,/'
run mutant-no-quiet 's/quietRefusals.has(d.input?.command) ? null : //'
run mutant-no-reclaim "s/case 'reclaimed':/case 'reclaimed_x':/"
run mutant-last-review-only 's/history.reviews.push(/history.reviews.splice(0, history.reviews.length, /'
run mutant-drop-all-verify "s/let repeat = false;/let repeat = event.type === 'rejected' \&\& d.input?.command === 'verify';/"
run mutant-any-previous-failure "s/repeat = open.get(attempt) === d.error;/repeat = true;/"
run mutant-feedback-breaks-fold "s/if (event.type === 'submitted' || event.type === 'verification_result') open.delete/if (!shown || event.type === 'submitted' || event.type === 'verification_result') open.delete/"
run mutant-fold-not-consumed "s/      open.delete(attempt);//"
run mutant-row-attempt "s/d.details?.attempt?.attempt_id ?? event.attempt : event.attempt/event.attempt : event.attempt/"
run mutant-first-appearance-header "s/const start = step.attempt !== null \&\& step.attempt !== shown;/const start = step.attempt !== null \&\& !steps.slice(0, steps.indexOf(step)).some(other => other.attempt === step.attempt);/"
run mutant-no-rule-check "s/case 'rule_check':/case 'rule_check_x':/"
rm -rf "$M"
