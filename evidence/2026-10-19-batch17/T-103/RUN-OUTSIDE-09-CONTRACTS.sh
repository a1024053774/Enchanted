#!/bin/bash
set -euo pipefail
# 执行主控 #16 已授权：四组合同通过后，调用 03 一并提交，不 push。
cd /Users/luckye/Documents/Code/a2a-wt-t103
/usr/bin/python3 -B - <<'PY'
import datetime, json, os, shutil, subprocess, sys, traceback
from pathlib import Path

source = Path.cwd()
evidence = source / 'evidence/2026-10-19-batch17/T-103'
disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载，停止验证'
accepted_path = evidence / 'run-20261019T063741Z-summary.json'
accepted = json.loads(accepted_path.read_text(encoding='utf-8'))
assert accepted['status'] == 'PASS'
baseline = Path(accepted['baseline_install']['baseline'])
runtime = Path(accepted['electron_runtime']['executable']).resolve(strict=True)
assert not runtime.is_relative_to('/Volumes') and runtime.stat().st_dev != disk.stat().st_dev
assert os.access(runtime, os.X_OK)
assert (source / 'workbench/node_modules/electron/dist/version').read_text(encoding='utf-8').strip() == '43.4.1'
for root in [source, baseline]:
    installed = json.loads((root / 'workbench/node_modules/electron/package.json').read_text(encoding='utf-8'))
    assert installed['version'] == accepted['electron_runtime']['version'] == '43.4.1'
for name in ['workbench/app/main.ts', 'workbench/app/preload.ts']:
    original = subprocess.run(['git', 'show', 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807:' + name],
                              check=True, stdout=subprocess.PIPE).stdout
    assert (baseline / name).read_bytes() == original, '基线文件已变：' + name
for name in accepted['source_files']:
    assert (source / name).read_bytes() == (Path(accepted['archive']) / 'source-snapshot' / name).read_bytes(), '已通过的产品／旅程源码已变：' + name

stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = disk / 'a2a-evidence/2026-10-19-batch17/T-103' / ('contracts-' + stamp)
out.mkdir(exist_ok=False)
(out / 'tmp').mkdir()
files = ['workbench/tests/test_t091_pane_ipc.mjs', 'workbench/tests/test_electron_e2e.py',
         'workbench/tests/electron_client.py', 'workbench/tests/electron_driver.mjs', 'workbench/tests/command_evidence.py',
         'evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-09-CONTRACTS.sh',
         'evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh']
for name in files:
    target = out / 'source-snapshot' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, target)
env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
env.pop('ELECTRON_RUN_AS_NODE', None)
env.pop('NODE_OPTIONS', None)
env.update(TMPDIR=str(out / 'tmp'), TMP=str(out / 'tmp'), TEMP=str(out / 'tmp'),
           electron_config_cache='/Volumes/WD-Elements/a2a-electron-cache',
           npm_config_cache='/Volumes/WD-Elements/a2a-t075-npm-cache')
report = {'status': 'INCOMPLETE', 'task': 'T-103', 'attempt': 'a1', 'authorization': '执行主控 #16：扩充两处旧合同；基线、候选与窗口级 pane-key 变异对照',
          'archive': str(out), 'e2e_summary': str(accepted_path), 'accepted_e2e_archive': accepted['archive'],
          'baseline': str(baseline), 'baseline_revision': 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807',
          'electron': str(runtime), 'electron_version': '43.4.1', 'source_files': files, 'checks': []}

def save():
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (out / 'run.json').write_text(text, encoding='utf-8')
    (evidence / (out.name + '-summary.json')).write_text(text, encoding='utf-8')

def run(label, argv):
    stdout, stderr = out / (label + '.stdout.txt'), out / (label + '.stderr.txt')
    entry = {'name': label, 'argv': [str(value) for value in argv], 'stdout': str(stdout), 'stderr': str(stderr), 'status': 'INCOMPLETE'}
    report['checks'].append(entry)
    save()
    with stdout.open('xb') as output, stderr.open('xb') as error:
        completed = subprocess.run(entry['argv'], cwd=source, env=env, stdout=output, stderr=error, timeout=240)
    entry['exit'] = completed.returncode
    assert completed.returncode == 0, entry
    return entry

