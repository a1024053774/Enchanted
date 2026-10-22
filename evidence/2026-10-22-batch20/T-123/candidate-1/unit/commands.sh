#!/bin/zsh
# T-123 candidate 1 unit evidence: run from workbench/.
E=../evidence/2026-10-22-batch20/T-123/candidate-1/unit
O=$(mktemp -d)
for t in test_relay_core test_t078_controller_relay test_t078_relay_role; do
  node --experimental-strip-types tests/$t.ts $O/$t > $E/$t.log 2>&1; print "$t exit=$?" >> $E/exits.txt
done
for t in test_t096_restore test_t124_quota_notice; do
  node --experimental-vm-modules tests/$t.mjs $E/$t.json > $E/$t.log 2>&1; print "$t exit=$?" >> $E/exits.txt
done
# t109 resolves its source from the repository root.
R=evidence/2026-10-22-batch20/T-123/candidate-1/unit
(cd .. && node --experimental-vm-modules workbench/tests/test_t109_hierarchy.mjs $R/test_t109_hierarchy.json > $R/test_t109_hierarchy.log 2>&1; print "test_t109_hierarchy exit=$?" >> $R/exits.txt)
