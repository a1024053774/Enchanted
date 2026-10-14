// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { request as daemonRequest, startDaemon } from "../transport.ts";
import { queueWorkerRequest, readWorkerRequests } from "../relayFiles.ts";
import { readOperatorCredential } from "../credentials.ts";

const commands: Record<string, { required: string[]; optional?: string[] }> = {
  daemon_start: { required: [], optional: ["launch-config"] },
  daemon_status: { required: [] },
  daemon_stop: { required: [] },
  pane_status: { required: ["thread"] },
  pane_output: { required: ["launch", "offset"], optional: ["max-bytes"] },
  workbench_snapshot: { required: [], optional: ["launch"] },
  pane_process_info: { required: ["thread"] },
  pane_release: { required: ["thread", "reason"] },
  pane_dispatch: { required: ["thread", "body-file"] },
  signal: { required: ["launch"] },
  launch_show: { required: ["launch"] },
  controller_prepare: { required: ["preset"] },
  controller_start: { required: ["manifest"] },
  orchestration_events: { required: [], optional: ["task"] },
  card_template: { required: ["repo"], optional: ["ticket", "project"] },
  card_validate: { required: ["card"] },
  card_save: { required: ["card", "expected-version"] },
  card_show: { required: ["card-version"] },
  create: { required: ["repo", "branch", "card-version"], optional: ["project", "title"] },
  dispatch: { required: ["runtime-mode"], optional: ["overlap-reason"] },
  attach: {
    required: ["role", "model-selection", "instructions", "runtime-mode"],
    optional: ["preset"],
  },
  run: { required: ["runtime-mode", "wait-seconds"], optional: ["overlap-reason"] },
  claim: { required: ["owner"], optional: ["overlap-reason"] },
  revoke: { required: ["reason"] },
  revise: { required: ["spec-rev"], optional: ["card-version"] },
  submit: { required: ["attempt", "session", "fence", "spec-rev", "commit"], optional: ["request-id"] },
  verify: { required: [], optional: ["attempt"] },
  integrate: { required: [], optional: ["attempt", "score-file"] },
  abandon: { required: ["attempt"], optional: ["score-file"] },
  scores_validate: { required: ["file"] },
  review_submit: { required: ["review-file"] },
  status: { required: [], optional: ["request-id"] },
  issue: { required: ["title", "body"], optional: ["blocking", "refs", "request-id"] },
  events: { required: [] },
  issues: { required: [], optional: ["thread"] },
  answer_issue: { required: ["issue", "answer"] },
  answer_issues: { required: ["answers"], optional: ["mode"] },
  disposition: { required: ["issue", "action"], optional: ["reason", "basis"] },
  reclaim: { required: [], optional: ["attempt", "thread"] },
  inbox_send: {
    required: ["to", "kind", "body"],
    optional: ["from", "reply-to", "refs", "title", "blocking", "action", "reason", "basis", "bundle-id"],
  },
  inbox_list: { required: [], optional: ["role"] },
  inbox_ack: { required: ["id"], optional: ["role", "body"] },
  inbox_ready: { required: ["project"] },
  stop: { required: ["thread", "stop-id"] },
};

async function emit(result: unknown) {
  await new Promise<void>((resolve, reject) => {
    process.stdout.write(JSON.stringify(result) + "\n", (error) =>
      error ? reject(error) : resolve(),
    );
  });
}