try:
    for label, root, contract in [('baseline', baseline, 'legacy'), ('candidate', source, 'picker')]:
        result_path = out / (label + '-ipc.json')
        entry = run(label + '-ipc', ['node', '--experimental-vm-modules', source / 'workbench/tests/test_t091_pane_ipc.mjs',
                                    result_path, '--source', root, '--contract', contract])
        result = json.loads(result_path.read_text(encoding='utf-8'))
        assert result['status'] == 'PASS' and result['contract'] == contract
        assert all(result[name]['rejected'] for name in ['known_bad_result', 'single_pane_counterexample', 'close_mutant', 'empty_layout_known_bad'])
        if contract == 'picker':
            assert result['window_key_mutant']['rejected'] is True
        entry.update(status='PASS', result=result)
        save()

        window_out = out / (label + '-window')
        entry = run(label + '-window', [sys.executable, '-B', source / 'workbench/tests/test_electron_e2e.py',
                                       '--source', root, '--output', window_out, '--stage', 'window',
                                       '--ipc-contract', contract, '--runtime-source', source])
        verdict = json.loads((window_out / 'verdict.json').read_text(encoding='utf-8'))
        assert verdict['status'] == 'PASS' and verdict['daemon_stopped'] is True
        assert {item['name'] for item in verdict['checks']} == {
            'electron_build_entry', 'daemon_workbench_snapshot', 'daemon_output_unknown_launch', 'electron_real_window'}
        assert all(item['status'] == 'PASS' for item in verdict['checks'])
        observed = [json.loads(line) for line in (window_out / 'window-driver.jsonl').read_text(encoding='utf-8').splitlines()]
        owner = next(item for item in observed if 'argv' in item)
        ready = next(json.loads(item['response']) for item in observed if 'response' in item and json.loads(item['response']).get('ready'))
        assert Path(owner['argv'][0]).resolve(strict=True) == runtime and ready['electron'] == '43.4.1'
        entry.update(status='PASS', result={'status': verdict['status'], 'checks': verdict['checks'],
                    'ipc_contract': verdict['ipc_contract'], 'daemon_stopped': True,
                    'electron_executable': owner['argv'][0], 'electron_version': ready['electron'],
                    'screenshot': str(window_out / 'window/claimed-no-pane.png')})
        save()
    for name in files:
        assert (source / name).read_bytes() == (out / 'source-snapshot' / name).read_bytes(), '合同测试期间源码改变：' + name
    for name in accepted['source_files']:
        assert (source / name).read_bytes() == (Path(accepted['archive']) / 'source-snapshot' / name).read_bytes(), '旅程源码改变：' + name
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
finally:
    save()
    manifest = {'original': str(out), 'archive': str(out),
                'bytes': sum(path.stat().st_size for path in out.rglob('*') if path.is_file()),
                'replay': 'bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-09-CONTRACTS.sh'}
    (evidence / (out.name + '.archive.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
if report['status'] == 'PASS':
    results = evidence / 'RESULTS.md'
    prior = results.read_text(encoding='utf-8')
    assert not prior.startswith('\ufeff') and '\ufffd' not in prior
    addition = ('\n### 09 合同验证回传：' + stamp + '\n\n'
                '状态：PASS（本次合同验证范围）。基线按 legacy 合同、候选按 picker 合同，'
                '两份 IPC 检查与两份真实 Electron 窗口检查均通过；旧有四类坏实现及新的窗口级 pane-key 变异被拒。'
                '两份窗口使用同一内置盘 Electron 43.4.1，均已确认窗口退出和后台停止。\n\n'
                '摘要：`' + out.name + '-summary.json`；原始日志、截图、夹具归档及测试源码快照：`' + str(out) + '`。'
                '本次没有改动或重新借用其他产品候选；完整项目选择旅程仍绑定 `run-20261019T063741Z-summary.json`。'
                '提交与独立审查按主控后续结果确认，不把合同验证通过当作已集成。\n')
    with results.open('a', encoding='utf-8') as stream:
        stream.write(addition)
    assert results.read_text(encoding='utf-8') == prior + addition
    print('提交命令：bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh ' +
          str(accepted_path.relative_to(source)) + ' ' + str((evidence / (out.name + '-summary.json')).relative_to(source)))
    sys.stdout.flush()
    os.execv('/bin/bash', ['/bin/bash', str(evidence / 'RUN-OUTSIDE-03-COMMIT.sh'),
                         str(accepted_path), str(evidence / (out.name + '-summary.json'))])
raise SystemExit(0 if report['status'] == 'PASS' else 1)
PY
