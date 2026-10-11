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
const command = manifest.cli_argv.map(quote).join(' ') + '; exec /bin/zsh -il';
const shellArgs = ['-il', '-c', command];
const childEnv=manifest.cli === 'claude' ? {...process.env,...manifest.env} : manifest.env;
if (manifest.cli === 'claude') delete childEnv.CLAUDE_CONFIG_DIR;
const child = pty.spawn('/bin/zsh', shellArgs, {
  name: 'xterm-256color', cols: 160, rows: 45,
  cwd: manifest.fixture, env: childEnv, encoding: 'utf8'
});
let primarySessionId = manifest.native_session || null;
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
  if (manifest.cli === 'codex' && manifest.launch_mode === 'legacy-approval-osc' && value.startsWith('9;')) {
    // This launch enables exactly one notification type: approval-requested.
    setState('awaiting_approval', {source: 'OSC9', received_at: received,
      configured_notification_types: ['approval-requested'], value,
      certainty: 'inferred-from-structured-control-and-launch-config'});
  }
  if (value === '7501;?') child.write('\x1b]7501;?1\x1b\\');
  if (manifest.cli === 'claude' && value.startsWith('7501;state=')) {
    const fields = Object.fromEntries(value.slice(5).split(':').map(p => {const i=p.indexOf('='); return [p.slice(0,i),p.slice(i+1)];}));
    if (fields.state === 'working') setState('running', {source:'OSC7501', received_at:received, fields});
    if (fields.state === 'idle' || fields.state === 'done') setState('idle', {source:'OSC7501', received_at:received, fields});
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
  cli_argv: manifest.cli_argv,
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
  for (const file of manifest.cli === 'codex' ? filesIn(path.join(manifest.codex_home, 'sessions')) : (fs.existsSync(manifest.native_transcript) ? [manifest.native_transcript] : [])) {
    const bytes = fs.readFileSync(file);
    let offset = offsets.get(file) || 0;
    let end;
    while ((end = bytes.indexOf(10, offset)) >= 0) {
      const record = JSON.parse(bytes.subarray(offset, end).toString('utf8'));
      if (manifest.cli === 'codex' && record.type === 'session_meta' && record.payload.source === 'cli') {
        if (primarySessionId && primarySessionId !== record.payload.id) throw Error('Ambiguous primary session');
        primarySessionId=record.payload.id;
      }
      const line = (lineNumbers.get(file) || 0) + 1;
      lineNumbers.set(file, line);
      append('native-events.jsonl', {received_at: now(), file: manifest.cli === 'codex' ? path.relative(manifest.codex_home,file) : file, line, record});
      if (manifest.cli === 'codex' && record.type === 'event_msg') {
        if (record.payload.type === 'task_started') setState('running', {source: 'rollout', line, record});
        if (record.payload.type === 'task_complete' || record.payload.type === 'turn_aborted') setState('idle', {source: 'rollout', line, record});
      }
      if (manifest.cli === 'claude' && record.type === 'assistant' && record.message?.stop_reason === 'end_turn') setState('idle',{source:'native-stop-reason',line,record});
      offset = end + 1;
    }
    offsets.set(file, offset);
  }
}

