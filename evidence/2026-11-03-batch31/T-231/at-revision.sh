#!/bin/zsh
# Run test_native_final_read.ts on a revision's workbench/src and print how many of the nine scenarios failed.
# Usage: at-revision.sh <rev>   (exports into /private/tmp; never checks out the repository)
set -u
rev=$1; repo=$(git -C "$(dirname $0)" rev-parse --show-toplevel)
dir=$(mktemp -d /private/tmp/t231-rev-XXXX)
git -C $repo archive $rev workbench/src workbench/tests/test_native_final_read.ts | tar -x -C $dir
ln -s $repo/workbench/node_modules $dir/workbench/node_modules; ln -s $repo/workbench/package.json $dir/workbench/package.json
out=$dir/out
ENCHANTED_HC_CACHE_DIR=$repo/../hc-cache perl -e 'alarm 120; exec @ARGV' node $dir/workbench/tests/test_native_final_read.ts $out > $dir/log 2>&1
python3 - "$out/results.json" "$rev" <<'PY'
import json,sys
try: r=json.load(open(sys.argv[1]))['results']
# The test crashed before writing results (e.g. an old revision fails to import); report that, not a count.
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e: print(sys.argv[2], 'NO_RESULTS', repr(e)); sys.exit()
bad=[x['scenario']+':'+x['failure'][:60] for x in r if x['failure']]
print(sys.argv[2], f'{len(bad)}/9 failed', bad[:1])
PY
rm -rf $dir
