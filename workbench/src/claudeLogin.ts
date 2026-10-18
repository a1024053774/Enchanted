import { appendFileSync, closeSync, constants, existsSync, fstatSync, linkSync, openSync, readFileSync, realpathSync, unlinkSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { execFile } from "node:child_process";
import { isDeepStrictEqual, promisify } from "node:util";
import { Refusal } from "./gates/core.ts";
import { countForwarderRecords, credentialHits, homeReferences, preflightObserved, redactCredentials, safeTerminal, scanCredentialFiles } from "./claudeLoginFacts.ts";
import { recordLoginProcess } from "./claudeLoginProcessTrace.ts";
import type { ClaudeLaunchInput, ClaudeLoginIsolation } from "./claudeLaunch.ts";

const exec = promisify(execFile);
const scopes = [".claude", ".claude.json", ".claude.json.backup", "Library/Keychains"];
const load = (path: string) => JSON.parse(readFileSync(path, "utf8"));
async function waitFile(path: string, timeout = 20_000) {
  const until = Date.now() + timeout;
  while (!existsSync(path)) {
    if (Date.now() >= until) throw new Refusal("login_service_deadline");
    await new Promise(resolve => setTimeout(resolve, 30));
  }
  return load(path);
}
export class ClaudeLogin {
  readonly isolation: ClaudeLoginIsolation;
  readonly realHome: string;
  readonly #input: ClaudeLaunchInput;
  readonly #session: any;
  readonly #env: Record<string, string>;
  #before: any;
  #secrets: string[] = [];
  #raw = "";
  #published = "";
  #finish: Promise<void> | null = null;
  #closed: any;
  versionProbe!: { argv: string[]; stdout: string; stderr: string };
  private constructor(input: ClaudeLaunchInput, session: any) {
    this.#input = input; this.#session = session; this.realHome = session.real_home;
    const root = session.private_root;
    this.isolation = { homeRoot: root, home: join(root, "home"), config: join(root, "home/.claude"),
      tmp: join(root, "tmp"), shell: join(root, "shell"), debug: join(root, "debug.log"),
      api_url: `http://127.0.0.1:${session.forward_port}`, audit_directory: session.audit_directory };
    this.#env = { PATH: "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", HOME: this.isolation.home,
      CLAUDE_CONFIG_DIR: this.isolation.config, TMPDIR: this.isolation.tmp, ZDOTDIR: this.isolation.shell,
      LANG: "en_US.UTF-8", TERM: "xterm-256color", ANTHROPIC_BASE_URL: this.isolation.api_url,
      NODE_OPTIONS: process.env.NODE_OPTIONS!, A2A_PROFILE_PROCESS_LOG: process.env.A2A_PROFILE_PROCESS_LOG! };
  }
  static async prepare(input: ClaudeLaunchInput, repo: string) {
    if (input.version !== "2.1.302") throw new Refusal("normal_login_version_requires_probe");
    const path = process.env.A2A_CLAUDE_LOGIN_SESSION;
    if (!path) throw new Refusal("normal_login_outer_profile_required");
    const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW);
    let session;
    try {
      const info = fstatSync(fd);
      if (!info.isFile() || info.uid !== process.getuid!() || info.mode & 0o077) throw new Refusal("private_login_session_required");
      session = JSON.parse(readFileSync(fd, "utf8"));
    } finally { closeSync(fd); }
    if (session.schema !== 1 || session.c_root_pid !== process.pid || session.repo !== realpathSync(repo) ||
        session.deadline * 1000 <= Date.now() || session.auth_original_reads !== 1 || !isDeepStrictEqual(session.manifest, input))
      throw new Refusal("prepared_login_session_mismatch");
    try { writeFileSync(join(session.private_root, "consumed"), input.launch, { flag: "wx", mode: 0o600 }); }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code === "EEXIST") throw new Refusal("prepared_login_already_consumed");
      throw error;
    }
    const value = new ClaudeLogin(input, session);
    try { await value.prepare(); return value; }
    catch { await value.discard(); throw new Refusal("normal_login_preparation_failed"); }
  }
  private async prepare() {
    const s = this.#session;
    const services = load(join(s.private_root, "services.json"));
    if (Object.values(services).some((v: any) => v.bootstrap_exit !== 0)) throw new Refusal("login_service_profile_failed");
    const forwarder = await waitFile(join(s.forwarder_directory, "ready.json"));
    const metadata = await waitFile(join(s.metadata_directory, "ready.json"));
    if (forwarder.pid !== services.F.pid || metadata.pid !== services.D.pid || forwarder.url !== this.isolation.api_url)
      throw new Refusal("login_service_identity_mismatch");
    this.#before = load(join(s.private_root, "metadata/before.json"));
    const auth = load(join(this.isolation.config, ".credentials.json"));
    this.#secrets = [auth.claudeAiOauth.accessToken, auth.claudeAiOauth.refreshToken].filter(Boolean);
    const version = exec(this.#input.executable, ["--version"], { env: this.#env, cwd: s.repo, timeout: 10000, maxBuffer: 65536 });
    recordLoginProcess("version", (version as any).child.pid);
    const checked = await version;
    if (checked.stdout.trim() !== "2.1.302 (Claude Code)") throw new Refusal("controller_version_mismatch");
    this.versionProbe = { argv: [this.#input.executable, "--version"], stdout: checked.stdout, stderr: "" };
    const status = exec(this.#input.executable, ["auth", "status", "--json"], { env: this.#env, cwd: s.repo, timeout: 10000, maxBuffer: 65536 });
    recordLoginProcess("auth status", (status as any).child.pid);
    if (JSON.parse((await status).stdout).loggedIn !== true) throw new Refusal("isolated_login_not_recognized");
  }
  recordChild(pid: number, role: string) {
    recordLoginProcess(role, pid);
    if (role === "PTY helper -> zsh -> CLI") appendFileSync(join(this.#session.private_root, "pty-groups.jsonl"), JSON.stringify({ pgrp: pid }) + "\n", { mode: 0o600 });
  }
  async preflight(record: unknown) {
    const s = this.#session;
    writeFileSync(join(s.forwarder_directory, "preflight"), "\n", { flag: "wx", mode: 0o600 });
    const counters = await waitFile(join(s.forwarder_directory, "preflight-counters.json"));
    const ledger = "forwarder/journal/requests.jsonl";
    const scan = scanCredentialFiles(this.#input.state, this.#secrets);
    const facts = { schema: 2, phase: "before_cli_input", task: this.#input.task, launch: this.#input.launch,
      network_boundary: { os_host_filter: false, os_remote_ports: [s.upstream_port], application_host_lock: true },
      session: this.#input.session, code_revision: this.#input.code_revision, ledger,
      forwarder: counters, counts: countForwarderRecords(join(s.audit_directory, ledger), counters.received),
      launch_home_references: homeReferences(record, this.realHome),
      inventory: { scope: scopes, before_phase: "before_original_auth_read", before_entries: Object.keys(this.#before).length,
        comparison_pending: true, pass_condition: false, acceptance_basis: "User decision A; main c06a73179" },
      credential_scan: { ...scan, launch_record_hits: credentialHits(JSON.stringify(record), this.#secrets),
        timing: "before launch registration and CLI spawn", scope: "state files plus prepared launch record in memory" },
      profiles: s.profiles, initial_inventory_process: s.initial_inventory_process,
      notice: "Facts only. This report does not grant permission to send a model prompt." };
    const encoded = redactCredentials(JSON.stringify(facts, null, 2), this.#secrets) + "\n";
    if (credentialHits(encoded, this.#secrets)) throw new Refusal("login_fact_redaction_failed");
    writeFileSync(join(s.audit_directory, "preflight.json"), encoded, { flag: "wx", mode: 0o600 });
  }
  observe(data: string, publicTrace: string) {
    this.#raw += data;
    if (Buffer.byteLength(this.#raw) > 32 * 1024 * 1024) throw new Refusal("login_terminal_limit");
    const safe = safeTerminal(this.#raw, this.#secrets);
    if (!safe.startsWith(this.#published)) throw new Refusal("login_terminal_redaction_changed");
    appendFileSync(publicTrace, safe.slice(this.#published.length)); this.#published = safe;
  }
  finish(record: unknown) { return this.#finish ??= this.finalize(record); }
  private async stopServices() {
    const s = this.#session;
    if (!existsSync(join(s.forwarder_directory, "stop"))) writeFileSync(join(s.forwarder_directory, "stop"), "\n", { flag: "wx", mode: 0o600 });
    this.#closed = await waitFile(join(s.forwarder_directory, "closed.json"));
    if (!existsSync(join(s.metadata_directory, "stop.json"))) {
      const probes = join(s.private_root, "home-probes.json");
      const pending = join(s.metadata_directory, "stop.pending-" + randomUUID());
      writeFileSync(pending, JSON.stringify({ home_probe_paths: existsSync(probes) ? load(probes) : [] }), { flag: "wx", mode: 0o600 });
      try { linkSync(pending, join(s.metadata_directory, "stop.json")); } finally { unlinkSync(pending); }
    }
    return await waitFile(join(s.metadata_directory, "closed.json"));
  }
  private async removeHome() {
    const directory = this.#session.metadata_directory;
    if (!existsSync(join(directory, "cleanup"))) writeFileSync(join(directory, "cleanup"), "\n", { flag: "wx", mode: 0o600 });
    return await waitFile(join(directory, "removed.json"));
  }
  private async finalize(record: unknown) {
    const s = this.#session;
    try {
      const metadata = await this.stopServices();
      const after = load(join(s.private_root, "metadata/after.json"));
      const changed = [...new Set([...Object.keys(this.#before), ...Object.keys(after)])].filter(path => JSON.stringify(this.#before[path]) !== JSON.stringify(after[path]));
      const ledger = "forwarder/journal/requests.jsonl";
      const counts = countForwarderRecords(join(s.audit_directory, ledger), this.#closed.received);
      const scan = scanCredentialFiles(this.#input.state, this.#secrets);
      const config = load(join(this.isolation.config, ".claude.json"));
      const debug = existsSync(this.isolation.debug) ? readFileSync(this.isolation.debug, "utf8") : "";
      const stateIntact = config.hasCompletedOnboarding === true && config.projects?.[s.repo.normalize("NFC")]?.hasTrustDialogAccepted === true;
      const removed = await this.removeHome();
      const facts = { schema: 2, build_ticket: "T-093", task: this.#input.task, launch: this.#input.launch,
        network_boundary: { os_host_filter: false, os_remote_ports: [s.upstream_port], application_host_lock: true },
        session: this.#input.session, thread: this.#input.thread, preset: this.#input.preset,
        code_revision: this.#input.code_revision, source_snapshot: this.#input.source_snapshot,
        spec_rev: (record as Record<string, unknown>).spec_rev, cli_version: "2.1.302", ledger, counts,
        forwarder: { received: this.#closed.received, forwarded: this.#closed.forwarded, journal_failure: this.#closed.journal_failure },
        launch_home_references: homeReferences(record, this.realHome),
        inventory: { pass_condition: false, acceptance_basis: "User decision A; main c06a73179 T-093 decision section", collection_complete: metadata.collection_complete,
          before_phase: "before_original_auth_read", after_phase: "after_cli_exit",
          scope: scopes, excludes: ["atime", "file contents", "symlink targets", "other HOME paths"], before_entries: Object.keys(this.#before).length,
          after_entries: Object.keys(after).length, changed, differences: changed.map(path => ({ path, before: this.#before[path] ?? null, after: after[path] ?? null })),
          attribution: "No causal attribution; concurrent sessions may write these paths." },
        credential_scan: { ...scan, scope: this.#input.state, timing: "session finalization" },
        onboarding: { generated: true, state_intact: stateIntact, trusted_project: s.repo, internal_state_version: "2.1.302",
          preflight_observed: preflightObserved(this.#raw + "\n" + debug), signal_sources: ["terminal", "private debug log"],
          silent_denied_attempts: "Not measured; C denies direct upstream connections.", direct_network_blocked: true },
        profiles: s.profiles, processes: { C: process.pid, baseline: s.initial_inventory_process, F: this.#closed, D: metadata }, auth_original_reads: s.auth_original_reads,
        isolated_home_removed: removed.isolated_home_removed, cleanup: removed };
      const encoded = redactCredentials(JSON.stringify(facts, null, 2), this.#secrets) + "\n";
      if (credentialHits(encoded, this.#secrets)) throw new Refusal("login_fact_redaction_failed");
      writeFileSync(join(s.audit_directory, "facts.json"), encoded, { flag: "wx", mode: 0o600 });
    } catch (error) { await this.discard(); throw error; }
    finally { this.#secrets = []; this.#raw = ""; this.#published = ""; }
  }
  async discard() {
    // D owns removal even when preparation or the C root fails. Do not delete
    // a live CLI's HOME from this error path, or report an unconfirmed cleanup.
    try {
      if (!existsSync(this.#session.private_root)) return;
      const abort = join(this.#session.metadata_directory, "abort");
      if (!existsSync(abort)) writeFileSync(abort, "\n", { flag: "wx", mode: 0o600 });
      await waitFile(join(this.#session.metadata_directory, "removed.json"));
    }
    finally { this.#secrets = []; this.#raw = ""; this.#published = ""; }
  }
}
