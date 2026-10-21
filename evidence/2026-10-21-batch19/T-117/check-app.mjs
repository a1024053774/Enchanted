// Launch an isolated real packaged app; no agent CLI or user data is used.
import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, openSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { CDP, sleep, until } from './check-branding.mjs';

const app = resolve(process.argv[2]), out = resolve(process.argv[3]);
mkdirSync(out);
const state = join(out, 'state'), ui = join(out, 'ui');
const executable = join(app, 'Contents/MacOS/Enchanted');
const resources = join(app, 'Contents/Resources/app');
const log = join(out, 'app.log');
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !key.startsWith('A2A_') && !key.startsWith('GIT_CONFIG_') && !key.startsWith('ELECTRON_') &&
  !['NODE_OPTIONS', 'NODE_PATH'].includes(key)));
const argv = [executable, '--inspect-brk=0', '--remote-debugging-port=0', '--state', state, '--user-data', ui];
const child = spawn(argv[0], argv.slice(1), { env, detached: true, stdio: ['ignore', openSync(log, 'wx'), openSync(join(out, 'stderr.log'), 'wx')] });
const report = { status: 'INCOMPLETE', app, argv, fixture: out, model_calls: 0, checks: [] };
let main, page, electron;
function call(command) {
  const { credential } = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8'));
  return JSON.parse(execFileSync(executable, [join(resources, 'src/gates/cli.ts'), '--state', state, command],
    { env: { ...env, ELECTRON_RUN_AS_NODE: '1', A2A_OPERATOR_CREDENTIAL: credential }, encoding: 'utf8' }));
}
try {
  const logs = () => readFileSync(log, 'utf8') + readFileSync(join(out, 'stderr.log'), 'utf8');
  const endpoint = await until(() => /Debugger listening on (ws:\/\/127\.0\.0\.1:\d+\/[^\s]+)/.exec(logs())?.[1], 'Main-process inspector unavailable');
  main = await CDP.connect(endpoint);
  await main.send('Debugger.enable');
  await main.send('Runtime.runIfWaitingForDebugger');
  await until(() => main.paused, 'Initial debugger pause missing');
  const breakpoint = await main.send('Debugger.setBreakpointByUrl', { url: 'file://' + join(resources, 'desktop.mjs'), lineNumber: 11 });
  main.paused = null;
  await main.send('Debugger.resume');
  await until(() => main.paused, 'Desktop debugger pause missing');
  await main.evaluate(`process.argv = process.argv.filter(arg => !arg.startsWith('--inspect-brk')); true`);
  await main.send('Debugger.removeBreakpoint', { breakpointId: breakpoint.breakpointId });
  await main.send('Debugger.resume');
  const port = await until(() => {
    assert.equal(child.exitCode, null, logs());
    return /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//.exec(logs())?.[1];
  }, 'Renderer endpoint missing');
  const target = await until(async () => (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
    .find(t => t.type === 'page' && t.url.startsWith('file://' + resources)), 'Packaged renderer missing');
  page = await CDP.connect(target.webSocketDebuggerUrl);
  await until(() => page.evaluate('!!document.querySelector(".brand")'), 'Brand missing');
  const logo = await page.evaluate(`(async () => { const image = document.querySelector('.brand img'); if (!image) return null;
    await image.decode(); return { width: image.naturalWidth, data: Array.from(new Uint8Array(await (await fetch(image.src)).arrayBuffer())) }; })()`);
  assert.ok(logo?.width > 0, 'The actual packaged sidebar must display the supplied logo');
  assert.deepEqual(Buffer.from(logo.data), readFileSync(resolve('docs/assets/brand/logo-on-dark.png')), 'Sidebar logo must preserve original PNG bytes');
  report.checks.push('Packaged sidebar displays the supplied white PNG, byte for byte');
  await page.capture(join(out, 'sidebar.png'));
  electron = 'globalThis.__t117electron';
  await main.evaluate(`${electron} = process.getBuiltinModule('module').createRequire(process.resourcesPath + '/app/package.json')('electron');
    ${electron}.nativeTheme.themeSource = 'dark'; true`);
  await sleep(200);
  await main.evaluate(`
    globalThis.__t117icons = [];
    globalThis.__t117setIcon = ${electron}.app.dock.setIcon;
    ${electron}.app.dock.setIcon = function(image) {
      globalThis.__t117icons.push(image);
      return globalThis.__t117setIcon.call(this, image);
    }; true`);
  for (const theme of ['light', 'dark', 'light']) {
    await main.evaluate(`${electron}.nativeTheme.themeSource = ${JSON.stringify(theme)}; true`);
    const path = await until(() => main.evaluate(`globalThis.__t117icons.findLast(path => path.endsWith('logo-on-${theme}.png')) || null`), 'Native theme did not update Dock icon');
    assert.equal(path, join(resources, 'ui/brand', `logo-on-${theme}.png`));
    assert.deepEqual(readFileSync(path), readFileSync(resolve(`docs/assets/brand/logo-on-${theme}.png`)));
    report.checks.push({ nativeTheme: theme, dockIcon: path, passedThroughToNativeSetIcon: true });
    await main.evaluate('globalThis.__t117icons = []; true');
  }
  await main.evaluate(`${electron}.app.dock.setIcon = globalThis.__t117setIcon; ${electron}.nativeTheme.themeSource = 'system'; true`);
  report.bundle = JSON.parse(execFileSync('/usr/bin/plutil', ['-convert', 'json', '-o', '-', join(app, 'Contents/Info.plist')], { encoding: 'utf8' }));
  assert.equal(report.bundle.CFBundleShortVersionString, '0.1.1');
  assert.equal(report.bundle.CFBundleIdentifier, 'org.a2a.workbench');
  const icon = join(app, 'Contents/Resources', report.bundle.CFBundleIconFile);
  assert.ok(existsSync(icon) && readFileSync(icon).subarray(0, 4).toString() === 'icns');
  report.icon = icon;
  execFileSync('/usr/bin/codesign', ['--verify', '--deep', '--strict', app]);
  report.accepted = true;
} catch (error) {
  report.error = String(error);
} finally {
  try {
    if (main && electron) {
      await main.evaluate(`${electron}.app.dock.setIcon = globalThis.__t117setIcon; ${electron}.nativeTheme.themeSource = 'system'; true`);
      await main.evaluate(`setTimeout(() => ${electron}.app.quit(), 100); true`);
      main.ws.close();
    } else if (child.exitCode === null) { main?.ws.close(); child.kill('SIGTERM'); }
    page?.ws.close();
    await until(() => child.exitCode !== null || child.signalCode !== null, 'Isolated app did not exit');
    if (existsSync(join(state, 'desktop-connection.json'))) {
      report.daemon = call('daemon_status').pid;
      assert.ok(call('daemon_stop').ok);
      await until(() => !existsSync(join(state, 'daemon.pid')) && !existsSync(join(state, 'control.sock')), 'Isolated daemon did not stop');
    }
    report.cleanup = true;
  } catch (error) { report.cleanup_error = String(error); }
  report.status = report.accepted && report.cleanup ? 'PASS' : 'NO_GO';
  writeFileSync(join(out, 'result.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: report.status, checks: report.checks, error: report.error, cleanup_error: report.cleanup_error }));
}
process.exitCode = report.status === 'PASS' ? 0 : 1;
