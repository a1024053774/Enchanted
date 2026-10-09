import { EventEmitter } from "node:events";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { afterEach, expect, it, vi } from "vitest";

const { lookup, httpRequest, httpsRequest, resetCredits } = vi.hoisted(() => ({
  lookup: vi.fn(),
  httpRequest: vi.fn(() => { throw new Error("Unexpected HTTP socket"); }),
  httpsRequest: vi.fn(() => { throw new Error("Unexpected HTTPS socket"); }),
  resetCredits: vi.fn(async () => null),
}));
vi.mock("node:dns/promises", () => ({ lookup }));
vi.mock("node:http", async importOriginal => ({
  ...(await importOriginal<typeof import("node:http")>()), request: httpRequest,
}));
vi.mock("node:https", async importOriginal => ({
  ...(await importOriginal<typeof import("node:https")>()), request: httpsRequest,
}));
vi.mock("#server/providerUsage/codexResetCredits", () => ({
  fetchCodexResetCredits: resetCredits,
  consumeCodexResetCredit: () => { throw new Error("Unexpected Codex CLI mutation"); },
}));

import { outboundHttp } from "@synara/shared/outboundHttp";
import * as credentials from "#server/providerUsage/credentials";
import { collectProviderUsageSnapshots, __resetProviderUsageCacheForTests } from "#server/providerUsage/index";
import { claudeUsageFetcher, __setClaudeAuthNudgeDepsForTests } from "#server/providerUsage/providers/claude";
import { codexUsageFetcher } from "#server/providerUsage/providers/codex";

// Failure modes: missing or stale credentials could obscure the DNS failure; a stubbed HTTP
// response could bypass the real policy; a CLI refresh or socket could leak outside the fixture.
// Use fresh fake files and a real Cursor database; replace only DNS and forbid external effects.
const nowMs = 1791518400000;
const fakeJwt = `${Buffer.from('{"alg":"none"}').toString("base64url")}.${Buffer.from(JSON.stringify({ exp: nowMs / 1000 + 86400 })).toString("base64url")}.fixture`;
const fakeIps: Record<string, string> = {
  "chatgpt.com": "198.18.0.79",
  "api.anthropic.com": "198.18.0.67",
  "api2.cursor.sh": "198.18.2.73",
};

afterEach(() => {
  vi.restoreAllMocks();
  lookup.mockReset();
  httpRequest.mockClear();
  httpsRequest.mockReset();
  resetCredits.mockClear();
  __resetProviderUsageCacheForTests();
  __setClaudeAuthNudgeDepsForTests(null);
});

