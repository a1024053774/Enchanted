#!/bin/zsh
# T-229 after review 02: block independent of the diagnostic write; diagnostic-fails case, its mutant, and reruns.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run r4-mutant-diagnostic-unguarded-claude $PY $T --cli claude --case diagnostic-fails --mutant diagnostic-unguarded --summary $E/r4-mutant-diagnostic-unguarded-claude.json
run r4-mutant-diagnostic-unguarded-codex $PY $T --cli codex --case diagnostic-fails --mutant diagnostic-unguarded --summary $E/r4-mutant-diagnostic-unguarded-codex.json
run r4-diag-claude $PY $T --cli claude --case diagnostic-fails --summary $E/r4-diag-claude.json
run r4-diag-codex $PY $T --cli codex --case diagnostic-fails --summary $E/r4-diag-codex.json
run r4-fails-claude $PY $T --cli claude --case record-fails --summary $E/r4-fails-claude.json
run r4-fails-codex $PY $T --cli codex --case record-fails --summary $E/r4-fails-codex.json
run r4-claude $PY $T --cli claude --summary $E/r4-claude.json
run r4-codex $PY $T --cli codex --summary $E/r4-codex.json
run r4-mutant-no-block-claude $PY $T --cli claude --case record-fails --mutant no-block --summary $E/r4-mutant-no-block-claude.json
run r4-mutant-no-claim-codex $PY $T --cli codex --mutant no-claim --summary $E/r4-mutant-no-claim-codex.json
run r4-t206 $PY workbench/tests/test_t206_input_on_send_e2e.py --summary $E/r4-t206.json
run r4-reg-t216-provenance-claude $PY workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r4-reg-t216-provenance-claude.json
run r4-reg-t216-provenance-codex $PY workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/r4-reg-t216-provenance-codex.json
echo "round4 done $(date +%T)" >> $E/runs.log
