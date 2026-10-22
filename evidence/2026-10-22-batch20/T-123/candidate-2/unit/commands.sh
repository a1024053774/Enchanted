#!/bin/zsh
# T-123 candidate 2 unit evidence: run from workbench/. M holds source copies made by this script: the parent
# revision and two known-bad migrations (the membership resume and the relay input column removed).
E=../evidence/2026-10-22-batch20/T-123/candidate-2/unit
O=$(mktemp -d)
for t in test_relay_core test_t078_controller_relay test_t078_relay_role; do
  node --experimental-strip-types tests/$t.ts $O/$t > $E/$t.log 2>&1; print "$t exit=$?" >> $E/exits.txt
done
for t in test_t096_restore test_t124_quota_notice; do
  node --experimental-vm-modules tests/$t.mjs $E/$t.json > $E/$t.log 2>&1; print "$t exit=$?" >> $E/exits.txt
done
R=evidence/2026-10-22-batch20/T-123/candidate-2/unit
(cd .. && node --experimental-vm-modules workbench/tests/test_t109_hierarchy.mjs $R/test_t109_hierarchy.json > $R/test_t109_hierarchy.log 2>&1; print "test_t109_hierarchy exit=$?" >> $R/exits.txt)
node --experimental-strip-types tests/test_t123_migration_resume.ts $E/migration-green.json > $E/migration-green.log 2>&1; print "migration-green exit=$?" >> $E/exits.txt
for m in parent memberships-not-resumed input-not-rewritten; do
  M=$(mktemp -d); mkdir -p $M/workbench; ln -s $PWD/node_modules $M/workbench/node_modules
  if [[ $m == parent ]]; then git -C .. archive 4116c8b44 workbench/src | tar -x -C $M; else cp -R src $M/workbench/src; fi
  python3 - $M/workbench/src/gates/core.ts $m <<'PY'
import sys
path, mutant = sys.argv[1:]
s = open(path).read()
if mutant == 'memberships-not-resumed':
    old = '''    for (const row of this.membership.database.prepare("SELECT id, json_extract(data,'$.projectId') AS project FROM memberships WHERE instr(id,'+')=0").all())
      if (!renamed.has(String(row.id))) renamed.set(String(row.id), taskKey(String(row.project), String(row.id)));
'''
    assert s.count(old) == 1; s = s.replace(old, '')
if mutant == 'input-not-rewritten':
    old = ' || column === "input");'
    assert s.count(old) == 1; s = s.replace(old, ');')
open(path, 'w').write(s)
PY
  node --experimental-strip-types tests/test_t123_migration_resume.ts $E/migration-$m.json $M/workbench/src/gates/core.ts > $E/migration-$m.log 2>&1
  print "migration-$m exit=$?" >> $E/exits.txt
done
