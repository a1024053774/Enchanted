#!/bin/bash
# 主控运行：只探测已安装在内置盘上的 Electron Node runtime，不启动 GUI／模型。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
python3 - "$@" <<'PY'
import datetime, json, os, pathlib, subprocess, sys, tempfile

repo = pathlib.Path.cwd()
electron = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron')
assert electron.is_absolute() and electron.is_file() and os.access(electron, os.X_OK)
assert not str(electron.resolve()).startswith('/Volumes/'), '不能运行外置盘 Electron'
label = datetime.datetime.now(datetime.timezone.utc).strftime('runtime-%Y%m%dT%H%M%S.%fZ')
out = repo / 'evidence/2026-10-19-batch17/T-102' / (label + '.json')
with tempfile.TemporaryDirectory(prefix='a2at102-runtime-', dir='/private/tmp') as tmp:
    module = pathlib.Path(tmp) / 'probe.ts'
    module.write_text('''import { DatabaseSync } from 'node:sqlite';
import { OrchestrationStore } from STORE;
const db = new DatabaseSync(':memory:');
db.exec("CREATE TABLE facts(value TEXT); INSERT INTO facts VALUES ('t102-sqlite-ok')");
if (db.prepare('SELECT value FROM facts').get()!.value !== 't102-sqlite-ok') throw new Error('sqlite readback mismatch');
db.close();
const store = new OrchestrationStore(process.argv[2]);
store.event('t102_runtime_probe', {value: 't102-store-ok'});
if (store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE type='t102_runtime_probe'").get()!.n !== 1) throw new Error('store readback mismatch');
store.db.close();
console.log(JSON.stringify({ok:true, electron:process.versions.electron, node:process.version, modules:process.versions.modules, sqlite:process.versions.sqlite, typescript:'actual store.ts imported'}));
'''.replace('STORE', json.dumps((repo/'workbench/src/store.ts').as_uri())), encoding='utf-8')
    env = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_')) and k not in ('NODE_OPTIONS','NODE_PATH')}
    env['ELECTRON_RUN_AS_NODE'] = '1'
    argv = [str(electron), str(module), tmp]
    result = {'task':'T-102','attempt':'a2','head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(), 'argv':argv, 'status':'INCOMPLETE'}
    try:
        p = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=30, start_new_session=True)
        result.update(exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
        if p.returncode == 0:
            facts = json.loads(p.stdout)
            assert facts['ok'] and facts['electron'] == '43.4.1' and facts['node'].startswith('v24.')
            result.update(status='PASS', facts=facts)
    except Exception as error:
        result['error'] = str(error)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status']=='PASS' else 1)
PY
