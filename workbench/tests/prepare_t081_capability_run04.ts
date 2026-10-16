// Prepare review artifacts only. No daemon, PTY, credentials or fixture writes.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { capabilityWorker } from "./t081_capability_materials.ts";

const root = resolve(import.meta.dirname, "../..");
const evidence = join(root, "evidence/2026-10-14-batch14/T-081");
const fixture = "/private/tmp/t081-capability-01", runRoot = fixture + "/run-04";
const output = join(evidence, "capability-review-04");
if (existsSync(runRoot)) throw new Error("run-04 fixture exists; do not replace it.");
mkdirSync(output);
const prior = JSON.parse(readFileSync(join(evidence, "capability-review-03/launch-policy.first-turn.pending.json"), "utf8"));
const { validateTaskCard } = await import(pathToFileURL(fixture + "/source/workbench/src/gates/taskCards.ts").href);
const input = JSON.parse(readFileSync(join(evidence, "capability-review-03/task-card.pending.json"), "utf8"));
input.id = "T-081-CAP-04";
// The validator clones its input and normalizes executables. Keep its return.
const card = validateTaskCard(input, input.id);
const state = runRoot + "/state", repo = runRoot + "/repo", bare = runRoot + "/local.git";
const trustBefore = JSON.parse(readFileSync(join(evidence, "capability-run03-finding-01/run.json"), "utf8")).home_baseline.config_text;
const oldTrustRoot = fixture + "/run-03/repo";
if (trustBefore.split(oldTrustRoot).length !== 2) throw new Error("Prior trust root must occur exactly once.");
const trustAfter = trustBefore.replace(oldTrustRoot, repo);
writeFileSync(join(output, "home-trust.before.toml"), trustBefore, { flag: "wx" });
writeFileSync(join(output, "home-trust.after.toml"), trustAfter, { flag: "wx" });
const workspace = state + "/worktrees/t081-capability/T-081-CAP-04-a1";
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const signal = [prior.node, prior.cli, "--state", state, "signal", "--launch", "${LAUNCH_ID}"].map(quote).join(" ");
const hook = `[{hooks=[{type="command",command=${JSON.stringify(signal)},timeout=10}]}]`;
const argv = [prior.argv[0], "--no-daemon", "--no-alt-screen", "-C", workspace,
  "-a", "never", "--sandbox", "workspace-write", "-m", "gpt-6.1-sol",
  "-c", 'model_reasoning_effort="xhigh"', "-c", 'service_tier="default"',
  "-c", "check_for_update_on_startup=false", "-c", "tui.notifications=false",
  "-c", "sandbox_workspace_write.network_access=false", "-c", "features.network_proxy=false"];
for (const event of ["UserPromptSubmit", "Stop", "PermissionRequest"]) argv.push("-c", `hooks.${event}=${hook}`);
argv.push("--dangerously-bypass-hook-trust");
const G = "4de60dac7fd4b9baebd5c5cb177267673f398d77", T = "16a341ae5f0b65b26c0829b830ca28c938ea9130";
const { role, commands } = capabilityWorker(runRoot, G, T);
const bound = { ...card, base_commit: G, writer: { task_id: card.id, attempt_id: "${ATTEMPT_ID}",
  session_id: "${SESSION_ID}", fence: 1, thread_id: "${THREAD_ID}" } };
const submit = { command: "submit", task: card.id, attempt: "${ATTEMPT_ID}", session: "${SESSION_ID}",
  fence: 1, spec_rev: 1, commit: "<FULL_COMMIT_SHA>" };
const submitCommand = [prior.node, prior.cli, "--state", state, "submit", "--task", card.id,
  "--attempt", "${ATTEMPT_ID}", "--session", "${SESSION_ID}", "--fence", "1", "--spec-rev", "1",
  "--commit", "FULL_COMMIT_SHA"].map(quote).join(" ");
const source = readFileSync(fixture + "/source/workbench/src/gates/core.ts", "utf8");
const matches = [...source.matchAll(/const prompt = (`[\s\S]*?`);\n    const dispatchPrompt/g)];
if (matches.length !== 1) throw new Error("Product first-turn template must be unique.");
const prompt = new Function("attempt", "submit", "submitCommand", "return " + matches[0][1] + ";")
  .call({ boundCard: () => bound }, {}, submit, submitCommand);
const first = "⟦主控 #1⟧\n" + role + "\n\n" + prompt;
const write = (name: string, value: any) => writeFileSync(join(output, name), JSON.stringify(value, null, 2) + "\n", { flag: "wx" });
write("task-card.pending.json", card);
write("task-card.bound.template.json", bound);
writeFileSync(join(output, "ROLE-BODY.md"), role, { flag: "wx" });
writeFileSync(join(output, "FIRST-TURN.template.md"), first, { flag: "wx" });
write("launch-policy.first-turn.pending.json", { ...prior, approved: false, run_root: runRoot,
  task: card.id, state, repo, bare_repo: bare, argv, first_turn_requested: 3,
  consumed_turns_before: 2, total_turn_limit: 3,
  trust_config_before: trustBefore, trust_config_after: trustAfter,
  shell_argv: ["-f", "-i", "-c", argv.map(quote).join(" ") + "; exec /bin/zsh -f -i"],
  approval_note: "run-01/02/03 保留；已消耗 2/3，本次待批准第 3 回合（最后一次）", turn_limit: 1,
  worker_commands: commands });
const config = JSON.parse(readFileSync(join(evidence, "capability-review-03/launch-config.pending.json"), "utf8"));
write("launch-config.pending.json", { ...config, role_card: runRoot + "/WORKER.md",
  role_card_revision: "T-081 capability-review-04 canonical card", hook_authorization: null, turn_authorization: null, turn_limit: 1 });
const hooks = JSON.parse(readFileSync(join(evidence, "capability-prepared-01/hook-contents.json"), "utf8"));
write("hook-contents.json", { ...hooks, cli_hooks: Object.fromEntries(["UserPromptSubmit", "Stop", "PermissionRequest"].map(e => [e, hook])), installed: false });
write("review-metadata.json", { status: "INCOMPLETE", approved: false, task: card.id, run_root: runRoot,
  source_revision: config.code_revision, proposed_approval_ref: "T-081 controller-decision-04 capability-turn-3",
  home: prior.codex_home, home_prepare_authorization: "T-081 controller-decision-01 capability-turn-1",
  canonical_python: card.completion_conditions[0].argv[0], actual_turns_started: 0, consumed_turns_before: 2,
  trust_change: "仅在新批准运行内把 run-03 的精确信任项改为 run-04；保留 TUI 标记，不读写 auth、不改规则",
  dynamic_fields: ["${LAUNCH_ID}", "${ATTEMPT_ID}", "${SESSION_ID}", "${THREAD_ID}"] });
process.stdout.write(JSON.stringify({ status: "INCOMPLETE", output, fixture_written: false, real_codex_turns: 0,
  canonical_python: card.completion_conditions[0].argv[0] }) + "\n");