export async function main(argv = process.argv.slice(2)) {
  let root: string;
  let request: Record<string, unknown>;
  try {
    const keys = [
      "state",
      "task",
      "repo",
      "project",
      "title",
      "thread",
      "role",
      "model-selection",
      "runtime-mode",
      "wait-seconds",
      "branch", "card", "ticket", "card-version", "expected-version",
      "instructions",
      "owner",
      "reason",
      "overlap-reason",
      "attempt",
      "session",
      "fence",
      "spec-rev",
      "commit",
      "issue",
      "answer",
      "answers",
      "mode",
      "action",
      "basis",
      "preset",
      "from",
      "to",
      "kind",
      "body",
      "reply-to",
      "refs",
      "blocking",
      "id",
      "bundle-id",
      "stop-id",
      "launch-config", "launch", "body-file", "request-id", "offset", "max-bytes", "manifest",
      "score-file", "review-file",
      "file",
    ];
    const { values, positionals } = parseArgs({
      args: argv,
      options: Object.fromEntries(keys.map((key) => [key, { type: "string" as const }])),
      allowPositionals: true,
    });
    const command = positionals[0] ?? "";
    const contract = commands[command];
    const noTask = command.startsWith("inbox_") || command === "stop" ||
      command.startsWith("daemon_") || command.startsWith("pane_") ||
      ["signal", "launch_show", "orchestration_events", "scores_validate"].includes(command);
    if (!contract || positionals.length !== 1 || (!noTask && !values.task))
      throw new Error("command and task required");
    const allowed = [
      "state",
      ...(!noTask ? ["task"] : []),
      ...contract.required,
      ...(contract.optional ?? []),
    ];
    if (
      Object.keys(values).some((key) => !allowed.includes(key)) ||
      contract.required.some((key) => values[key] === undefined)
    )
      throw new Error("invalid command arguments");
    root = values.state ?? process.env.A2A_STATE ?? join(homedir(), "Library/Application Support/a2a-orchestrator");
    request = { command };
    for (const [key, value] of Object.entries(values)) {
      if (key === "state") continue;
      if (["fence", "spec-rev", "wait-seconds", "card-version", "expected-version", "offset", "max-bytes"].includes(key)) {
        if (
          typeof value !== "string" ||
          !/^[+-]?\d+$/.test(value) ||
          !Number.isSafeInteger(Number(value))
        )
          throw new Error("integer required: " + key);
        request[key.replaceAll("-", "_")] = Number(value);
      } else if (key === "model-selection") request.modelSelection = JSON.parse(value!);
      else if (key === "answers") request.answers = JSON.parse(value!);
      else if (key === "refs") request.refs = JSON.parse(value!);
      else if (key === "manifest") request.manifest = JSON.parse(readFileSync(value!, "utf8"));
      else if (key === "blocking") {
        if (value !== "true" && value !== "false") throw new Error("boolean required: blocking");
        request.blocking = value === "true";
      } else if (["reply-to", "bundle-id", "stop-id", "request-id", "score-file", "overlap-reason"].includes(key))
        request[key.replaceAll("-", "_")] = value;
      else request[key === "runtime-mode" ? "runtimeMode" : key] = value;
    }
    if (command === "signal") {
      request.received_at = new Date().toISOString();
      request.raw_stdin = readFileSync(0, "utf8");
      if (JSON.parse(String(request.raw_stdin)).hook_event_name === "Stop" && process.env.A2A_ROLE !== "reviewer") {
        request.relay_files = readWorkerRequests(process.env.A2A_REQUEST_DIR!);
      }
    }
    if (command === "pane_dispatch") request.body = readFileSync(String(request["body-file"]), "utf8");
    if (command === "review_submit") {
      const file = request["review-file"];
      const result = JSON.parse(readFileSync(String(file), "utf8"));
      const { schema: _schema, request_id: _id, ...body } = result;
      request = { ...body, command, task: request.task };
    }
  } catch (error) {
    console.error("usage: --state ABS_DIR COMMAND --task ID ...\n" + String(error));
    return 2;
  }
  try {
    const identity = process.env.A2A_LAUNCH ? {
      launch: process.env.A2A_LAUNCH,
      token: process.env.A2A_CAPABILITY,
      native_session: process.env.A2A_NATIVE_SESSION ?? process.env.CODEX_THREAD_ID,
    } : undefined;
    if (identity && ["submit", "status", "issue", "inbox_send", "inbox_list", "inbox_ack", "inbox_ready"].includes(String(request.command))) {
      await emit(queueWorkerRequest(request));
      return 0;
    }
    if (identity && request.command !== "signal") throw new Error("worker_command_forbidden");
    const operator = request.command === "daemon_start" || identity ? undefined : readOperatorCredential(root);
    const result = request.command === "daemon_start"
      ? await startDaemon(root, request["launch-config"] ? JSON.parse(readFileSync(String(request["launch-config"]), "utf8")) : {})
      : await daemonRequest(root, request, identity ?? operator);
    await emit(request.command === "signal" && result.ok ? {} : result);
    return result.ok ? 0 : 1;
  } catch (error) {
    await emit({
      ok: false,
      error: "daemon_call_failed",
      details: String(error),
    });
    return 1;
  }
}
if (import.meta.main) process.exitCode = await main();
