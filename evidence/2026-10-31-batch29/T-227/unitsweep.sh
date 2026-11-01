#!/bin/zsh
# usage: unitsweep.sh LABEL PANES_SOURCE OUT
cd /Users/luckye/Documents/Code/a2a/workbench
cp "$2" src/panes.ts
for t in tests/test_pane_dispatch_state.ts tests/test_conflict_panes.ts tests/test_ready_file.ts tests/test_t078_*.ts tests/test_t093_*.ts tests/test_t126_failed_start_cleanup.ts tests/test_t157_turn_identity.ts tests/test_t165_queued_stop.ts tests/test_t207_interrupted_turn_hooks.ts tests/test_t166_queued_input.ts tests/test_t160_protocol_idle.ts tests/test_t221_codex_scan_days.ts; do
  n=$(basename $t .ts); o=$3/$1-$n; 
  TMPDIR=/private/tmp perl -e "alarm 180; exec @ARGV" node $t $o > $o.log 2>&1; echo "$n $?"
done
