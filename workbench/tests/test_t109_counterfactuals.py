"""用 T-109 起点运行同一个合同检查；保存具体业务红态，拒绝基础设施错误。"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
assert not args.summary.exists()
source = Path(__file__).resolve().parents[2]
revision = '6411bdff8482ba47da207efa6a295a12666222aa'
root = Path(tempfile.mkdtemp(prefix='t109-red-', dir='/private/tmp'))
env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'A2A_'))}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
report = dict(status='INCOMPLETE', baseline=revision, model_calls=0, checks=[])
try:
    archive = subprocess.check_output(['git', 'archive', revision, 'scripts', 'workbench/src'], cwd=source, env=env)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(root)
    # Launch provenance queries its own source repository, so this private
    # archive is also a Git fixture. No inherited Git routing reaches a checkout.
    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', str(root)], env=env, check=True, capture_output=True)
    subprocess.run(['git', '-C', str(root), 'add', 'scripts'], env=env, check=True)
    subprocess.run(['git', '-C', str(root), '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=T109 fixture',
                    '-c', 'user.email=t109@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-m', 'Frozen baseline scripts'], env=env, check=True, capture_output=True)
    shutil.copytree(source / 'workbench/node_modules', root / 'workbench/node_modules', symlinks=False)
    for name, command, expected in [
        ('launch', ['python3', 'workbench/tests/test_t109_dispatch.py', '--source', str(root), '--summary', str(root / 'launch.json')], 'Launch command dropped parent launch'),
        ('hierarchy', ['node', 'workbench/tests/test_t109_hierarchy.mjs', str(root / 'hierarchy.json'), str(root / 'workbench/src/sidebar.ts')], 'Explicit executor parent launch must be projected'),
    ]:
        result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=60)
        value = json.loads((root / (name + '.json')).read_text(encoding='utf-8'))
        assert result.returncode == 1 and expected in value.get('error', ''), (result.returncode, value, result.stderr)
        report['checks'].append(dict(name=name, command=command, exit=result.returncode, rejected_for=value['error']))
    mutant = root / 'write-mutant'
    shutil.copytree(source / 'workbench/src', mutant / 'workbench/src')
    projection = mutant / 'workbench/src/sidebar.ts'
    text = projection.read_text(encoding='utf-8')
    marker = '  const launches = store.launches()'
    assert text.count(marker) == 1
    projection.write_text(text.replace(marker, "  store.event('sidebar_read', { source: 'write-mutant' });\n" + marker), encoding='utf-8')
    command = ['node', '--experimental-vm-modules', 'workbench/tests/test_t107_daemon_readonly.mjs', str(root / 'write.json'), str(mutant), 'readonly']
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=60)
    value = json.loads((root / 'write.json').read_text(encoding='utf-8'))
    assert result.returncode == 1 and value.get('cleanup_complete') and 'Sidebar read changed persisted tables or traces' in value.get('error', ''), value
    report['checks'].append(dict(name='sidebar-write-mutant', command=command, exit=result.returncode, rejected_for=value['error']))
    conflicting = root / 'workbench/parent-mutant'
    shutil.copytree(source / 'workbench/src', conflicting)
    projection = conflicting / 'sidebar.ts'
    text = projection.read_text(encoding='utf-8')
    marker = 'senders.size === 1 ? [...senders][0] : null'
    assert text.count(marker) == 1
    projection.write_text(text.replace(marker, 'senders.size ? [...senders][0] : null'), encoding='utf-8')
    command = ['node', 'workbench/tests/test_t109_hierarchy.mjs', str(root / 'parent-conflict.json'), str(projection)]
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=60)
    value = json.loads((root / 'parent-conflict.json').read_text(encoding='utf-8'))
    assert result.returncode == 1 and 'Conflicting explicit parent and authenticated successful assign must remain unassigned' in value.get('error', ''), value
    report['checks'].append(dict(name='conflicting-parent-mutant', command=command, exit=result.returncode, rejected_for=value['error']))
    title_mutant = root / 'workbench/title-mutant'
    shutil.copytree(source / 'workbench/src', title_mutant)
    projection = title_mutant / 'sidebar.ts'
    text = projection.read_text(encoding='utf-8')
    marker = "    if (typeof record.parent_launch === 'string') senders.add(record.parent_launch);"
    assert text.count(marker) == 1
    # Reproduce independent review F1 exactly; this intentionally wrong branch
    # exists only in the private mutant, never in production source.
    wrong_title_branch = "\n    else if (record.role === 'worker' && gates.listTasks(record.project).find(task => task.task_id === record.task)?.title?.includes('执行主控')) senders.add(launches.find(row => row.preset === 'executor').id);"
    projection.write_text(text.replace(marker, marker + wrong_title_branch), encoding='utf-8')
    command = ['node', 'workbench/tests/test_t109_hierarchy.mjs', str(root / 'task-title.json'), str(projection)]
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=60)
    value = json.loads((root / 'task-title.json').read_text(encoding='utf-8'))
    assert result.returncode == 1 and 'Task titles must not supply parent launch facts for legacy sessions' in value.get('error', ''), value
    report['checks'].append(dict(name='task-title-parent-inference-mutant', command=command, exit=result.returncode, rejected_for=value['error']))
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
report['retained_fixture'] = str(root)
args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
