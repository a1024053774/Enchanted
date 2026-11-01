#!/bin/zsh
# T-229 round 5: every unit test that constructs Panes directly, on the HEAD copy (base) and on the candidate tree (cand).
# Arg 1 = base|cand. Each test gets a fresh output path as argv[2] (tests that take none ignore it); 240 s limit each.
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
[[ $1 == base ]] && W=/private/tmp/t229-t108base/workbench || W=/Users/luckye/Documents/Code/a2a/workbench
cd $W
export TMPDIR=/private/tmp
for f in $(grep -ln "new Panes(" tests/*.ts tests/*.mjs); do
  n=${f:t:r}
  perl -e 'alarm shift; exec @ARGV' 240 node $f $E/r5-unit/$1/$n.json > $E/r5-unit/$1/$n.log 2>&1
  echo "$n exit=$?" >> $E/r5-unit/$1/exits.txt
done
echo done >> $E/r5-unit/$1/exits.txt
