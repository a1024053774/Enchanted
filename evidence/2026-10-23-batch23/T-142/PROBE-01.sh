#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 2
root=$PWD
out=$(mktemp -d "$root/evidence/2026-10-23-batch23/T-142/probe-01-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/t142-probe-pycache
print -r -- "探针证据目录：$out"
git rev-parse HEAD > "$out/candidate.txt"
print -r -- "python3 workbench/tests/probe_t142_bash_redirect.py --summary '$out/summary.json'" > "$out/command.txt"
python3 workbench/tests/probe_t142_bash_redirect.py --summary "$out/summary.json" > "$out/probe.log" 2>&1
code=$?
print -r -- "$code" > "$out/exit.txt"
cat "$out/summary.json"
exit "$code"
