#!/usr/bin/env bash
set -euo pipefail

# Real T-082 runner. Default prints the plan. --execute N runs exactly one
# product-path round: daemon -> gate -> createReview -> Panes -> reviewer.
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
CODEX_BIN=${CODEX_BIN:-/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex}
NODE_BIN=${NODE_BIN:-/opt/homebrew/Cellar/node/26.5.0/bin/node}
EXECUTE=""
MANIFEST=""
APPROVAL_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=${2:-}; shift 2 ;;
    --manifest) MANIFEST=${2:-}; shift 2 ;;
    --approval-dir) APPROVAL_DIR=${2:-}; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
cat <<PLAN
T-082 real product-path runner
rounds: 1 boundary proof, 2 delivery review; maximum 4
path: daemon_start -> gate card/create/claim/submit/verify -> A2AGates.requestReview -> Panes.createReview -> reviewer submit/reclaim
argv source: workbench/src/panes.ts via the product launch record (no hand-written Codex argv)
PLAN
[[ -n "$EXECUTE" ]] || exit 2
[[ "$EXECUTE" =~ ^[12]$ ]] || { echo '--execute must be 1 or 2' >&2; exit 2; }
[[ -f "$MANIFEST" && -f "$APPROVAL_DIR/round-$EXECUTE.approved" ]] || { echo 'manifest and per-round approval are required' >&2; exit 2; }
[[ -s "$APPROVAL_DIR/round-$EXECUTE.approved" ]] || { echo 'approval file must be nonempty signed JSON' >&2; exit 2; }
[[ -x "$CODEX_BIN" && -x "$NODE_BIN" && -f "$HOME/.codex/auth.json" ]] || { echo 'pinned runtime/auth is unavailable' >&2; exit 2; }

eval "$(python3 - "$MANIFEST" "$EXECUTE" <<'PY'
import json, shlex, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
for key in ('fixture_root','task','repo','state','card','role_round1','role_round2','trusted_marker'):
    print(f'{key.upper()}={shlex.quote(m[key])}')
if sys.argv[2] == '2':
    print('CARD=' + shlex.quote(m['card_round2']))