it.each([17, 47])("reads supplied usage %s through the production batch entry without real sockets or refresh", async (percent) => {
  const homeDir = mkdtempSync(join(tmpdir(), "t045-fake-home-"));
  const codexHome = join(homeDir, ".codex");
  const claudeHome = join(homeDir, ".claude");
  const cursorHome = join(homeDir, ".config/Cursor/User/globalStorage");
  for (const dir of [codexHome, claudeHome, cursorHome]) mkdirSync(dir, { recursive: true });
  const codexPath = join(codexHome, "auth.json");
  const claudePath = join(claudeHome, ".credentials.json");
  writeFileSync(codexPath, JSON.stringify({ tokens: { access_token: fakeJwt, account_id: "fake-account" } }));
  writeFileSync(claudePath, JSON.stringify({ claudeAiOauth: { accessToken: "fake-claude-access", expiresAt: nowMs + 86400000, scopes: ["user:profile"] } }));
  const filesBefore = [readFileSync(codexPath, "utf8"), readFileSync(claudePath, "utf8")];
  const database = new DatabaseSync(join(cursorHome, "state.vscdb"));
  database.exec("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)");
  database.prepare("INSERT INTO ItemTable VALUES (?, ?)").run("cursorAuth/accessToken", fakeJwt);
  database.close();
  const ctx = { homeDir, env: { HOME: homeDir, CODEX_HOME: codexHome }, platform: "linux" as const, nowMs, isolateCredentials: true, skipLocalUsage: true };

  lookup.mockImplementation(async (host: string) => {
    if (!fakeIps[host]) throw new Error(`Unexpected DNS name: ${host}`);
    return [{ address: fakeIps[host], family: 4 }];
  });
  const keychain = vi.spyOn(credentials, "readKeychainPassword").mockImplementation(async () => { throw new Error("Unexpected Keychain read"); });
  const refresh = vi.spyOn(credentials, "refreshOAuthAccessToken").mockImplementation(async () => { throw new Error("Unexpected refresh redemption"); });
  const write = vi.spyOn(credentials, "writeJsonFileAtomic").mockImplementation(async () => { throw new Error("Unexpected credential write"); });
  const nudge = vi.fn(async () => { throw new Error("Unexpected Claude CLI refresh"); });
  __setClaudeAuthNudgeDepsForTests({ acquireLock: async () => () => {}, runAuthStatus: nudge });

  // Mock only transport, after the real origin, DNS and address policy. Never create a socket.
  httpsRequest.mockImplementation((url, options, callback) => {
    const host = url.hostname;
    if (!fakeIps[host]) throw new Error(`Unexpected transport host: ${host}`);
    const request = new EventEmitter();
    request.write = () => {};
    request.end = () => {
      options.lookup(host, { all: true }, (error, addresses) => {
        expect(error).toBeNull();
        expect(addresses).toEqual([{ address: fakeIps[host], family: 4 }]);
        const payload = host === "chatgpt.com"
          ? { rate_limit: { primary_window: { used_percent: percent } } }
          : host === "api.anthropic.com"
            ? { five_hour: { utilization: percent } }
            : url.pathname.endsWith("GetCreditGrantsBalance")
              ? { hasCreditGrants: false }
              : { planUsage: { totalPercentUsed: percent } };
        const response = new EventEmitter();
        response.statusCode = 200;
        response.headers = { "content-type": "application/json" };
        callback(response);
        response.emit("data", Buffer.from(JSON.stringify(payload)));
        response.emit("end");
      });
    };
    return request;
  });
  const snapshots = await collectProviderUsageSnapshots(ctx, { providers: ["codex", "claudeAgent", "cursor"], forceRefresh: true });
  console.log(JSON.stringify({ fixtureHome: homeDir, snapshots, dnsHosts: lookup.mock.calls.map(call => call[0]), realSockets: 0, mockedTransports: httpsRequest.mock.calls.length, refreshes: refresh.mock.calls.length + nudge.mock.calls.length, writes: write.mock.calls.length }));
  expect(snapshots).toHaveLength(3);
  expect([...new Set(lookup.mock.calls.map(call => call[0]))].sort()).toEqual([
    "api.anthropic.com", "api2.cursor.sh", "chatgpt.com",
  ]);
  expect(httpRequest).not.toHaveBeenCalled();
  expect(httpsRequest).toHaveBeenCalledTimes(4);
  expect(keychain).not.toHaveBeenCalled();
  expect(refresh).not.toHaveBeenCalled();
  expect(nudge).not.toHaveBeenCalled();
  expect(write).not.toHaveBeenCalled();
  expect(resetCredits).toHaveBeenCalledOnce();
  expect([readFileSync(codexPath, "utf8"), readFileSync(claudePath, "utf8")]).toEqual(filesBefore);
  // Input-supplied quota must survive the real HTTP decoder and provider parsers.
  expect(snapshots.map(snapshot => snapshot.status)).toEqual(["ok", "ok", "ok"]);
  expect(snapshots.map(snapshot => snapshot.limits[0]?.usedPercent)).toEqual([percent, percent, percent]);
});

it("distinguishes credential absence and unsupported auth from an unreachable endpoint", async () => {
  const homeDir = mkdtempSync(join(tmpdir(), "t045-auth-cases-"));
  const ctx = { homeDir, env: {}, platform: "linux" as const, nowMs, isolateCredentials: true };
  const request = vi.spyOn(outboundHttp, "request").mockImplementation(async () => { throw new Error("Unexpected request without usable auth"); });
  const missing = await codexUsageFetcher.fetch(ctx);
  const environmentToken = await claudeUsageFetcher.fetch({ ...ctx, env: { CLAUDE_CODE_OAUTH_TOKEN: "fake-environment-token" } });
  mkdirSync(join(homeDir, ".codex"));
  writeFileSync(join(homeDir, ".codex/auth.json"), JSON.stringify({ OPENAI_API_KEY: "fake-api-key" }));
  const apiKey = await codexUsageFetcher.fetch({ ...ctx, env: { CODEX_HOME: join(homeDir, ".codex") } });
  console.log(JSON.stringify({ authCases: { missing, environmentToken, apiKey } }));
  expect(missing.status).toBe("needs-auth");
  expect(environmentToken.status).toBe("unsupported");
  expect(apiKey.status).toBe("unsupported");
  expect(request).not.toHaveBeenCalled();
});
