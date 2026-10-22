#!/bin/zsh
# T-124 candidate 2 unit evidence: run from workbench/. H holds copies made by this script from HEAD (28a0550cc) and two mutants.
E=../evidence/2026-10-22-batch20/T-124/candidate-2/unit
H=$(mktemp -d)
git -C .. show 28a0550cc:workbench/src/processSnapshot.py > $H/snapshot-head.py
sed 's/if error.operation not in TRANSIENT or error.pid==root_pid or attempt/if error.operation not in TRANSIENT or attempt/' src/processSnapshot.py > $H/snapshot-root-retried.py
python3 - src/processSnapshot.py $H/snapshot-reader-reused.py <<'PY'
import sys
s=open(sys.argv[1]).read()
s=s.replace("    for attempt in range(1,SNAPSHOT_ATTEMPTS+1):\n        try:return snapshot(root_pid,make_reader()),attempt",
            "    reader=make_reader()\n    for attempt in range(1,SNAPSHOT_ATTEMPTS+1):\n        try:return snapshot(root_pid,reader),attempt")
open(sys.argv[2],'w').write(s)
PY
git -C .. show 28a0550cc:workbench/src/panes.ts > $H/panes-28a0550cc.ts
for name in green:src/processSnapshot.py head:$H/snapshot-head.py root-retried:$H/snapshot-root-retried.py reader-reused:$H/snapshot-reader-reused.py; do
  python3 tests/test_t093_process_snapshot.py $E/t093-${name%%:*}.json ${name#*:} > $E/t093-${name%%:*}.log 2>&1; print "t093-${name%%:*} exit=$?" >> $E/exits.txt
done
node tests/test_t124_quota_notice.mjs $E/quota-notice-green.json > $E/quota-notice-green.log 2>&1; print "quota-notice-green exit=$?" >> $E/exits.txt
node --experimental-vm-modules tests/test_t096_restore.mjs $E/t096-restore-green.json > $E/t096-restore-green.log 2>&1; print "t096-restore-green exit=$?" >> $E/exits.txt
# Not a red: the updated test's mutant names `native`, which 28a0550cc's panes.ts does not have, so the test itself fails there.
node --experimental-vm-modules tests/test_t096_restore.mjs $E/t096-restore-28a0550cc.json $H/panes-28a0550cc.ts > $E/t096-restore-28a0550cc.log 2>&1; print "t096-restore-28a0550cc exit=$?" >> $E/exits.txt
python3 tests/test_t121_role_request_e2e.py --summary $E/t121-green.json > $E/t121-green.log 2>&1; print "t121-green exit=$?" >> $E/exits.txt
