#!/bin/sh
# 审查第三轮 F2 的核对：git for-each-ref 给多个 --contains 时是“或”还是“与”。
set -e
d=$(mktemp -d); cd "$d"; git init -q -b main .; git commit -q --allow-empty -m base
git switch -q -c a; git commit -q --allow-empty -m W1; w1=$(git rev-parse HEAD)
git switch -q main; git switch -q -c b; git commit -q --allow-empty -m W2; w2=$(git rev-parse HEAD)
git branch leak "$w1"
git --version
echo "refs containing W1 or/and W2:"; git for-each-ref --format='%(refname)' --contains "$w1" --contains "$w2"
cd /; rm -rf "$d"
