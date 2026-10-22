// Test-only Electron entry: opens the workbench window from a build's main.mjs with a DevTools port, so tests/cdp.mjs
// can drive it. CommonJS so the switch is set before Electron is ready. Usage: electron cdp_launch.cjs MAIN_MJS STATE USER_DATA PORT
const { app } = require('electron');
const { pathToFileURL } = require('node:url');
const [main, state, userData, port] = process.argv.slice(2);
app.commandLine.appendSwitch('remote-debugging-port', port);
import(pathToFileURL(main).href).then(({ run }) => run({ state, userData })).catch(error => { console.error(error); app.exit(1); });
