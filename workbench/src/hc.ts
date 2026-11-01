import { createConnection, type Socket } from 'node:net';
import { EventEmitter } from 'node:events';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { hcBinary, hcRelease } from './hcDistribution.mjs';

const exec = promisify(execFile);
const DATA = 0, CREDIT = 1, CLOSE = 2, RESIZE = 3;
type TerminalRecord = { address: string; pid: number; state: string; screen: string; cols: number; rows: number;
  labels: Record<string, string>; exit_code?: number; reason?: string };

// The released 0.1.15 wire protocol: 9-byte LE header, channel 0 JSON-RPC.
class HcConnection {
  private socket: Socket;
  private buffer = Buffer.alloc(0);
  private framed = false;
  private sequence = 0;
  private pending = new Map<number, { resolve: (result: any) => void; reject: (error: Error) => void;
    accept?: (result: any) => void; timer: ReturnType<typeof setTimeout> }>();
  readonly streams = new Map<number, HcTerminal>();
  private failure: Error | null = null;
  constructor(path: string) {
    this.socket = createConnection(path);
    this.socket.on('data', bytes => {
      try { this.receive(bytes); }
      catch (error) { this.socket.destroy(error as Error); }
    });
    this.socket.on('error', error => this.fail(error));
    this.socket.on('close', () => this.fail(new Error('hc connection closed; terminal survival unknown')));
  }
  private fail(error: Error) {
    if (this.failure) return;
    this.failure = error;
    for (const call of this.pending.values()) { clearTimeout(call.timer); call.reject(error); }
    this.pending.clear();
    for (const terminal of new Set(this.streams.values())) terminal.emit('lost', error);
    this.streams.clear();
  }
  private reply(bytes: Buffer) {
    const reply = JSON.parse(bytes.toString('utf8'));
    const call = this.pending.get(reply.id);
    if (!call) throw new Error('unexpected hc RPC reply');
    clearTimeout(call.timer); this.pending.delete(reply.id);
    if (reply.error) call.reject(Object.assign(new Error(reply.error.message), { hc: reply.error }));
    else {
      try { call.accept?.(reply.result); }
      catch (error) {
        // This call has left pending: reject it before a callback bug fails the
        // connection, otherwise fail() cannot settle its caller's write queue.
        call.reject(error as Error); throw error;
      }
      call.resolve(reply.result);
    }
  }
  private receive(bytes: Buffer) {
    this.buffer = Buffer.concat([this.buffer, bytes]);
    if (!this.framed) {
      const end = this.buffer.indexOf(10);
      if (end < 0) return;
      const line = this.buffer.subarray(0, end);
      this.buffer = this.buffer.subarray(end + 1);
      const reply = JSON.parse(line.toString('utf8'));
      if (reply.result?.framed !== true) throw new Error('hc refused framed hello');
      this.framed = true;
      this.reply(line);
    }
    while (this.buffer.length >= 9) {
      const channel = this.buffer.readUInt32LE(0), kind = this.buffer[4]!, length = this.buffer.readUInt32LE(5);
      if (length > 16 * 1024 * 1024) throw new Error('hc frame exceeds released protocol limit');
      if (this.buffer.length < 9 + length) return;
      const payload = this.buffer.subarray(9, 9 + length);
      this.buffer = this.buffer.subarray(9 + length);
      if (channel === 0 && kind === DATA) this.reply(payload);
      else {
        const terminal = this.streams.get(channel);
        if (!terminal) throw new Error('hc frame for unregistered attach channel');
        if (kind === DATA) {
          // Credit only after the synchronous trace consumer has accepted the bytes.
          terminal.data(channel, payload);
          const credit = Buffer.alloc(4); credit.writeUInt32LE(length);
          this.send(channel, CREDIT, credit);
        } else if (kind === CLOSE) {
          this.streams.delete(channel);
          terminal.closed(channel, payload);
        } else throw new Error(`unexpected hc stream frame ${kind}`);
      }
    }
  }
  send(channel: number, kind: number, payload: Buffer) {
    if (this.failure || this.socket.destroyed) throw this.failure ?? new Error('hc disconnected');
    const header = Buffer.alloc(9);
    header.writeUInt32LE(channel); header[4] = kind; header.writeUInt32LE(payload.length, 5);
    this.socket.write(Buffer.concat([header, payload]));
  }
  call(method: string, params: Record<string, unknown> = {}, accept?: (result: any) => void): Promise<any> {
    if (this.failure) return Promise.reject(this.failure);
    return new Promise((resolve, reject) => {
      const id = ++this.sequence;
      const timer = setTimeout(() => {
        this.socket.destroy(new Error(`hc ${method} deadline; outcome unknown`));
      }, 15_000);
      this.pending.set(id, { resolve, reject, accept, timer });
      const body = Buffer.from(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
      if (method === 'hello') this.socket.write(Buffer.concat([body, Buffer.from('\n')]));
      else this.send(0, DATA, body);
    });
  }
  close() {
    // A viewer detaches; it must not kill the program or stop the core.
    for (const terminal of new Set(this.streams.values())) terminal.emit('detach');
    this.streams.clear();
    this.socket.destroy();
  }
}

export class HcTerminal extends EventEmitter {
  readonly pid: number;
  readonly address: string;
  readonly screen: string;
  cols: number; rows: number;
  private channel = 0;
  private connection: HcConnection;
  constructor(connection: HcConnection, record: TerminalRecord) {
    super(); this.connection = connection;
    this.pid = record.pid; this.address = record.address; this.screen = record.screen;
    this.cols = record.cols; this.rows = record.rows;
  }
  async attach() {
    await this.connection.call('terminal.attach', { terminal: this.address, cols: this.cols, rows: this.rows,
      history: 1_000_000 }, result => {
      const previous = this.channel;
      this.channel = result.channel;
      this.connection.streams.set(this.channel, this);
      // The reply precedes this channel's first paint. Keep the old channel registered
      // until its CLOSE acknowledgement, but consume none of its now-stale output.
      this.emit('paint');
      if (previous) this.connection.send(previous, CLOSE, Buffer.alloc(0));
    });
  }
  data(channel: number, bytes: Buffer) { if (channel === this.channel) this.emit('data', bytes); }
  closed(channel: number, bytes: Buffer) {
    if (channel === this.channel) this.emit('exit', bytes.length ? JSON.parse(bytes.toString('utf8')) : {});
  }
  write(bytes: string | Buffer) { this.connection.send(this.channel, DATA, Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes)); }
  async resize(cols: number, rows: number) {
    const size = Buffer.alloc(4); size.writeUInt16LE(cols); size.writeUInt16LE(rows, 2);
    this.connection.send(this.channel, RESIZE, size); this.cols = cols; this.rows = rows;
    // 0.1.15 RESIZE changes the screen but sends no paint. Attach applies these
    // dimensions before taking the full paint, with live bytes ordered after it.
    await this.attach();
  }
  // 0.1.15 correlates wait with this send (caller), rather than with an arbitrary later working report.
  send(params: { terminal: string; text: string; caller: string; wait: true; timeout: number; if?: "idle" }) {
    return this.connection.call('terminal.send', params);
  }
  async kill() { await this.connection.call('terminal.kill', { terminal: this.address }); }
}

