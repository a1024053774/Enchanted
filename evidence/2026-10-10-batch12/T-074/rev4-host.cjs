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
  if (value === '7501;?') rawWrite('\x1b]7501;?1\x1b\\','inject',{kind:'terminal_protocol'});
  if (manifest.cli === 'claude' && value.startsWith('7501;state=')) {
    const fields = Object.fromEntries(value.slice(5).split(':').map(p => {const i=p.indexOf('='); return [p.slice(0,i),p.slice(i+1)];}));
    if (fields.state === 'working') setState('running', {source:'OSC7501', received_at:received, fields});
    if (fields.state === 'idle' || fields.state === 'done') setState('idle', {source:'OSC7501', received_at:received, fields});
  }
  if (value === '11;?') rawWrite('\x1b]11;rgb:0000/0000/0000\x1b\\','inject',{kind:'terminal_protocol'});
}
function csi(value) {
  if (value === '6n') rawWrite('\x1b[1;1R','inject',{kind:'terminal_protocol'});
  if (value === 'c' || value === '0c') rawWrite('\x1b[?1;2c','inject',{kind:'terminal_protocol'});
  if (value === '>c' || value === '>0c') rawWrite('\x1b[>0;0;0c','inject',{kind:'terminal_protocol'});
  if (value === '?u') rawWrite('\x1b[?0u','inject',{kind:'terminal_protocol'});
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

let gateState='idle';let busyAt=null;let sending=false;let halt=null;let hookCursor=0;
const submissions=[];const items=new Map();const queue=[];
function snapshot() {return {gate_state:gateState,busy_at:busyAt,pending_queue:queue.map(x=>x.id),halt};}
function fail(reason,details) {
  halt={at:now(),reason,details};append('violations.jsonl',halt);
}
function rawWrite(bytes,source,meta={}) {
  const writtenAt=now();
  child.write(bytes);
  if(meta.submit) {
    gateState='busy';busyAt=writtenAt;
    const submission={submission_id:submissions.length+1,item_id:meta.id||null,source,
      busy_at:busyAt,stop:null,released_at:null};
    submissions.push(submission);
    append('gate-events.jsonl',{at:now(),kind:'busy',...submission});
    if(meta.id)items.get(meta.id).submission_id=submission.submission_id;
  }
  append('writes.jsonl',{written_at:writtenAt,bytes,source,...meta,gate_state_after:gateState,busy_at:busyAt});
}
function readHooks() {
  scan();
  const file=path.join(out,'turn-hooks.jsonl');if(!fs.existsSync(file))return;
  const bytes=fs.readFileSync(file);const end=bytes.lastIndexOf(10);if(end<0)return;
  const all=bytes.subarray(0,end).toString('utf8').split('\n').filter(Boolean).map(JSON.parse);
  for(;hookCursor<all.length;hookCursor++) {
    const event=all[hookCursor];if(event.payload.session_id!==primarySessionId)continue;
    append('hook-observations.jsonl',{at:now(),event});
    if(event.payload.hook_event_name!=='Stop')continue;
    const eligible=submissions.filter(s=>!s.stop&&!s.released_at&&Date.parse(s.busy_at)<Date.parse(event.received_at));
    if(eligible.length!==1) {fail('Stop has no unique preceding submission',{event,eligible});continue;}
    const submission=eligible[0];submission.stop=event;
    append('gate-events.jsonl',{at:now(),kind:'stop-matched',submission_id:submission.submission_id,item_id:submission.item_id,event});
    if(Date.parse(event.received_at)>Date.parse(busyAt)) {
      gateState='idle';append('gate-events.jsonl',{at:now(),kind:'idle',reason:'newer-Stop',submission_id:submission.submission_id,event});
    }
  }
}
function register(request) {
  if(!['inject','user_sim'].includes(request.source))throw Error('Unknown source');
  const item={id:++sequence,cli:manifest.cli,ready_rev:4,source:request.source,state:request.state,
    launch_mode:manifest.launch_mode,registered_text:request.text,registered_at:now(),method:'M3',
    case_id:request.case_id||null,role:request.role||null,gate_state:gateState,gate_at_registration:snapshot(),
    phase:'registered',written:false,queued_at:null,queued_ms:0,release_action:null};
  append('registrations.jsonl',item);items.set(item.id,item);return item;
}
async function writeItem(item,releaseAction=null) {
  if(halt)throw Error('Probe halted');
  if(item.source==='inject'&&gateState!=='idle'&&!releaseAction) {
    fail('Injection write while busy without release',{item,gate:snapshot()});throw Error('Busy write rejected');
  }
  if(sending)throw Error('Concurrent transport write');
  sending=true;item.phase='writing';item.gate_state=gateState;item.release_action=releaseAction;
  item.first_written_at=now();item.written=true;
  item.queued_ms=item.queued_at ? Date.parse(item.first_written_at)-Date.parse(item.queued_at):0;
  rawWrite('\x1b[200~'+item.registered_text+'\x1b[201~',item.source,{kind:'message',id:item.id,part:1,release_action:releaseAction,gate_state:gateState});
  await new Promise(resolve=>setTimeout(resolve,300));
  item.submitted_at=now();
  rawWrite('\r',item.source,{kind:'message',id:item.id,part:2,submit:true,release_action:releaseAction});
  item.phase='submitted';sending=false;append('send-results.jsonl',item);
}
async function submit(item) {
  if(halt)throw Error('Probe halted');
  if(item.source==='user_sim'||(gateState==='idle'&&!sending)) {await writeItem(item);return;}
  item.phase='queued';item.queued_at=now();queue.push(item);
  append('queue-events.jsonl',{at:now(),kind:'queued',id:item.id,...snapshot()});
}
async function release(reason) {
  if(halt)throw Error('Probe halted');
  if(sending)throw Error('Release while transport active');
  const action={at:now(),source:'release',record_type:'user_input',shape:'action',simulated_by_probe:true,reason,
    gate_before:snapshot(),queued_id:queue[0]?.id||null};
  append('user-actions.jsonl',action);
  // Explicit manual release retires the interrupted submission; no state is inferred from Esc.
  for(const s of submissions)if(!s.stop&&!s.released_at)s.released_at=action.at;
  if(queue.length) {
    const item=queue.shift();append('queue-events.jsonl',{at:now(),kind:'manual-release',id:item.id,action});
    await writeItem(item,action.at);
  } else {
    // Startup trust confirmation has no conversation Stop. This is the same explicit user release.
    gateState='idle';append('gate-events.jsonl',{at:now(),kind:'idle',reason:'manual-release-without-queue',action});
  }
  return action;
}
const timer=setInterval(()=>{
  readHooks();
  if(!halt&&!sending&&queue.length&&gateState==='idle') {
    const item=queue.shift();append('queue-events.jsonl',{at:now(),kind:'stop-release',id:item.id,...snapshot()});
    writeItem(item).catch(error=>fail('Queue send error',{error:String(error)}));
  }
},25);
const server=net.createServer(socket=>{
  let input='';let handled=false;
  socket.on('data',async data=>{
    input+=data.toString('utf8');const end=input.indexOf('\n');if(end<0||handled)return;handled=true;
    const request=JSON.parse(input.slice(0,end));
    try {
      readHooks();let result;
      if(request.op==='status')result={...snapshot(),submissions,primary_session_id:primarySessionId,sequence,host_pid:process.pid,pty_pid:child.pid};
      else if(request.op==='submit') {const item=register(request);await submit(item);result=item;}
      else if(request.op==='item')result=items.get(request.id);
      else if(request.op==='pair') {
        if(gateState!=='idle'||halt)throw Error('Pair A requires idle');
        const a=register(request.a);await submit(a);
        const b=register(request.b);await submit(b);
        result={at:now(),a_id:a.id,b_id:b.id,a_submitted_at:a.submitted_at,b_phase:b.phase,gate:snapshot()};
        append('pair-attempts.jsonl',result);
      } else if(request.op==='control') {
        if(request.source!=='user_sim')throw Error('Controls require user_sim source');
        rawWrite(request.bytes,'user_sim',{kind:'control',reason:request.reason,submit:request.bytes==='\r'});result={ok:true,...snapshot()};
      } else if(request.op==='release')result=await release(request.reason);
      else if(request.op==='stop') {
        append('process-events.jsonl',{received_at:now(),kind:'stop',reason:request.reason,...snapshot()});
        scan();child.kill('SIGTERM');clearInterval(timer);socket.end('{"ok":true}\n');server.close(()=>process.exit(0));return;
      } else throw Error('Unknown operation');
      socket.end(JSON.stringify(result)+'\n');
    } catch(error) {
      fail('Control error',{request,error:String(error)});socket.end(JSON.stringify({error:String(error),halt})+'\n');
    }
  });
});
server.listen(manifest.socket,()=>fs.writeFileSync(path.join(out,'host-ready.json'),JSON.stringify({pid:process.pid,socket:manifest.socket})));