PY
)"
[[ "$FIXTURE_ROOT" == /Volumes/WD-Elements/* && -f "$TRUSTED_MARKER" ]] || { echo 'fixture root is not trusted external storage' >&2; exit 2; }
python3 - "$APPROVAL_DIR/round-$EXECUTE.approved" "$EXECUTE" "$FIXTURE_ROOT" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
if v.get('round') != int(sys.argv[2]) or not all(isinstance(v.get(k), str) and v[k].strip() for k in ('approved_by', 'approval_ref', 'argv_summary')):
    raise SystemExit('approval JSON needs round, argv_summary, approved_by and approval_ref')
if v.get('fixture_root') != sys.argv[3] or v.get('max_real_turns') != 1:
    raise SystemExit('approval must bind this fixture and one real turn')
PY
CODE_REVISION=$(git -C "$ROOT" rev-parse HEAD)
git -C "$ROOT" diff --exit-code HEAD -- workbench/src workbench/hooks workbench/tests workbench/README.md > /dev/null || { echo 'freeze the candidate source before a real round' >&2; exit 2; }
[[ -z "$(git -C "$ROOT" ls-files --others --exclude-standard -- workbench/src workbench/hooks workbench/tests)" ]] || { echo 'include new runtime and test files in the frozen candidate' >&2; exit 2; }
OUT_BASE="$SCRIPT_DIR/real-codex-round-$EXECUTE"
OUT="$OUT_BASE"
output_seq=1
while [[ -e "$OUT" ]]; do
  output_seq=$((output_seq + 1))
  OUT="${OUT_BASE}-$(printf '%02d' "$output_seq")"
done
mkdir "$OUT"
USER_HOME=$HOME
HOME_ROOT=$(mktemp -d /private/tmp/t082-codex-home.XXXXXX)
DAEMON_HOME="$HOME_ROOT/daemon-home"
REVIEW_HOME="$HOME_ROOT/review-codex-home"
TIMEOUT=0
cleanup() {
  set +e
  if [[ "$TIMEOUT" == 0 ]]; then
    [[ -n "${DAEMON_STARTED:-}" ]] && "$NODE_BIN" "$ROOT/workbench/src/gates/cli.ts" --state "$STATE" daemon_stop > "$OUT/daemon-stop.json" 2> "$OUT/daemon-stop.stderr.txt"
    find "$HOME_ROOT" -mindepth 1 -maxdepth 3 -print > "$OUT/home-before-delete.txt"
    rm -rf -- "$HOME_ROOT"
    [[ ! -e "$HOME_ROOT" ]] && printf '%s\n' absent > "$OUT/home-after-delete.txt" || printf '%s\n' present > "$OUT/home-after-delete.txt"
  else
    printf '%s\n' preserved-timeout > "$OUT/cleanup-status.txt"
  fi
}
trap cleanup EXIT HUP INT TERM
mkdir -m 700 "$DAEMON_HOME" "$REVIEW_HOME"
cp "$USER_HOME/.codex/auth.json" "$REVIEW_HOME/auth.json"
chmod 600 "$REVIEW_HOME/auth.json"
mkdir -m 700 "$REVIEW_HOME/rules"
python3 - "$REVIEW_HOME/config.toml" "$FIXTURE_ROOT" <<'PY'
import sys
from pathlib import Path
path, fixture = sys.argv[1:]
Path(path).write_text(f'[projects."{fixture}"]\ntrust_level = "trusted"\n\n[tui]\nscreen_reader_detection_done = true\n\n[tui.model_availability_nux]\n"gpt-6.1-sol" = 1\n', encoding='utf-8')
PY
cat > "$REVIEW_HOME/rules/default.rules" <<'RULES'
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
RULES
cp "$REVIEW_HOME/config.toml" "$OUT/home-trust.toml"
cp "$REVIEW_HOME/rules/default.rules" "$OUT/home-rules.default.rules"
export HOME="$DAEMON_HOME"
unset CODEX_HOME
[[ $(find "$REVIEW_HOME" -maxdepth 1 -type f -name auth.json | wc -l | tr -d ' ') == 1 ]] || { echo 'isolated reviewer home must contain only auth.json' >&2; exit 2; }

ROLE="$ROLE_ROUND1"; [[ "$EXECUTE" == 2 ]] && ROLE="$ROLE_ROUND2"
WORKER_HOME="$HOME_ROOT/unused-worker-home"; REVIEW_HOME="$HOME_ROOT/review-codex-home"
mkdir -m 700 "$WORKER_HOME"
CONFIG="$OUT/launch-config.json"
python3 - "$CONFIG" "$CODEX_BIN" "$ROLE" "$WORKER_HOME" "$REVIEW_HOME" "$APPROVAL_DIR/round-$EXECUTE.approved" "$CODE_REVISION" <<'PY'
import json, sys
out, codex_bin, role, worker_home, review_home, approval, revision = sys.argv[1:]
value = {'codex_bin': codex_bin,
 'codex_home': worker_home, 'role_card': role, 'role_card_revision': 'T-082-real-approved-role',
 'code_revision': revision, 'source_snapshot': None,
 'hook_authorization': approval, 'turn_limit': 1, 'turn_authorization': approval,
 'reviewers': [{'codex_home': review_home, 'role_card': role, 'role_card_revision': 'T-082-real-approved-role', 'hook_authorization': approval}]}
json.dump(value, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
PY
printf '%s\n' 'git add' 'git commit' > "$OUT/allowed-prefix-rules.txt"

CLI=("$NODE_BIN" "$ROOT/workbench/src/gates/cli.ts" --state "$STATE")
run_cli() { "${CLI[@]}" "$@"; }
run_cli daemon_start --launch-config "$CONFIG" > "$OUT/daemon-start.json"
DAEMON_STARTED=1
run_cli card_save --task "$TASK" --card "$CARD" --expected-version 0 > "$OUT/card-save.json"
run_cli create --task "$TASK" --repo "$REPO" --branch refs/heads/main --card-version 1 --project t082-real > "$OUT/create.json"
run_cli claim --task "$TASK" --owner executor-fixture > "$OUT/claim.json"
eval "$(python3 - "$OUT/claim.json" <<'PY'
import json, shlex, sys
v=json.load(open(sys.argv[1]))['attempt']
for key in ('workspace','attempt_id','session_id','fence','spec_rev'):
 print(f'{key.upper()}={shlex.quote(str(v[key]))}')
PY
)"
printf 'correct\n' > "$WORKSPACE/src/value.txt"
(cd "$WORKSPACE" && git add src/value.txt)
WORKER_SENTINEL="$WORKSPACE/src/t082-worker-sentinel.txt"
printf 'T082 worker/review sentinel\n' > "$WORKER_SENTINEL"
(cd "$WORKSPACE" && git add src/t082-worker-sentinel.txt)
(cd "$WORKSPACE" && git commit -m 'T-082 real candidate') > "$OUT/candidate-commit.txt"
CANDIDATE=$(git -C "$WORKSPACE" rev-parse HEAD)
SHARED_SENTINEL="$REPO/.git/t082-shared-sentinel"
printf 'T082 shared sentinel\n' > "$SHARED_SENTINEL"
run_cli submit --task "$TASK" --attempt "$ATTEMPT_ID" --session "$SESSION_ID" --fence "$FENCE" --spec-rev "$SPEC_REV" --commit "$CANDIDATE" > "$OUT/submit.json"
if run_cli verify --task "$TASK" --attempt "$ATTEMPT_ID" > "$OUT/verify.json" 2> "$OUT/verify.stderr.txt"; then
  :
else
  verify_exit=$?
  run_cli status --task "$TASK" > "$OUT/status-failure.json" 2>/dev/null || true
  run_cli events --task "$TASK" > "$OUT/events-failure.json" 2>/dev/null || true
  python3 - "$OUT/verify.json" "$OUT/status-failure.json" "$OUT/readback-failure.json" <<'PY'
import json, sys
def read(path):
    try: return json.load(open(path, encoding='utf-8'))
    except Exception as e: return {'read_error': str(e)}
v=read(sys.argv[1]); s=read(sys.argv[2])
json.dump({'verify': v, 'status': s, 'failure': v.get('error')}, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
PY
  printf '%s\n' "$verify_exit" > "$OUT/verify-exit.txt"
  exit "$verify_exit"
fi
python3 - "$OUT/verify.json" "$OUT/binding.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1])); r=v['task']['review']; json.dump({'task':v['task'],'review':r},open(sys.argv[2],'w'),ensure_ascii=False,indent=2)
PY
eval "$(python3 - "$OUT/verify.json" <<'PY'
import json, shlex, sys
r=json.load(open(sys.argv[1]))['task']['review']
print('REVIEW_THREAD=' + shlex.quote(r['thread_id']))
print('REVIEW_ID=' + shlex.quote(r['review_id']))
print('REVIEW_LAUNCH=' + shlex.quote(str(r['launch_id'])))
print('REVIEW_WORKSPACE=' + shlex.quote(r['workspace']))
print('CANDIDATE_WORKSPACE=' + shlex.quote(r['candidate_workspace']))
PY
)"
REVIEW_SENTINEL="$REVIEW_WORKSPACE/src/t082-worker-sentinel.txt"
cat "$WORKER_SENTINEL" > "$OUT/worker-sentinel-before.txt"
cat "$REVIEW_SENTINEL" > "$OUT/review-sentinel-before.txt"
git -C "$REPO" show "$CANDIDATE:src/t082-worker-sentinel.txt" > "$OUT/review-sentinel-committed.txt"
cat "$SHARED_SENTINEL" > "$OUT/shared-sentinel-before.txt"
git -C "$REPO" for-each-ref --format='%(refname)=%(objectname)' > "$OUT/shared-refs-before.txt"
git -C "$WORKSPACE" status --porcelain=v1 --untracked-files=all > "$OUT/worker-status-before.txt"
run_cli pane_status --thread "$REVIEW_THREAD" > "$OUT/pane-before-release.json"
run_cli pane_output --launch "$REVIEW_LAUNCH" --offset 0 --max-bytes 65536 > "$OUT/pane-output-before-release.json" || true
python3 - "$OUT/pane-output-before-release.json" "$OUT/pane-output-before-release.raw.txt" <<'PY'
import base64, json, sys
try:
    value=json.load(open(sys.argv[1])); data=base64.b64decode(value.get('data_base64',''))
except Exception as e:
    data=('pane_output_read_error: '+str(e)+'\n').encode()
open(sys.argv[2],'wb').write(data)
PY
run_cli pane_process_info --thread "$REVIEW_THREAD" > "$OUT/pane-process-before-release.json" || true
if python3 - "$OUT/pane-process-before-release.json" "$OUT/pane-ready-readback.json" <<'PY'
import json, sys
try: value=json.load(open(sys.argv[1]))
except Exception as e: value={'read_error':str(e)}
ready=bool(value.get('leader')) and not value.get('failed')
json.dump({'ready':ready,'leader':value.get('leader'),'failed':value.get('failed'),'raw':value},open(sys.argv[2],'w'),indent=2)
if not ready: raise SystemExit(1)
PY
then
  :
else
  TIMEOUT=1
  printf '%s\n' pane-not-ready-preserved > "$OUT/pane-not-ready.txt"
  exit 125
fi
run_cli pane_release --thread "$REVIEW_THREAD" --reason "T-082 approved real round $EXECUTE" > "$OUT/pane-release.json"
run_cli launch_show --launch "$REVIEW_LAUNCH" > "$OUT/launch-readback.json"
start=$(date +%s)
while :; do
  run_cli status --task "$TASK" > "$OUT/status-last.json" || true
  run_cli events --task "$TASK" > "$OUT/events-last.json" || true
  if python3 - "$OUT/status-last.json" "$OUT/events-last.json" "$REVIEW_ID" <<'PYCODE'
import json, sys
state = json.load(open(sys.argv[1])).get('task', {})
events = json.load(open(sys.argv[2])).get('events', [])
rid = sys.argv[3]
if any(e['type'] == 'review_reclaimed' and e['details'].get('review_id') == rid for e in events):
    raise SystemExit(0)
if state.get('review', {}).get('state') == 'unknown':
    raise SystemExit(2)
raise SystemExit(1)
PYCODE
  then
    break
  else
    poll_exit=$?
    if [[ "$poll_exit" == 2 ]]; then
      TIMEOUT=1
      printf '%s\n' review-failed-preserved > "$OUT/review-failure.txt"
      run_cli pane_output --launch "$REVIEW_LAUNCH" --offset 0 --max-bytes 65536 > "$OUT/pane-output-failure.json" || true
      exit 1
    fi
  fi
  if (( $(date +%s) - start > 900 )); then
    TIMEOUT=1
    printf '%s\n' timeout-preserved > "$OUT/timeout.txt"
    exit 124
  fi
  sleep 1
done
run_cli events --task "$TASK" > "$OUT/events-final.json" || true
run_cli status --task "$TASK" > "$OUT/status-final.json" || true
if [[ -d "$STATE/traces" ]]; then cp -R "$STATE/traces" "$OUT/traces"; fi
git -C "$WORKSPACE" status --porcelain=v1 --untracked-files=all > "$OUT/worker-status-after.txt"
git -C "$REPO" for-each-ref --format='%(refname)=%(objectname)' > "$OUT/shared-refs-after.txt"
git -C "$REPO" rev-parse HEAD > "$OUT/shared-head-after.txt"
cat "$WORKER_SENTINEL" > "$OUT/worker-sentinel-after.txt" 2>/dev/null || printf '%s\n' unavailable > "$OUT/worker-sentinel-after.txt"
cat "$SHARED_SENTINEL" > "$OUT/shared-sentinel-after.txt" 2>/dev/null || printf '%s\n' unavailable > "$OUT/shared-sentinel-after.txt"
if [[ -e "$REVIEW_SENTINEL" ]]; then cat "$REVIEW_SENTINEL" > "$OUT/review-sentinel-after.txt"; else printf '%s\n' deleted-after-clean-check > "$OUT/review-sentinel-after.txt"; fi
python3 -B "$ROOT/workbench/tests/read_t082_real_result.py" --run "$OUT" --round "$EXECUTE" > "$OUT/readback.stdout.txt" 2> "$OUT/readback.stderr.txt"
grep -R -h 'T082_DENY\|T082_PROBE\|EPERM\|Operation not permitted\|network' "$OUT/traces" > "$OUT/boundary-error-readback.txt" 2>/dev/null || printf '%s\n' unavailable > "$OUT/boundary-error-readback.txt"
exit 0
