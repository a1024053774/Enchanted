import { existsSync, linkSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { ClaudeForwarder } from "./claudeForwarder.ts";

export async function runForwarder(sessionPath: string) {
  const session = JSON.parse(readFileSync(sessionPath, "utf8"));
  const directory = session.forwarder_directory;
  const host = JSON.parse(readFileSync(join(directory, "host.json"), "utf8"));
  const save = (name: string, value: unknown) => {
    const temporary = join(directory, name + ".pending-" + randomUUID());
    writeFileSync(temporary, JSON.stringify(value) + "\n", { flag: "wx", mode: 0o600 });
    try { linkSync(temporary, join(directory, name)); } finally { unlinkSync(temporary); }
  };
  let relay: ClaudeForwarder | undefined;
  try {
    if (host.pid !== process.pid || !Number.isInteger(session.forward_port) || session.forward_port < 1) throw new Error("invalid_forwarder_host");
    const { claudeAiOauth: oauth } = JSON.parse(readFileSync(join(session.private_root, "home/.claude/.credentials.json"), "utf8"));
    const secrets = [oauth.accessToken, oauth.refreshToken].filter(value => typeof value === "string" && value.length);
    relay = await ClaudeForwarder.start({ directory: join(directory, "journal"), upstream_url: session.manifest.upstream_url,
      upstream_address: session.upstream_address, port: session.forward_port, access_token: oauth.accessToken, secrets });
    save("ready.json", { ...host, url: relay.url, profile: "F" });
    let checkpoint = false;
    await new Promise<void>((resolve, reject) => {
      const timer = setInterval(() => {
        try {
          if (!checkpoint && existsSync(join(directory, "preflight"))) {
            save("preflight-counters.json", { ...relay!.counters, at: new Date().toISOString() });
            checkpoint = true;
          }
          if (existsSync(join(directory, "stop")) || Date.now() >= session.deadline * 1000) { clearInterval(timer); resolve(); }
        } catch (error) { clearInterval(timer); reject(error); }
      }, 30);
    });
    await relay.close();
    save("closed.json", { ...host, ...relay.counters, deadline_reached: Date.now() >= session.deadline * 1000 });
  } catch {
    // JSON parse/transport exceptions can contain input data. No raw error or
    // terminal output is persisted by the credential-holding process.
    await relay?.close();
    save("failed.json", { ...host, error: "forwarder_session_failed" });
    process.exitCode = 2;
  }
}
if (import.meta.main) await runForwarder(process.argv[2]);
