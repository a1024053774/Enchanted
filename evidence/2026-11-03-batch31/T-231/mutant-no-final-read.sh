#!/bin/zsh
# Known-bad: drop the final native read at exit (this.scan(pane, true)), run the test against that copy of workbench/src.
# Usage: mutant-no-final-read.sh <output dir>
set -eu
repo=$(git -C "$(dirname $0)" rev-parse --show-toplevel); dir=$(mktemp -d /private/tmp/t231-mutant-XXXX)
cp -R $repo/workbench/src $dir/src; ln -s $repo/workbench/node_modules $dir/node_modules; ln -s $repo/workbench/package.json $dir/package.json
python3 - $dir/src/panes.ts <<'PY'
import sys; p=sys.argv[1]; s=open(p).read(); old='        this.scan(pane, true);\n'
assert s.count(old)==1; open(p,'w').write(s.replace(old,'',1))
PY
A2A_PANE_MODULE=$dir/src/panes.ts node $repo/workbench/tests/test_native_final_read.ts $1 > $1.log 2>&1 || true
python3 -c "import json;r=json.load(open('$1/results.json'))['results'];print([(x['scenario'],(x['failure'] or '')[:70]) for x in r])"
rm -rf $dir
