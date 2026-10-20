#!/bin/sh
# 已知坏版本：复制 docs 到临时目录，各注入一处缺陷，确认对应场景报 FAIL。
# 用法：sh evidence/2026-10-20-batch18/T-113/mutants.sh（在仓库根目录运行，需要本机 Google Chrome）
cd "$(dirname "$0")/../../.." || exit 2
here=evidence/2026-10-20-batch18/T-113
work=$(mktemp -d /private/tmp/t113-mutants-XXXXXX)
port=8614
result=0
mutate() { # 名称 场景前缀 python 替换（旧串 新串）
  name=$1 only=$2 old=$3 new=$4
  rm -rf "$work/site" && cp -R docs "$work/site"
  python3 - "$work/site/assets/demo.js" "$old" "$new" <<'PY'
import sys
path, old, new = sys.argv[1:]
text = open(path, encoding='utf-8').read()
assert text.count(old) == 1, 'mutation anchor not unique'
open(path, 'w', encoding='utf-8').write(text.replace(old, new))
PY
  python3 -m http.server $port --bind 127.0.0.1 --directory "$work/site" >/dev/null 2>&1 & server=$!
  i=0; until curl -fs -o /dev/null "http://127.0.0.1:$port/" || [ $i -ge 50 ]; do sleep 0.1; i=$((i+1)); done
  if node "$here/check_demo.mjs" --url "http://127.0.0.1:$port/" --only "$only" > "$work/$name.txt" 2>&1; then
    echo "NOT REJECTED  ${name}"; result=1
  elif grep -q '^FAIL' "$work/$name.txt"; then
    echo "REJECTED      ${name}: $(grep -c '^FAIL' "$work/$name.txt") 项 FAIL"; grep '^FAIL' "$work/$name.txt" | head -3
  else
    echo "RUN ERROR     ${name}（没有 FAIL 行，不算拒收）"; tail -5 "$work/$name.txt"; result=1
  fi
  kill $server; wait $server 2>/dev/null
}
mutate answer-keeps-waiting 03 "      agent.state = 'running';" "      agent.state = agent.state;"
mutate dock-follows-notifications 03 '${ui.dockBadges && waiting ?' '${ui.dockBadges && pending.length ?'
mutate flow-more-off-by-one 05 'list.slice(0, 4)' 'list.slice(0, 5)'
mutate split-replaces-pane 04 "{ direction: target.dataset.direction, first: paneKey, second: next }" "next"
mutate execution-save-ignored 10 "      data.execution[ui.execRole] = { ...(ui.execDraft ?? data.execution[ui.execRole]) };" "      void 0;"
mutate reply-ignores-choice 03b "question.replies[value] ?? question.freeReply;" "Object.values(question.replies)[0];"
mutate notice-replays-after-reenable 03b "if (ui.notifications && !ui.noticeSeen.has(id))" "if (ui.notifications)"
rm -rf "$work"
exit $result
