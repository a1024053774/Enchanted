#!/bin/zsh
# T-126 candidate 2 unit evidence: run from workbench/. The failed-start cleanup test (review 01, P2) on the candidate
# and on candidate 1 (35cadc44b, extracted to a temporary directory); the credential test again on the candidate.
E=../evidence/2026-10-22-batch20/T-126/candidate-2/unit
node --experimental-strip-types tests/test_t126_failed_start_cleanup.ts $E/cleanup-green.json > $E/cleanup-green.log 2>&1; print "cleanup-green exit=$?" >> $E/exits.txt
M=$(mktemp -d); mkdir -p $M/workbench; git -C .. archive 35cadc44b workbench/src | tar -x -C $M; ln -s $PWD/node_modules $M/workbench/node_modules
node --experimental-strip-types tests/test_t126_failed_start_cleanup.ts $E/cleanup-red-candidate-1.json $M/workbench/src > $E/cleanup-red-candidate-1.log 2>&1; print "cleanup-red-candidate-1 exit=$?" >> $E/exits.txt
node --experimental-strip-types tests/test_t126_desktop_credentials.ts $E/credentials-green.json > $E/credentials-green.log 2>&1; print "credentials-green exit=$?" >> $E/exits.txt