function hookEvents() {
  const file=path.join(out,'turn-hooks.jsonl');
  if (!fs.existsSync(file)) return [];
  const bytes=fs.readFileSync(file); const last=bytes.lastIndexOf(10);
  if (last<0) return [];
  return bytes.subarray(0,last).toString('utf8').split('\n').filter(Boolean).map(JSON.parse);
}
function gate() {
  scan();
  const all=hookEvents().filter(e=>e.payload.session_id===primarySessionId);
  const turns=all.filter(e=>['UserPromptSubmit','Stop'].includes(e.payload.hook_event_name));
  const last=turns.at(-1)||null;
  return {checked_at:now(), primary_session_id:primarySessionId,
    allowed:!!last && last.payload.hook_event_name==='Stop',last_event:last,
    event_count:turns.length, permission_events:all.filter(e=>e.payload.hook_event_name==='PermissionRequest')};
}
const items=new Map();const queue=[];let sending=false;
function register(request) {
  const id=++sequence;
  const item={id,cli:manifest.cli,ready_rev:3,state:request.state,launch_mode:manifest.launch_mode,
    registered_text:request.text,registered_at:now(),method:'M3',experiment:request.experiment,
    race_role:request.race_role||null,race_case:request.race_case||null,
    diagnostic_running:request.diagnostic_running===true,written:false,phase:'registered',
    gate_attempt:gate(),gate_last_event:null,queued_at:null,queued_seconds:0};
  append('registrations.jsonl',item);items.set(id,item);return item;
}
async function writeItem(item,g) {
  sending=true;item.phase='writing';item.gate_last_event=g.last_event;item.gate_checked_at=g.checked_at;
  item.queued_seconds=item.queued_at ? (Date.now()-Date.parse(item.queued_at))/1000 : 0;
  item.first_written_at=now();item.written=true;
  const bytes='\x1b[200~'+item.registered_text+'\x1b[201~';
  append('writes.jsonl',{id:item.id,part:1,written_at:item.first_written_at,bytes,gate_snapshot:g});
  child.write(bytes);
  await new Promise(resolve=>setTimeout(resolve,300));
  item.submitted_at=now();item.gate_at_submit=gate();
  append('writes.jsonl',{id:item.id,part:2,written_at:item.submitted_at,bytes:'\r',gate_snapshot:item.gate_at_submit});
  child.write('\r');item.phase='submitted';sending=false;
  append('send-results.jsonl',item);
}
async function submit(item) {
  const g=gate();
  if(item.diagnostic_running) {
    if(manifest.cli!=='claude'||g.last_event?.payload.hook_event_name!=='UserPromptSubmit') throw Error('Running diagnostic lacks a start event');
    if(sending) throw Error('Overlapping running diagnostic');
    await writeItem(item,g);return;
  }
  if(g.allowed && !sending) {await writeItem(item,g);return;}
  item.phase='queued';item.queued_at=now();queue.push(item);
  append('queue-events.jsonl',{at:now(),kind:'queued',id:item.id,gate_snapshot:g});
}
const timer=setInterval(()=>{
  scan();
  if(!sending && queue.length) {
    const g=gate();if(g.allowed) {
      const item=queue.shift();append('queue-events.jsonl',{at:now(),kind:'released',id:item.id,gate_snapshot:g});
      writeItem(item,g).catch(error=>{append('host-errors.jsonl',{at:now(),error:String(error)});process.exit(1);});
    }
  }
},100);
const server=net.createServer(socket=>{
  let input='';let handled=false;
  socket.on('data',async data=>{
    input+=data.toString('utf8');const end=input.indexOf('\n');
    if(end<0||handled)return;handled=true;
    const request=JSON.parse(input.slice(0,end));
    if(request.op==='status') {
      const g=gate();socket.end(JSON.stringify({state:g.allowed?'idle':g.last_event?'running':'unknown',gate:g,native_state:latestState,native_evidence:stateEvidence,sequence,host_pid:process.pid,pty_pid:child.pid})+'\n');
    } else if(request.op==='submit') {
      const item=register(request);await submit(item);socket.end(JSON.stringify(item)+'\n');
    } else if(request.op==='item') {
      socket.end(JSON.stringify(items.get(request.id)||{error:'Unknown item'})+'\n');
    } else if(request.op==='race-gap') {
      const a=register(request.a);if(!gate().allowed)throw Error('Race A was not idle');
      await submit(a);
      // Same event-loop continuation: A has been submitted, then B reads the file afresh.
      const b=register(request.b);await submit(b);
      const result={at:now(),a_id:a.id,b_id:b.id,a_submitted_at:a.submitted_at,b_first_written_at:b.first_written_at||null,b_phase:b.phase,b_gate_at_attempt:b.gate_attempt};
      append('race-gap-attempts.jsonl',result);socket.end(JSON.stringify(result)+'\n');
    } else if(request.op==='control') {
      append('writes.jsonl',{kind:'harness-control',written_at:now(),bytes:request.bytes,reason:request.reason});child.write(request.bytes);socket.end('{"ok":true}\n');
    } else if(request.op==='stop') {
      append('process-events.jsonl',{received_at:now(),kind:'stop',reason:request.reason,pending_queue:queue.map(x=>x.id)});
      scan();child.kill('SIGTERM');clearInterval(timer);socket.end('{"ok":true}\n');server.close(()=>process.exit(0));
    } else socket.end('{"error":"Unknown operation"}\n');
  });
});
server.listen(manifest.socket,()=>fs.writeFileSync(path.join(out,'host-ready.json'),JSON.stringify({pid:process.pid,socket:manifest.socket})));
