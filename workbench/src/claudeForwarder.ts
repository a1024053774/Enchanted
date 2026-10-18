import { createServer, request as httpRequest, type IncomingMessage, type ServerResponse, type ClientRequest } from "node:http";
import { request as httpsRequest } from "node:https";
import { closeSync, constants, fstatSync, fsyncSync, lstatSync, mkdirSync, openSync, writeSync } from "node:fs";
import { join } from "node:path";
import { isIP, type Socket } from "node:net";
import { Refusal } from "./gates/core.ts";
import { credentialHits, redactCredentials } from "./claudeLoginFacts.ts";

const hop = new Set(["host", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"]);
export function upstreamUrl(value: string) {
  const url = new URL(value);
  if (url.username || url.password || url.pathname !== "/" || url.search || url.hash ||
      !(url.protocol === "https:" && url.hostname && (!url.port || Number(url.port) > 0) ||
        url.protocol === "http:" && url.hostname === "127.0.0.1" && Number(url.port) > 0)) throw new Refusal("invalid_login_upstream");
  return url;
}
export class ClaudeForwarder {
  readonly directory: string;
  readonly ledger: string;
  readonly #token: string;
  readonly #secrets: readonly string[];
  readonly #upstream: URL;
  readonly #address: string;
  readonly #server = createServer((req, res) => this.receive(req, res));
  readonly #sockets = new Set<Socket>();
  readonly #active = new Set<() => void>();
  readonly #fd: number;
  #url = "";
  #closed = false;
  #received = 0;
  #forwarded = 0;
  #failure: string | null = null;
  private constructor(options: { directory: string; upstream_url: string; upstream_address: string; port: number; access_token: string; secrets: readonly string[] }) {
    this.directory = options.directory; this.#upstream = upstreamUrl(options.upstream_url);
    this.#address = options.upstream_address;
    this.#token = options.access_token; this.#secrets = options.secrets;
    mkdirSync(this.directory, { mode: 0o700 });
    this.ledger = join(this.directory, "requests.jsonl");
    this.#fd = openSync(this.ledger, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_APPEND | constants.O_NOFOLLOW, 0o600);
    this.#server.on("connection", socket => { this.#sockets.add(socket); socket.on("close", () => this.#sockets.delete(socket)); });
  }
  static async start(options: { directory: string; upstream_url: string; upstream_address: string; port: number; access_token: string; secrets: readonly string[] }) {
    if (!Number.isInteger(options.port) || options.port < 0 || options.port > 65535 || isIP(options.upstream_address) !== 4)
      throw new Refusal("explicit_forwarder_port_and_address_required");
    const value = new ClaudeForwarder(options);
    try {
      await new Promise<void>((resolve, reject) => {
        value.#server.once("error", reject);
        value.#server.listen(options.port, "127.0.0.1", () => { value.#server.off("error", reject); resolve(); });
      });
      const address = value.#server.address();
      if (!address || typeof address === "string") throw new Refusal("forwarder_not_bound");
      value.#url = `http://127.0.0.1:${address.port}`;
      return value;
    } catch (error) { closeSync(value.#fd); throw error; }
  }
  get url() { return this.#url; }
  get counters() { return { received: this.#received, forwarded: this.#forwarded, journal_failure: this.#failure }; }
  private record(value: Record<string, unknown>) {
    const disk = lstatSync(this.ledger), owned = fstatSync(this.#fd);
    if (disk.isSymbolicLink() || disk.ino !== owned.ino || disk.dev !== owned.dev) throw new Refusal("forwarder_journal_replaced");
    const safe = Object.fromEntries(Object.entries({ at: new Date().toISOString(), ...value }).map(([key, item]) =>
      [key, typeof item === "string" ? redactCredentials(item, this.#secrets) :
        typeof item === "number" && credentialHits(String(item), this.#secrets) ? "<CREDENTIAL>" : item]));
    const bytes = Buffer.from(JSON.stringify(safe) + "\n");
    if (credentialHits(bytes.toString("utf8"), this.#secrets)) throw new Refusal("forwarder_metadata_redaction_failed");
    let offset = 0;
    while (offset < bytes.length) offset += writeSync(this.#fd, bytes, offset, bytes.length - offset);
    fsyncSync(this.#fd);
  }
  private receive(req: IncomingMessage, res: ServerResponse) {
    if (this.#closed) { req.destroy(); return; }
    const sequence = ++this.#received, rawPath = (req.url ?? "").split("?", 1)[0]!;
    const path = credentialHits(rawPath, this.#secrets) ? "<CREDENTIAL-PATH>" : rawPath;
    const authenticated = req.headers.authorization === "Bearer " + this.#token;
    try {
      if (this.#failure) throw new Refusal("forwarder_journal_failed");
      this.record({ kind: "request", sequence, method: req.method, path,
        body_bytes_declared: /^\d+$/.test(String(req.headers["content-length"])) ? Number(req.headers["content-length"]) : null,
        bearer_matches_copied_login: authenticated });
    } catch { this.#failure = "journal_write_failed"; req.resume(); res.writeHead(503).end(); return; }
    let finished = false, bytes = 0, upstream: ClientRequest | undefined;
    const settle = (status: number | null, error: string | null) => {
      if (finished) return;
      finished = true; this.#active.delete(cancel);
      try { this.record({ kind: "outcome", sequence, status, error, body_bytes: bytes }); }
      catch { this.#failure = "journal_write_failed"; }
    };
    const cancel = () => { settle(null, "forwarder_closed"); upstream?.destroy(); req.destroy(); res.destroy(); };
    this.#active.add(cancel);
    req.on("data", data => { bytes += data.length; });
    req.on("aborted", () => { settle(null, "client_aborted"); upstream?.destroy(); });
    if (!authenticated || !req.url?.startsWith("/") || req.url.startsWith("//")) {
      req.resume(); settle(401, "login_bearer_required"); res.writeHead(401, { "content-type": "application/json" }).end('{"error":"login_bearer_required"}'); return;
    }
    const headers = Object.fromEntries(Object.entries(req.headers).filter(([key]) => !hop.has(key)));
    const send = this.#upstream.protocol === "https:" ? httpsRequest : httpRequest;
    // Journal request and fsync are complete before this network boundary.
    this.#forwarded++;
    try { upstream = send(this.#upstream, { method: req.method, path: req.url, headers, family: 4, autoSelectFamily: false, agent: false,
      lookup: (_hostname, _options, callback) => callback(null, this.#address, 4) }, response => {
      res.writeHead(response.statusCode!, Object.fromEntries(Object.entries(response.headers).filter(([key]) => !hop.has(key))));
      response.on("end", () => settle(response.statusCode!, null));
      response.on("error", () => { settle(response.statusCode!, "upstream_response_error"); res.destroy(); });
      response.pipe(res);
    }); } catch {
      settle(null, "upstream_request_invalid"); req.resume(); res.writeHead(502).end(); return;
    }
    upstream.setTimeout(300_000, () => { settle(null, "upstream_timeout"); upstream!.destroy(); res.destroy(); });
    upstream.on("error", () => { settle(null, "upstream_error"); if (!res.headersSent) res.writeHead(502); res.end(); });
    res.on("close", () => { if (!finished) { settle(null, "client_closed"); upstream?.destroy(); } });
    req.pipe(upstream);
  }
  async close() {
    if (this.#closed) return;
    this.#closed = true;
    for (const cancel of [...this.#active]) cancel();
    for (const socket of this.#sockets) socket.destroy();
    await new Promise<void>(resolve => this.#server.close(() => resolve()));
    fsyncSync(this.#fd); closeSync(this.#fd);
  }
}
