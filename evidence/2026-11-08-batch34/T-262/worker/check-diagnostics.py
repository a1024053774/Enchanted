"""夹具准备与诊断自检；不启动后台、Electron、模型或 ps，不证明产品行为。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd()
source = ROOT / 'workbench/tests/test_t262_records_e2e.py'
spec = importlib.util.spec_from_file_location('t262', source)
test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test)
report = dict(status='INCOMPLETE', scope='仅夹具准备和诊断；无产品 UI 证据', checks=[])
fixture = test.Fixture(report)
try:
    fixture.prepare('f80d5cdbf0e1b62de864300eff7bb4497f8c4c70')
    assert max(report['socket_bytes'].values()) <= 103
    report['checks'].append('所有预计 Unix socket 路径不超过 103 字节')
    # The deliberately failing subprocess proves the diagnostic collector preserves an
    # abnormal return code and the tail of a real log, including its truncation marker.
    fixture.log = (fixture.root / 'electron.log').open('w', encoding='utf-8')
    fixture.process = subprocess.Popen([sys.executable, '-c',
        'import sys; print("x" * 17000); print("T262_DIAGNOSTIC_SENTINEL"); sys.exit(7)'],
        cwd=ROOT, stdout=fixture.log, stderr=subprocess.STDOUT, start_new_session=True)
    fixture.process.wait(10)
    fixture.diagnostics('before_cleanup')
    snapshot = report['diagnostics']['before_cleanup']
    assert snapshot['returncode'] == 7
    log = snapshot['logs']['electron.log']
    assert log['truncated'] and log['bytes'] > 16000 and 'T262_DIAGNOSTIC_SENTINEL' in log['tail']
    persisted = json.loads(fixture.diagnostics_file.read_text(encoding='utf-8'))
    assert persisted['returncode'] == 7 and 'T262_DIAGNOSTIC_SENTINEL' in persisted['logs']['electron.log']['tail']
    report['checks'].append('真实本地子进程的退出码 7、日志尾部和截断标记被保留')
    fixture.stop()  # phase=prepare; no daemon/core/ps path is entered.
    assert not fixture.root.exists()
    assert report['diagnostics']['after_cleanup']['returncode'] == 7
    assert len(fixture.diagnostics_file.read_text(encoding='utf-8').splitlines()) == 2
    report['checks'].append('清理前诊断已落盘，清理后仍可读')
    report['checks'].append('已退出子进程不再 terminate；自有准备夹具清理完成，诊断仍在')
    # Compact self-check output: preserve the meaningful tail, not the filler bytes.
    for snapshot in report['diagnostics'].values():
        snapshot['logs']['electron.log']['tail'] = snapshot['logs']['electron.log']['tail'][-60:]
    # Only synthetic filler is removed; the compact self-check report retains both stages.
    fixture.diagnostics_file.unlink()
    report['status'] = 'PASS'
finally:
    print(json.dumps(report, ensure_ascii=False, indent=2))
