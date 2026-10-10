// Evidence-only host: control sequences and native records, never screen text state.
const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const cp = require('node:child_process');
const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (!fs.existsSync('/Volumes/WD-Elements')) throw Error('External cache volume absent');
const pty = require(manifest.node_pty_path);
const out = manifest.output;
const now = () => new Date().toISOString();
function append(name, object) {
  const fd = fs.openSync(path.join(out, name), 'a');
  fs.writeSync(fd, JSON.stringify(object) + '\n');
  fs.fsyncSync(fd);
  fs.closeSync(fd);
}
const quote = s => "'" + s.replaceAll("'", "'\\''") + "'";
const command = manifest.codex_argv.map(quote).join(' ') + '; exec /bin/zsh -il';
const shellArgs = ['-il', '-c', command];
const child = pty.spawn('/bin/zsh', shellArgs, {
  name: 'xterm-256color', cols: 160, rows: 45,
  cwd: manifest.fixture, env: manifest.env, encoding: 'utf8'
});
let latestState = 'unknown';
let stateEvidence = null;
let sequence = 0;
let parser = 'text';
let control = '';
let escapeInOsc = false;
const rawFd = fs.openSync(path.join(out, 'pty.raw'), 'a');
function setState(value, evidence) {
  latestState = value;
  stateEvidence = evidence;
  append('states.jsonl', {received_at: now(), state: value, evidence});
}
function osc(value) {
  const received = now();
  append('terminal-controls.jsonl', {received_at: received, kind: 'OSC', value});
  if (value.startsWith('9;')) {
    // This launch enables exactly one notification type: approval-requested.
    setState('awaiting_approval', {source: 'OSC9', received_at: received,
      configured_notification_types: ['approval-requested'], value,
      certainty: 'inferred-from-structured-control-and-launch-config'});
  }
  if (value === '11;?') child.write('\x1b]11;rgb:0000/0000/0000\x1b\\');
}
function csi(value) {
  if (value === '6n') child.write('\x1b[1;1R');
  if (value === 'c' || value === '0c') child.write('\x1b[?1;2c');
  if (value === '>c' || value === '>0c') child.write('\x1b[>0;0;0c');
  if (value === '?u') child.write('\x1b[?0u');
  if (value === '?2004h' || value === '?2004l') {
    append('terminal-controls.jsonl', {received_at: now(), kind: 'CSI', value});
  }
}
child.onData(data => {
  fs.writeSync(rawFd, data);
  for (const ch of data) {
    if (parser === 'text') { if (ch === '\x1b') parser = 'escape'; }
    else if (parser === 'escape') {
      control = '';
      if (ch === ']') { parser = 'osc'; escapeInOsc = false; }
      else if (ch === '[') parser = 'csi';
      else parser = 'text';
    } else if (parser === 'osc') {
      if (ch === '\x07' || (escapeInOsc && ch === '\\')) {
        osc(control); parser = 'text'; escapeInOsc = false;
      } else if (ch === '\x1b') escapeInOsc = true;
      else { control += ch; escapeInOsc = false; }
    } else if (parser === 'csi') {
      control += ch;
      if (ch >= '@' && ch <= '~') { csi(control); parser = 'text'; }
    }
  }
});
child.onExit(event => append('process-events.jsonl', {received_at: now(), kind: 'pty-exit', ...event}));
append('process-events.jsonl', {received_at: now(), kind: 'launch', host_pid: process.pid,
  pty_pid: child.pid, shell: '/bin/zsh', shell_argv: shellArgs,
  codex_argv: manifest.codex_argv,
  process_table: cp.execFileSync('/bin/ps', ['-o', 'pid,ppid,pgid,command', '-p', String(process.pid), '-p', String(child.pid)], {encoding: 'utf8'})});
const offsets = new Map();
const lineNumbers = new Map();
function filesIn(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap(e => {
    const file = path.join(dir, e.name);
    return e.isDirectory() ? filesIn(file) : e.name.endsWith('.jsonl') ? [file] : [];
  });
}
function scan() {
  for (const file of filesIn(path.join(manifest.codex_home, 'sessions'))) {
    const bytes = fs.readFileSync(file);
    let offset = offsets.get(file) || 0;
    let end;
    while ((end = bytes.indexOf(10, offset)) >= 0) {
      const record = JSON.parse(bytes.subarray(offset, end).toString('utf8'));
      const line = (lineNumbers.get(file) || 0) + 1;
      lineNumbers.set(file, line);
      append('native-events.jsonl', {received_at: now(), file: path.relative(manifest.codex_home, file), line, record});
      if (record.type === 'event_msg') {
        if (record.payload.type === 'task_started') setState('running', {source: 'rollout', line, record});
        if (record.payload.type === 'task_complete' || record.payload.type === 'turn_aborted') setState('idle', {source: 'rollout', line, record});
      }
      offset = end + 1;
    }
    offsets.set(file, offset);
  }
}
const timer = setInterval(scan, 100);
const server = net.createServer(socket => {
  let input = '';
  socket.on('data', data => {
    input += data.toString('utf8');
    const newline = input.indexOf('\n');
    if (newline < 0) return;
    const request = JSON.parse(input.slice(0, newline));
    if (request.op === 'status') {
      scan();
      socket.end(JSON.stringify({state: latestState, evidence: stateEvidence,
        host_pid: process.pid, pty_pid: child.pid, sequence}) + '\n');
    } else if (request.op === 'inject') {
      scan();
      if (request.state !== latestState) {
        socket.end(JSON.stringify({error: 'State mismatch', actual: latestState}) + '\n');
        return;
      }
      const registered = {id: ++sequence, cli: 'codex', state: latestState,
        registered_text: request.text, registered_at: now(),
        state_evidence: stateEvidence, mode: request.mode || 'plain'};
      append('registrations.jsonl', registered);
      const bytes = request.mode === 'bracketed' ? '\x1b[200~' + request.text + '\x1b[201~\r' : request.text + '\r';
      append('writes.jsonl', {...registered, written_at: now(), bytes});
      child.write(bytes);
      socket.end(JSON.stringify(registered) + '\n');
    } else if (request.op === 'control') {
      append('writes.jsonl', {kind: 'harness-control', written_at: now(), bytes: request.bytes, reason: request.reason});
      child.write(request.bytes);
      socket.end('{"ok":true}\n');
    } else if (request.op === 'stop') {
      append('process-events.jsonl', {received_at: now(), kind: 'stop', reason: request.reason});
      scan();
      child.kill('SIGTERM');
      clearInterval(timer);
      socket.end('{"ok":true}\n');
      server.close(() => process.exit(0));
    } else socket.end('{"error":"Unknown operation"}\n');
  });
});
server.listen(manifest.socket, () => fs.writeFileSync(path.join(out, 'host-ready.json'), JSON.stringify({pid: process.pid, socket: manifest.socket})));