export class HcRuntime {
  readonly root: string;
  readonly session: string;
  readonly socket: string;
  readonly environment: NodeJS.ProcessEnv;
  private connection?: HcConnection;
  private starting?: Promise<void>;
  constructor(root: string, environment: NodeJS.ProcessEnv) {
    this.root = root;
    const manifest = join(root, 'hc-runtime.json');
    let identity: { session: string; socket: string };
    if (existsSync(manifest)) identity = JSON.parse(readFileSync(manifest, 'utf8'));
    else {
      const directory = mkdtempSync('/private/tmp/enchanted-hc-');
      identity = { session: 'enchanted-' + randomUUID(), socket: join(directory, 'core.sock') };
      writeFileSync(manifest, JSON.stringify(identity) + '\n', { mode: 0o600, flag: 'wx' });
    }
    if (!/^enchanted-[0-9a-f-]{36}$/.test(identity.session)) throw new Error('invalid private HC_SESSION');
    // paths.rs: core.holder.<8 hex>.sock is the longest endpoint (103 bytes).
    const holder = identity.socket.replace(/\.[^/.]*$/, '.holder.sock');
    if (Math.max(Buffer.byteLength(identity.socket), Buffer.byteLength(holder) + 9) > 103)
      throw new Error('private hc socket path including holder suffix exceeds 103 bytes');
    this.session = identity.session; this.socket = identity.socket;
    this.environment = { ...environment, HC_SESSION: this.session, HC_SOCKET: this.socket,
      XDG_STATE_HOME: join(root, 'hc', 'state'), XDG_CONFIG_HOME: join(root, 'hc', 'config') };
    mkdirSync(this.environment.XDG_CONFIG_HOME!, { recursive: true, mode: 0o700 });
  }
  async start() {
    this.starting ??= (async () => {
      const binary = await hcBinary(this.root);
      await exec(binary, ['--json', 'server', 'start'], { env: this.environment, timeout: 15_000 });
      // T-228: the checks below are about the core this connection reached, asked over the connection itself; a
      // core checked first and connected to after could have died and been replaced in between. If the connected
      // core dies later, the connection drops and the panes record hc_connection_lost.
      const connection = new HcConnection(this.socket);
      try {
        await connection.call('hello', { framed: true });
        const status = await connection.call('server.status');
        if (status.version !== hcRelease.version) throw new Error('private hc version differs from packaged pin');
        const observed = await exec('/bin/ps', ['-p', String(status.pid), '-o', 'pgid='], { timeout: 5000 });
        const caller = await exec('/bin/ps', ['-p', String(process.pid), '-o', 'pgid='], { timeout: 5000 });
        if (Number(observed.stdout.trim()) === Number(caller.stdout.trim())) throw new Error('private hc core did not detach');
        // The core is ours when it holds this session's private core.lock open. The holder respawns a dead core as
        // its own child with our environment, so the parent is not 1; a core another client started with the
        // session and socket but the default XDG directory holds a different lock. lsof is the outside view of
        // which state directory a running core uses. The lock goes to lsof as a name, so it matches by file
        // identity: the names lsof prints are escaped (non-ASCII bytes under the C locale) and cannot be compared
        // as text. lsof exits 1 with no output when the process does not have it open; any failure refuses the core.
        const lock = join(this.environment.XDG_STATE_HOME!, 'herdr-core', this.session, 'core.lock');
        let held = '', lsofError = '';
        try { held = (await exec('/usr/sbin/lsof', ['-a', '-p', String(status.pid), '-Fp', '--', lock], { timeout: 5000 })).stdout; }
        catch (error) { lsofError = String((error as { stderr?: string }).stderr ?? error).trim(); }
        if (!held.split('\n').includes('p' + status.pid))
          throw new Error(`hc core ${status.pid} does not hold this session's ${lock}${lsofError ? ` (lsof: ${lsofError})` : ''}; refusing it`);
      } catch (error) { connection.close(); throw error; }
      this.connection = connection;
    })();
    return this.starting;
  }
  async run(launch: string, argv: string[], cwd: string, env: Record<string, string>) {
    await this.start();
    const result = await this.connection!.call('terminal.run', { argv, cwd, env,
      labels: { enchanted_launch: launch }, no_notify: true });
    return new HcTerminal(this.connection!, { ...result, cols: 160, rows: 45 });
  }
  async find(launch: string, address: string) {
    await this.start();
    const result = await this.connection!.call('terminal.list');
    const record: TerminalRecord | undefined = result.terminals.find((terminal: TerminalRecord) =>
      terminal.address === address && terminal.labels.enchanted_launch === launch);
    if (!record) throw new Error('recorded hc terminal identity missing');
    return record.state === 'live' ? new HcTerminal(this.connection!, record) : null;
  }
  detach() { this.connection?.close(); }
}
