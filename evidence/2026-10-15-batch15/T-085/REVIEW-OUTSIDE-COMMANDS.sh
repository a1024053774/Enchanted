#!/bin/bash
set -u
set -o pipefail

# T-085 独立审查：只在一次性副本中构造错误实现，不改候选工作树。
ROOT=/Users/luckye/Documents/Code/a2a-wt-t085
EVIDENCE="$ROOT/evidence/2026-10-15-batch15/T-085"
CANDIDATE=e059da18c0d579b1d9da415b33e67bd840e109e0

declare -a SOURCES=()
declare -a SUITE_EXITS=()
PREPARED_SOURCE=''
overall=0

cleanup() {
  local source
  for source in "${SOURCES[@]}"; do
    [[ -n "$source" && -d "$source" ]] && rm -rf "$source"
  done
}
trap cleanup EXIT

reserve_output() {
  local label="$1"
  local n=1
  [[ "$label" == 'mutant-04' ]] && n=2
  local candidate
  while :; do
    candidate="$EVIDENCE/review-01-${label}-$(printf '%02d' "$n")"
    if [[ ! -e "$candidate" ]]; then
      mkdir "$candidate"
      printf '%s\n' "$candidate"
      return 0
    fi
    n=$((n + 1))
  done
}

prepare_source() {
  local label="$1"
  local source
  source=$(mktemp -d "/tmp/t085-review-01-${label}.XXXXXX")
  SOURCES+=("$source")
  # 只解出恢复套件及其源码/夹具依赖；明确排除数 GB 的 evidence/。
  git archive "$CANDIDATE" \
    workbench acceptance scripts fixtures records .project-map .grilling \
    AGENTS.md CONTEXT.md README.md intent.md | tar -x -C "$source"
  ln -s "$ROOT/workbench/node_modules" "$source/workbench/node_modules"
  PREPARED_SOURCE="$source"
}

patch_mutant_01() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
start = source.index("    def restart(self):\n")
end = source.index("    def snapshot(self, label):\n", start)
method = """    def restart(self):
        env_path = self.env['PATH']
        self.env['PATH'] = str(self.root / 'daemon-git') + os.pathsep + env_path
        try:
            result = self.process(['node', records.GATE, '--state', self.state, 'daemon_start'])
            self.assertEqual(result.returncode, 0, records.COMMANDS[-1])
            self._daemon_state = self.state
        finally:
            self.env['PATH'] = env_path

"""
if source.count("    def restart(self):\n") != 1 or source.count("    def snapshot(self, label):\n") != 1:
    raise SystemExit("restart method anchors are not unique")
path.write_text(source[:start] + method + source[end:], encoding="utf-8")
PY
}

patch_mutant_02() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
old = """            argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', self.quality.control]"""
new = """            review_control = self.quality.control
            if self._testMethodName == 'test_daemon_verify_interruption_and_operation_lock':
                review_control = self.root / 'alternate-review-control'
                review_control.mkdir()
                source_control = self.quality.control
                (review_control / 'config.json').write_text(
                    (source_control / 'config.json').read_text(encoding='utf-8'), encoding='utf-8')
                (review_control / 'process-facts.json').write_text('{}\n', encoding='utf-8')
            argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', review_control]"""
if source.count(old) != 1:
    raise SystemExit("restart host argv anchor is not unique")
path.write_text(source.replace(old, new), encoding="utf-8")
PY
}

patch_mutant_03() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
old = "        self.quality.complete_review(self.task)\n"
new = "        if self._testMethodName != 'test_daemon_verify_interruption_and_operation_lock':\n            self.quality.complete_review(self.task)\n"
if source.count(old) != 1:
    raise SystemExit("complete_review anchor is not unique")
path.write_text(source.replace(old, new), encoding="utf-8")
PY
}

patch_mutant_04() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
old_argv = """            argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', self.quality.control]"""
new_argv = """            review_control = self.quality.control
            if self._testMethodName == 'test_daemon_verify_interruption_and_operation_lock':
                review_control = self.root / 'empty-review-control'
                review_control.mkdir()
                (review_control / 'config.json').write_text('{}\n', encoding='utf-8')
                (review_control / 'process-facts.json').write_text('{}\n', encoding='utf-8')
            argv = ['node', host, self.state, self.worker_control, ready,
                    records.ROOT / 'workbench/src/gates/core.ts', review_control]"""
old_assertions = """            self.assertEqual(Path(comparison['before']['source']).resolve(), self.launch_config_path.resolve())
            self.assertEqual(Path(comparison['after']['source']).resolve(), self.launch_config_path.resolve())
            self.assertTrue(comparison['equal'], comparison)
"""
if source.count(old_argv) != 1 or source.count(old_assertions) != 1:
    raise SystemExit("config mutation anchors are not unique")
source = source.replace(old_argv, new_argv).replace(old_assertions, "")
path.write_text(source, encoding="utf-8")
PY
}

run_mutant() {
  local label="$1"
  local description="$2"
  local patch_function="$3"
  local source
  local output
  local suite_output
  local patch_exit
  local suite_exit

  printf '%s\n' "=== 变异 ${label}：${description} ==="
  output=$(reserve_output "$label")
  suite_output="$output/run"
  prepare_source "$label"
  source="$PREPARED_SOURCE"
  printf '源副本：%s\n' "$source" > "$output/setup.log"

  set +e
  "$patch_function" "$source/workbench/tests/test_daemon_recovery_e2e.py" > "$output/mutation.log" 2>&1
  patch_exit=$?
  if [[ "$patch_exit" -eq 0 ]]; then
    python3 -B "$source/workbench/tests/test_daemon_recovery_e2e.py" \
      --output "$suite_output" > "$output/suite.log" 2>&1
    suite_exit=$?
  else
    suite_exit=125
  fi
  set +e

  SUITE_EXITS+=("$suite_exit")
  printf 'patch_exit=%s\nsuite_exit=%s\n' "$patch_exit" "$suite_exit" >> "$output/setup.log"
  printf '输出目录：%s\n变异脚本退出码：%s\n套件退出码：%s\n' "$output" "$patch_exit" "$suite_exit"
  if [[ "$patch_exit" -ne 0 || "$suite_exit" -ne 1 ]]; then
    overall=1
  fi
}

run_mutant 'mutant-04' '使用空配置并删除配置来源与等同性断言' patch_mutant_04

printf '%s\n' '=== 各段退出码 ==='
index=0
for label in mutant-04; do
  printf '%s=%s\n' "${label^^}_EXIT" "${SUITE_EXITS[$index]}"
  index=$((index + 1))
done
printf 'OVERALL_EXIT=%s\n' "$overall"
exit "$overall"
