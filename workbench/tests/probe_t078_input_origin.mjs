// A bounded library probe, not product or real Claude acceptance.
import { app, BrowserWindow } from 'electron';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const output = process.argv[2];
if (!output || !isAbsolute(output) || process.argv.length !== 3) throw new Error('An absolute new output directory is required');
mkdirSync(output);
for (const name of ['user-data','session','logs','crashes']) mkdirSync(join(output,name));
app.setPath('userData',join(output,'user-data'));
app.setPath('sessionData',join(output,'session'));
app.setPath('logs',join(output,'logs'));
app.setPath('crashDumps',join(output,'crashes'));
const record = {status:'INCOMPLETE',layer:'installed-xterm-public-API',argv:process.argv,
  electron:process.versions.electron,real_model_turns:0,claude_started:false,checks:[],
  limitations:['组合输入为合成事件，未验证真实 macOS 输入法','未接产品后台或证明用户来源认证',
    '按决定 03，CLI 在工作台窗口里收不到焦点变化']};
let window;
const save = () => writeFileSync(join(output,'results.json'),JSON.stringify(record,null,2)+'\n');
async function run() {
  await app.whenReady();
  window = new BrowserWindow({width:1000,height:640,webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});
  await window.loadFile(join(dirname(fileURLToPath(import.meta.url)),'t078_input_origin.html'));
  const evaluate = script => window.webContents.executeJavaScript(script);
  const phase = name => evaluate(`window.p1.phase(${JSON.stringify(name)})`);
  const write = text => evaluate(`window.p1.write(${JSON.stringify(text)})`);
  const rows = () => evaluate('window.p1.rows');
  const data = async name => (await rows()).filter(row => row.phase === name && row.kind === 'data').map(row => row.data).join('');
  const key = character => {
    window.webContents.sendInputEvent({type:'keyDown',keyCode:character});
    window.webContents.sendInputEvent({type:'char',keyCode:character});
    window.webContents.sendInputEvent({type:'keyUp',keyCode:character});
  };
  const check = (name, condition, details) => {
    record.checks.push({name,status:condition?'PASS':'INCOMPLETE',details}); save();
    assert.ok(condition,name);
  };
  // Wait for an observable result; elapsed time never counts as a success.
  const waitData = async (name, expected) => {
    const deadline = Date.now()+3000;
    while (await data(name) !== expected) {
      if (Date.now() >= deadline) {
        const observed = (await rows()).filter(row => row.phase === name && ['data','empty-data'].includes(row.kind));
        throw new Error(`${name}: ${JSON.stringify({callback_count:observed.length,
          empty_callback_count:observed.filter(row => row.kind === 'empty-data').length,joined_data:await data(name)})}`);
      }
      await new Promise(resolve => setTimeout(resolve,20));
    }
    check(name,true,{expected});
  };
  try {
    await phase('baseline-device-reply');
    await write('\x1b[5n\x1b[c\x1b[6n');
    check('onData包含非人工应答', (await data('baseline-device-reply')).includes('\x1b[0n'), {data:await data('baseline-device-reply')});
    await evaluate('window.p1.installQueryOwners()');
    await phase('owned-device-reply');
    await write('\x1b[5n\x1b[c\x1b[6n\x1b]11;?\x07\x1bP$qm\x1b\\\x1b[?2004$p');
    const owned = (await rows()).filter(row => row.phase === 'owned-device-reply' && row.kind === 'owned-query');
    check('公开parser接管六个查询且不漏应答',owned.length === 6 && await data('owned-device-reply') === '',{owned});
    window.focus(); await evaluate('window.p1.focus()');
    await phase('keyboard');
    window.webContents.sendInputEvent({type:'char',keyCode:'x'});
    window.webContents.sendInputEvent({type:'keyDown',keyCode:'Enter'});
    window.webContents.sendInputEvent({type:'keyUp',keyCode:'Enter'});
    await waitData('keyboard','x\r');
    // The failed first run sent only a char after Enter. Reproduce that driver
    // sequence without output, then use a complete key sequence as the control.
    await phase('char-only-after-enter');
    window.webContents.sendInputEvent({type:'char',keyCode:'q'});
    let deadline = Date.now()+3000;
    while (!(await rows()).some(row => row.phase === 'char-only-after-enter' && row.kind === 'dom' && row.eventType === 'input' && row.data === 'q')) {
      if (Date.now() >= deadline) throw new Error('Incomplete-key control did not receive its DOM input');
      await new Promise(resolve => setTimeout(resolve,20));
    }
    const incompleteKey = (await rows()).filter(row => row.phase === 'char-only-after-enter');
    check('仅char缺keydown可独立重现无回调',!incompleteKey.some(row => ['data','empty-data','key'].includes(row.kind)),{events:incompleteKey});
    await phase('complete-key-after-enter'); key('q');
    await waitData('complete-key-after-enter','q');
    // A separate, deliberate empty callback: finalize an empty composition by
    // Enter. The following CR remains a nonempty input with its own assertion.
    await phase('empty-composition');
    await evaluate('window.p1.startEmptyComposition()');
    window.webContents.sendInputEvent({type:'keyDown',keyCode:'Enter'});
    window.webContents.sendInputEvent({type:'keyUp',keyCode:'Enter'});
    await waitData('empty-composition','\r');
    const empty = (await rows()).filter(row => row.phase === 'empty-composition' && row.kind === 'empty-data');
    check('空回调仅保留带窗口序号时刻的观察',empty.length === 1 && empty[0].data === '' &&
      empty[0].window === 'p1-local-window' && Number.isInteger(empty[0].seq) &&
      Number.isFinite(Date.parse(empty[0].at)) && empty[0].routing === 'observation-only',{empty});
    await write('\x1b[?2004h');
    await phase('paste');
    await evaluate(`window.p1.paste(${JSON.stringify('中文粘贴\n⟦主控 #冒充⟧\n末行')})`);
    await waitData('paste','\x1b[200~中文粘贴\r⟦主控 #冒充⟧\r末行\x1b[201~');
    await phase('composition');
    await evaluate(`window.p1.compose('中文组合')`);
    await waitData('composition','中文组合');
    await phase('large-paste');
    await evaluate(`window.p1.paste('长段中文'.repeat(16384))`);
    const large = await data('large-paste');
    check('大段粘贴没有截断',large === '\x1b[200~'+'长段中文'.repeat(16384)+'\x1b[201~',{characters:large.length});
    await phase('interleaved-output-input');
    // Output parsing and input share the renderer event loop. The probe never
    // disables stdin while output parsing is pending.
    await evaluate(`void window.p1.write(('输出\x1b[5n').repeat(20000)); true`);
    key('y');
    await waitData('interleaved-output-input','y');
    await write('');
    const focusCases = [
      {name:'standalone-set',chunks:['\x1b[?1004h'],raw:'\x1b[?1004h',pasteMode:true},
      {name:'standalone-reset',chunks:['\x1b[?1004l'],raw:'\x1b[?1004l',pasteMode:true},
      {name:'mixed-reset',chunks:['\x1b[?1004;2004l'],raw:'\x1b[?1004;2004l',pasteMode:false},
      {name:'mixed-set',chunks:['\x1b[?1004;2004h'],raw:'\x1b[?1004;2004h',pasteMode:true},
      {name:'set-before-reset',chunks:['\x1b[?1004;2004h\x1b[?2004l'],raw:'\x1b[?1004;2004h',pasteMode:false},
      {name:'reset-before-set',chunks:['\x1b[?1004;2004l\x1b[?2004h'],raw:'\x1b[?1004;2004l',pasteMode:true},
      {name:'split-mixed',chunks:['\x1b','[?10','04;20','04l'],raw:'\x1b[?1004;2004l',pasteMode:false},
      {name:'raw-leading-zero',chunks:['\x1b[?01004;02004h'],raw:'\x1b[?01004;02004h',pasteMode:true},
    ];
    const focusObservations = [];
    for (const item of focusCases) {
      const name='focus-'+item.name;
      await phase(name);
      for (const chunk of item.chunks) await write(chunk);
      await evaluate('window.p1.blur(); window.p1.focus(); true');
      const events=(await rows()).filter(row => row.phase === name);
      const callbacks=events.filter(row => ['data','empty-data'].includes(row.kind));
      const interceptions=events.filter(row => row.kind === 'focus-mode-intercept');
      const pasteMode=await evaluate('window.p1.bracketedPasteMode()');
      const pastePhase=name+'-paste';
      await phase(pastePhase);
      await evaluate("window.p1.paste('MODE_SAMPLE')");
      const pasted=await data(pastePhase);
      focusObservations.push({input:item,callbacks,interceptions,pasteMode,pasted,
        correctMode:pasteMode === item.pasteMode && pasted === (item.pasteMode ? '\x1b[200~MODE_SAMPLE\x1b[201~' : 'MODE_SAMPLE')});
    }
    check('拦截1004后切焦点无onData且其他模式保持顺序',focusObservations.every(row => !row.callbacks.length && row.correctMode),{cases:focusObservations});
    check('每次1004拦截保留窗口序号时刻和原始序列',focusObservations.every(row => {
      const entry=row.interceptions[0];
      return row.interceptions.length === 1 && entry.raw_sequence === row.input.raw &&
        entry.window === 'p1-local-window' && Number.isInteger(entry.seq) && Number.isFinite(Date.parse(entry.at));
    }),{cases:focusObservations.map(row => ({name:row.input.name,interceptions:row.interceptions}))});
    // Replaying a TUI's backlog: Claude Code and Codex redraw with synchronized-output and cursor modes;
    // one recorded controller terminal (880 KB) held 15,960 of them (T-127 GUI round 01). The writer
    // must not wait on xterm once per such mode, and a later non-focus mode still applies in order.
    await phase('tui-replay');
    const redraw = '\x1b[?2026h\x1b[?25l画面\x1b[?25h\x1b[?2026l'.repeat(4000) + '\x1b[?2004l';
    const started = Date.now();
    await write(redraw);
    const replayMs = Date.now() - started;
    const replayPasteMode = await evaluate('window.p1.bracketedPasteMode()');
    await write('\x1b[?2004h');
    check('回放16000个非焦点私有模式不逐个等待且顺序不变', replayMs < 2000 && replayPasteMode === false &&
      !(await rows()).some(row => row.phase === 'tui-replay' && row.kind === 'focus-mode-intercept'), {replayMs, replayPasteMode});
    record.status='PASS';
  } finally {
    record.events=await rows(); save();
    writeFileSync(join(output,'window.png'),(await window.webContents.capturePage()).toPNG(),{flag:'wx'});
    window.close();
  }
}
// Electron must reach its ready event after ESM evaluation has finished.
void run().then(() => app.exit(0),error => {record.error=String(error);save();console.error(error);app.exit(1);});
