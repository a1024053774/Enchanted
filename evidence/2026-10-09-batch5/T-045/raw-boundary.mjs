// Diagnose the shared source boundary without depending on workspace installation completion.
import assert from "node:assert/strict";
import dns from "node:dns/promises";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import https from "node:https";
import { stripTypeScriptTypes, syncBuiltinESMExports } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const repo = process.env.T045_SYNARA_ROOT;
const directory = mkdtempSync(join(tmpdir(), "t045-source-boundary-"));
const sources = [
  ["outboundHttpPolicy", "packages/shared/src/outboundHttpPolicy.ts"],
  ["outboundHttp", "packages/shared/src/outboundHttp.ts"],
  ["http", "apps/server/src/providerUsage/http.ts"],
];
for (const [name, path] of sources) {
  let source = readFileSync(join(repo, path), "utf8");
  if (name === "outboundHttpPolicy" && process.env.T045_POLICY_MUTANT === "allow-benchmark-subnet") {
    assert.ok(source.includes('["198.18.0.0", 15],'));
    source = source.replace('["198.18.0.0", 15],', "");
  }
  const transformed = stripTypeScriptTypes(source, { mode: "transform" })
    .replace('"./outboundHttpPolicy"', '"./outboundHttpPolicy.mjs"')
    .replace('"@synara/shared/outboundHttp"', '"./outboundHttp.mjs"');
  writeFileSync(join(directory, `${name}.mjs`), transformed);
}

const originalLookup = dns.lookup;
const originalRequest = https.request;
let tlsRequests = 0;
const fakeIps = {
  "chatgpt.com": "198.18.0.79",
  "api.anthropic.com": "198.18.0.67",
  "api2.cursor.sh": "198.18.2.73",
};
dns.lookup = async host => {
  assert.ok(fakeIps[host], "Unexpected DNS lookup");
  return [{ address: fakeIps[host], family: 4 }];
};
https.request = () => {
  tlsRequests += 1;
  throw new Error("External TLS requests are forbidden in this fixture");
};
syncBuiltinESMExports();

const { fetchJson } = await import(pathToFileURL(join(directory, "http.mjs")));
const failures = [];
try {
  for (const [host, path] of [
    ["chatgpt.com", "/backend-api/wham/usage"],
    ["api.anthropic.com", "/api/oauth/usage"],
    ["api2.cursor.sh", "/aiserver.v1.DashboardService/GetCurrentPeriodUsage"],
  ]) {
    try {
      await fetchJson({ service: `t045-${host}`, url: `https://${host}${path}`,
        allowedOrigins: [`https://${host}`], headers: { Authorization: "Bearer fake-diagnostic-token" } });
      assert.fail("Expected reserved-address rejection before transport");
    } catch (error) {
      console.log(JSON.stringify({ host, observedError: error.name, observedCode: error.code,
        observedMessage: error.message, externalTlsRequests: tlsRequests }));
      assert.equal(error.name, "OutboundPolicyError");
      assert.equal(error.code, "private-address");
      failures.push({ host, address: fakeIps[host], name: error.name, code: error.code, message: error.message });
    }
  }
  assert.equal(tlsRequests, 0);

  // Positive control uses the real HTTP transport and the existing explicit loopback policy.
  // Two externally supplied values must survive the read; no provider endpoint is contacted.
  let usedPercent = 17;
  let localRequests = 0;
  const server = createServer((_request, response) => {
    localRequests += 1;
    response.setHeader("Content-Type", "application/json");
    response.end(JSON.stringify({ used_percent: usedPercent }));
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const controls = [];
  try {
    for (const supplied of [17, 47]) {
      usedPercent = supplied;
      const response = await fetchJson({ service: "t045-loopback", url: `${origin}/usage`, allowedOrigins: [origin], allowLoopbackHttp: true });
      assert.equal(response.status, 200);
      assert.equal(response.ok, true);
      assert.deepEqual(response.json, { used_percent: supplied });
      controls.push({ supplied, received: response.json });
    }
    assert.equal(localRequests, 2);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
  console.log(JSON.stringify({ status: "PASS", sourceFixture: directory, failures, externalTlsRequests: tlsRequests, localRequests, positiveControls: controls }, null, 2));
} finally {
  dns.lookup = originalLookup;
  https.request = originalRequest;
  syncBuiltinESMExports();
}
