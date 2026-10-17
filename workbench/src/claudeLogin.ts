import { appendFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { Refusal } from "./gates/core.ts";
import { ClaudeForwarder, upstreamUrl } from "./claudeForwarder.ts";
import { countForwarderRecords, homeReferences, preflightObserved, redactCredentials, safeTerminal, scanCredentialFiles } from "./claudeLoginFacts.ts";
import type { ClaudeLaunchInput, ClaudeLoginIsolation } from "./claudeLaunch.ts";

const exec = promisify(execFile);
const helper = fileURLToPath(new URL("./claudeLoginFiles.py", import.meta.url));
const scopes = [".claude", ".claude.json", ".claude.json.backup", "Library/Keychains"];
async function privateFiles(input: object, env: Record<string, string>) {
  return new Promise<any>((resolve, reject) => {
    const child = spawn("/usr/bin/python3", ["-B", helper], { env, stdio: ["pipe", "pipe", "pipe"] });
    let output = "", bytes = 0, failed = false;
    const timer = setTimeout(() => { failed = true; child.kill("SIGKILL"); }, 15_000);
    child.stdout.on("data", part => { bytes += part.length; if (bytes > 32 * 1024 * 1024) { failed = true; child.kill("SIGKILL"); } else output += part; });
    child.stderr.resume();
    child.on("error", () => { clearTimeout(timer); reject(new Refusal("login_private_files_failed")); });
    child.on("close", code => {
      clearTimeout(timer);
      if (code !== 0 || failed) { reject(new Refusal("login_private_files_failed")); return; }
      try { resolve(JSON.parse(output)); } catch { reject(new Refusal("login_private_files_failed")); }
    });
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify(input));
  });
}

export function loginSandbox(home: string, executable: string, repo: string, state: string, roles: string, port?: number) {
  const source = realpathSync(fileURLToPath(new URL("..", import.meta.url)));
  const read = [realpathSync(executable), realpathSync(process.execPath)];
  const write = [repo, state, roles];
  const exceptions = [...read.map(path => `(literal ${JSON.stringify(path)})`),
    ...[source, ...write].map(path => `(subpath ${JSON.stringify(path)})`)];
  const deniedRead = `(require-all (subpath ${JSON.stringify(home)}) (require-not (require-any ${exceptions.join(" ")})))`;
  const deniedWrite = `(require-all (subpath ${JSON.stringify(home)}) (require-not (require-any ${write.map(path => `(subpath ${JSON.stringify(path)})`).join(" ")})))`;
  return `(version 1)(allow default)
    (deny file-read* ${deniedRead})(deny file-write* ${deniedWrite})
    ${scopes.map(scope => `(deny file-read* file-write* (subpath ${JSON.stringify(join(home, scope))}))`).join("\n")}
    (deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))
    (deny network*)
    (allow network-outbound (remote unix-socket (path-literal ${JSON.stringify(join(state, "control.sock"))})))
    ${port ? `(allow network-outbound (remote tcp4 "localhost:${port}"))` : ""}`;
}

