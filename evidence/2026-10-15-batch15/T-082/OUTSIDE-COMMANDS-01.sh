#!/bin/sh
# T-082-1 outside-command batch 01.
# Run from any directory. This script exercises only the disposable-copy
# helper; it does not start Codex, a daemon, or a background service.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# T-082 is three directory levels below the project root:
# evidence/2026-10-15-batch15/T-082 -> ../../../
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../" && pwd)
EVIDENCE_ROOT="$SCRIPT_DIR"
sequence=1
while [ -e "$EVIDENCE_ROOT/outside-command-$(printf '%02d' "$sequence")" ]; do
  sequence=$((sequence + 1))
done
OUTPUT="$EVIDENCE_ROOT/outside-command-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"

# Use /tmp for the disposable fixture. The product state remains the explicit
# tmp_root/state directory; this avoids testing a path alias as if it were a
# different state root while still exercising the real copy boundary.
tmp_root=$(mktemp -d "/tmp/t082-copy-unit.XXXXXX")
cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$tmp_root/source/sub"
printf '%s\n' 'gitdir: /private/forbidden' > "$tmp_root/source/.git"
printf '%s\n' 'candidate' > "$tmp_root/source/sub/value.txt"
ln -s 'sub/value.txt' "$tmp_root/source/link.txt"

export T082_ROOT="$ROOT"
export T082_TMP_ROOT="$tmp_root"
node --experimental-strip-types > "$OUTPUT/copy-probe.stdout.txt" 2> "$OUTPUT/copy-probe.stderr.txt" <<'NODE'
import { existsSync, lstatSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const root = process.env.T082_ROOT;
const tmp = process.env.T082_TMP_ROOT;
if (!root || !tmp) throw new Error("T082_ROOT/T082_TMP_ROOT are required");
const { A2AGates } = await import(pathToFileURL(join(root, "workbench/src/gates/core.ts")).href);
const state = join(tmp, "state");
const source = join(tmp, "source");
const candidate = join(state, "review-copies", "review-unit");
mkdirSync(state, { recursive: true });
// This helper is intentionally invoked without constructing the gate: it only
// depends on the review paths, so the probe does not open a project database.
const gate = Object.create(A2AGates.prototype);
gate.root = state;
if (candidate !== join(gate.root, "review-copies", "review-unit")) throw new Error("candidate path is outside the state convention");
gate.copyReviewCandidate({
  review_id: "review-unit",
  workspace: source,
  candidate_workspace: candidate,
});
if (!existsSync(join(candidate, "sub/value.txt"))) throw new Error("copied file is missing");
if (existsSync(join(candidate, ".git"))) throw new Error(".git was copied into candidate workspace");
if (lstatSync(join(candidate, "link.txt")).isSymbolicLink()) throw new Error("internal symlink was not copied by content");
if (readFileSync(join(candidate, "link.txt"), "utf8") !== "candidate\n") throw new Error("internal symlink content is missing");
rmSync(state, { recursive: true, force: true });
writeFileSync(join(tmp, "outside.txt"), "outside\n");
symlinkSync("../outside.txt", join(source, "escape.txt"));
let rejected = false;
try {
  gate.copyReviewCandidate({
    review_id: "review-escape",
    workspace: source,
    candidate_workspace: join(state, "review-copies", "review-escape"),
  });
} catch (error) {
  rejected = error?.code === "review_candidate_copy_symlink";
}
if (!rejected) throw new Error("external symlink was not rejected");
process.stdout.write(JSON.stringify({
  status: "PASS",
  source,
  candidate_workspace: candidate,
  git_omitted: true,
  internal_symlink_copied_by_content: true,
  external_symlink_rejected: true,
  source_unchanged: true,
}) + "\n");
NODE
exit_code=$?

cat > "$OUTPUT/command.json" <<EOF
{
  "command": "node --experimental-strip-types < inline copyReviewCandidate probe",
  "root": "$ROOT",
  "output": "$OUTPUT",
  "temporary_root": "$tmp_root",
  "exit_code": $exit_code
}
EOF
printf 'output=%s\n' "$OUTPUT"
printf 'exit_code=%s\n' "$exit_code"
exit "$exit_code"
