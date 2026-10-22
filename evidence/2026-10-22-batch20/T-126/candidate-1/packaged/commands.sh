#!/bin/zsh
# T-126 candidate 1 packaged evidence: run from the repository root.
# Builds (already made for this run; each slot is new, the build refuses to reuse one):
#   new    node workbench/app/package.mjs --slot t126-new --variant test        (main checkout at 35cadc44, workbench/ clean)
#   parent git worktree add --detach /private/tmp/t126-parent-src 04d632694
#          cp -c -R workbench/node_modules /private/tmp/t126-parent-src/workbench/node_modules
#          (cd /private/tmp/t126-parent-src && node workbench/app/package.mjs --slot t126-parent --variant test)
# Each app's Contents/Resources/app/package.json records its revision (a2a.revision).
# The run directory with screenshots and app logs goes to the archive disk; run.json is copied back here.
A=/Volumes/WD-Elements/a2a-evidence/2026-10-22-batch20/T-126/candidate-1/packaged-${1:?run number}
E=evidence/2026-10-22-batch20/T-126/candidate-1/packaged
mkdir -p ${A:h}
node evidence/2026-10-22-batch20/T-126/packaged/t126drive.mjs "$TMPDIR/a2a-build-t126-parent/Enchanted Test.app" \
  "$TMPDIR/a2a-build-t126-new/Enchanted Test.app" $A 9361 > $E/packaged-$1.log 2>&1
print "packaged-$1 exit=$?" >> $E/exits.txt
cp $A/run.json $E/packaged-$1.run.json