export class ClaudeLogin {
  readonly isolation: ClaudeLoginIsolation;
  readonly realHome: string;
  readonly #env: Record<string, string>;
  readonly #input: ClaudeLaunchInput;
  readonly #repo: string;
  #before: any;
  #secrets: string[] = [];
  #forwarder: ClaudeForwarder | null = null;
  #raw = "";
  #published = "";
  #finish: Promise<void> | null = null;
  #stage = "inventory";
  versionProbe!: { argv: string[]; stdout: string; stderr: string };
  private constructor(input: ClaudeLaunchInput, repo: string) {
    this.#input = input; this.#repo = repo; this.realHome = realpathSync(homedir());
    const homeRoot = realpathSync(mkdtempSync("/private/tmp/a2a-claude-login-"));
    for (const path of ["home", "home/.claude", "tmp", "shell"]) mkdirSync(join(homeRoot, path), { mode: 0o700 });
    this.isolation = { homeRoot, home: join(homeRoot, "home"), config: join(homeRoot, "home/.claude"),
      tmp: join(homeRoot, "tmp"), shell: join(homeRoot, "shell"), debug: join(homeRoot, "debug.log"),
      api_url: "", sandbox_profile: "", audit_directory: join(input.state, "login-audits", input.launch) };
    this.#env = { PATH: "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", HOME: this.isolation.home,
      CLAUDE_CONFIG_DIR: this.isolation.config, TMPDIR: this.isolation.tmp, ZDOTDIR: this.isolation.shell,
      LANG: "en_US.UTF-8", TERM: "xterm-256color" };
  }
  static async prepare(input: ClaudeLaunchInput, repo: string) {
    if (input.version !== "2.1.302") throw new Refusal("normal_login_version_requires_probe");
    if (!["file", "macos-keychain"].includes(input.credential_source ?? "")) throw new Refusal("login_credential_source_required");
    upstreamUrl(input.upstream_url ?? "");
    const value = new ClaudeLogin(input, realpathSync(repo));
    try { await value.prepare(); return value; }
    catch (error) {
      await value.discard();
      throw new Refusal("normal_login_preparation_failed", { stage: value.#stage,
        cause: error instanceof Refusal ? error.code : "private_operation_failed" });
    }
  }
  private async prepare() {
    this.#before = await privateFiles({ operation: "inventory", home: this.realHome }, this.#env);
    this.#stage = "version";
    const roles = realpathSync(join(this.#input.root, "roles"));
    const profile = loginSandbox(this.realHome, this.#input.executable, this.#repo, this.#input.state, roles);
    const command = ["-p", profile, this.#input.executable, "--version"];
    const version = await exec("/usr/bin/sandbox-exec", command, { env: this.#env, cwd: this.#repo, timeout: 10000, maxBuffer: 65536 });
    if (version.stdout.trim() !== "2.1.302 (Claude Code)") throw new Refusal("controller_version_mismatch");
    this.versionProbe = { argv: ["/usr/bin/sandbox-exec", ...command], stdout: version.stdout, stderr: "" };
    this.#stage = "credential_copy";
    const auth = await privateFiles({ operation: "auth", home: this.realHome, source: this.#input.credential_source }, this.#env);
    this.#secrets = [auth.claudeAiOauth.accessToken, auth.claudeAiOauth.refreshToken].filter(Boolean);
    writeFileSync(join(this.isolation.config, ".credentials.json"), JSON.stringify(auth), { flag: "wx", mode: 0o600 });
    writeFileSync(join(this.isolation.config, ".claude.json"), JSON.stringify({ hasCompletedOnboarding: true,
      projects: { [this.#repo.normalize("NFC")]: { hasTrustDialogAccepted: true } } }), { flag: "wx", mode: 0o600 });
    this.#stage = "forwarder";
    mkdirSync(dirname(this.isolation.audit_directory), { recursive: true, mode: 0o700 });
    this.#forwarder = await ClaudeForwarder.start({ directory: this.isolation.audit_directory,
      upstream_url: this.#input.upstream_url!, access_token: this.#secrets[0]!, secrets: this.#secrets });
    this.isolation.api_url = this.#forwarder.url;
    this.isolation.sandbox_profile = loginSandbox(this.realHome, this.#input.executable, this.#repo, this.#input.state, roles,
      Number(new URL(this.isolation.api_url).port));
    this.#stage = "auth_status";
    const status = await exec("/usr/bin/sandbox-exec", ["-p", this.isolation.sandbox_profile, this.#input.executable, "auth", "status", "--json"],
      { env: { ...this.#env, ANTHROPIC_BASE_URL: this.isolation.api_url }, cwd: this.#repo, timeout: 10000, maxBuffer: 65536 });
    if (JSON.parse(status.stdout).loggedIn !== true) throw new Refusal("isolated_login_not_recognized");
  }
  observe(data: string, publicTrace: string) {
    this.#raw += data;
    if (Buffer.byteLength(this.#raw) > 32 * 1024 * 1024) throw new Refusal("login_terminal_limit");
    const safe = safeTerminal(this.#raw, this.#secrets);
    if (!safe.startsWith(this.#published)) throw new Refusal("login_terminal_redaction_changed");
    appendFileSync(publicTrace, safe.slice(this.#published.length)); this.#published = safe;
  }
  finish(record: unknown) {
    return this.#finish ??= this.finalize(record);
  }
  private async finalize(record: unknown) {
    try {
      await this.#forwarder!.close();
      const after = await privateFiles({ operation: "inventory", home: this.realHome }, this.#env);
      const changed = [...new Set([...Object.keys(this.#before), ...Object.keys(after)])]
        .filter(path => JSON.stringify(this.#before[path]) !== JSON.stringify(after[path]));
      const scan = scanCredentialFiles(this.#input.state, this.#secrets);
      const counts = countForwarderRecords(this.#forwarder!.ledger, this.#forwarder!.counters.received);
      const facts = { schema: 1, task: "T-093", launch: this.#input.launch, cli_version: "2.1.302",
        counts, forwarder: this.#forwarder!.counters,
        launch_home_references: homeReferences(record, this.realHome),
        inventory: { scope: scopes, excludes: ["atime", "file contents", "symlink targets", "other HOME paths"],
          before_entries: Object.keys(this.#before).length, after_entries: Object.keys(after).length, changed,
          differences: changed.map(path => ({ path, before: this.#before[path] ?? null, after: after[path] ?? null })),
          attribution: "No causal attribution; concurrent sessions may write these paths." },
        credential_scan: { ...scan, scope: this.#input.state, timing: "session finalization" },
        onboarding: { generated: true, trusted_project: this.#repo, internal_state_version: "2.1.302",
          preflight_observed: preflightObserved(this.#raw), direct_network_blocked: true }, isolated_home_removed: false };
      // Inventory paths may themselves contain a secret. Redact before persistence.
      rmSync(this.isolation.homeRoot, { recursive: true });
      facts.isolated_home_removed = !existsSync(this.isolation.homeRoot);
      writeFileSync(join(this.isolation.audit_directory, "facts.json"), redactCredentials(JSON.stringify(facts, null, 2), this.#secrets) + "\n", { flag: "wx", mode: 0o600 });
    } finally { await this.discard(); }
  }
  async discard() {
    await this.#forwarder?.close();
    rmSync(this.isolation.homeRoot, { recursive: true, force: true });
    this.#secrets = []; this.#raw = ""; this.#published = "";
  }
}
