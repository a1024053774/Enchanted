"""Private copies + real installed Claude/local fake API + Electron. Python 3.9.

The red candidate removes only the visible notification list. The same native
entry and business assertion must reject it, then accept the unchanged candidate.
No model/vendor calls, screenshots, shared output links or global configuration.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--summary', type=Path, required=True)
    p.add_argument('--electron-dist', type=Path, required=True)
    p.add_argument('--baseline', default='c5ac40c0b4cf60c30407af1a00953a297eb55005')
    p.add_argument('--receipt-comparison', action='store_true')
    args = p.parse_args()
    source = Path(__file__).resolve().parents[2]
    output = args.summary.resolve()
    assert not output.exists(), 'Use a fresh summary path'
    root = Path(tempfile.mkdtemp(prefix='t078-2-t110-', dir='/private/tmp')).resolve()
    env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'):
        env.pop(key, None)
    report = dict(status='INCOMPLETE', task='T-110', attempt='a1', fixture=str(root), commands=[],
                  model_calls=0, vendor_calls=0, screenshots=[], runs=[])
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, env=env, text=True).strip()
        report['source_head'] = revision
        report['source_changes'] = subprocess.check_output(['git', 'status', '--short'], cwd=source, env=env, text=True).splitlines()
        copy = root / 'candidate'
        copy.mkdir()
        shutil.copytree(source / 'workbench', copy / 'workbench', symlinks=False,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__'))
        shutil.copytree(source / 'workbench/node_modules', copy / 'workbench/node_modules', symlinks=False)
        # Only this newly created, private test copy receives the executable bit.
        helper = copy / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
        helper.chmod(0o755)
        component = copy / 'workbench/app/AppNotifications.tsx'
        original = component.read_text(encoding='utf-8')
        candidate = {name: (copy / name).read_bytes() for name in ['workbench/app/main.ts', 'workbench/app/notificationCenter.ts',
                     'workbench/app/renderer.tsx', 'workbench/src/transport.ts']}
        baseline = {name: subprocess.check_output(['git', 'show', args.baseline + ':' + name], cwd=source, env=env) for name in candidate}
        report['disconnect_baseline'] = args.baseline
        reconnect_revision = 'e1c7b5c275eaca7e342da44cb2582cf81f56ca17'
        reconnect_baseline = {name: subprocess.check_output(['git', 'show', reconnect_revision + ':' + name], cwd=source, env=env) for name in candidate}
        report['reconnect_baseline'] = reconnect_revision
        receipt_revision = '4a6d6bb9ecefc2bb16196b326ff032726d4d16fb'
        receipt_baseline = {name: subprocess.check_output(['git', 'show', receipt_revision + ':' + name], cwd=source, env=env) for name in candidate}
        report['receipt_baseline'] = receipt_revision
        report['receipt_comparison'] = args.receipt_comparison
        previous = {'red-disconnected-badge': (baseline, args.baseline),
                    'red-reconnect-view': (reconnect_baseline, reconnect_revision),
                    'parent-reconnect-answer': (reconnect_baseline, reconnect_revision),
                    'red-reconnect-answer': (receipt_baseline, receipt_revision)}
        fixtures = root / 'fixtures'
        fixtures.mkdir()
        marker = 'notices.map(notice =>'
        assert original.count(marker) == 1
        cases = [('parent-reconnect-answer', False, False), ('green-parent-recovery', False, False)] if args.receipt_comparison else [
            ('red-hidden-notices', False, True), ('red-disconnected-badge', False, False), ('red-reconnect-view', False, False),
            ('red-reconnect-answer', False, False), ('green', False, False), ('disabled', True, False)]
        for label, disabled, mutant in cases:
            component.write_text(original.replace(marker, 'notices.slice(0, 0).map(notice =>') if mutant else original, encoding='utf-8')
            product, tested_revision = previous.get(label, (candidate, revision))
            for name, content in product.items():
                (copy / name).write_bytes(content)
            summary = root / (label + '.json')
            command = ['/usr/bin/python3', '-B', str(copy / 'workbench/tests/run_t108_native_e2e.py'),
                       '--summary', str(summary), '--electron-dist', str(args.electron_dist.resolve()),
                       '--source-revision', tested_revision, '--fixture-parent', str(fixtures), '--notifications']
            if disabled:
                command.append('--disable-notifications')
            if args.receipt_comparison:
                command.append('--receipt-comparison-refresh')
            with (root / (label + '.log')).open('x', encoding='utf-8') as log:
                result = subprocess.run(command, cwd=copy, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
            report['commands'].append(dict(argv=command, exit=result.returncode))
            value = json.loads(summary.read_text(encoding='utf-8'))
            report['runs'].append(dict(label=label, summary=str(summary), result=value))
            if mutant:
                assert result.returncode == 1 and value['status'] == 'INCOMPLETE'
                assert 'One in-app waiting-user notification' in value.get('error', ''), value
                assert not value.get('window_cleanup_error') and not value.get('daemon_cleanup_error') and not value.get('process_cleanup_errors'), value
                report['red_business_rejected'] = True
            elif label == 'red-disconnected-badge':
                assert result.returncode == 1 and value['status'] == 'INCOMPLETE'
                assert 'Disconnected unknown state must clear Dock badge' in value.get('error', ''), value
                assert value['disconnect_observation']['badge'] == 1, value
                assert not any(value.get(key) for key in ['window_cleanup_error', 'daemon_cleanup_error', 'process_cleanup_errors']), value
                report['disconnect_red_business_rejected'] = True
            elif label == 'red-reconnect-view':
                assert result.returncode == 1 and value['status'] == 'INCOMPLETE'
                assert 'Reload keeps the selected project after reconnect' in value.get('error', ''), value
                observed = value['reconnect_observation']
                assert any(agent['state'] == 'waiting_user_answer' for agent in observed['sidebar']['agents']), value
                assert not any(value.get(key) for key in ['window_cleanup_error', 'daemon_cleanup_error', 'process_cleanup_errors']), value
                report['reconnect_red_business_rejected'] = True
            elif label in ['red-reconnect-answer', 'parent-reconnect-answer']:
                assert value.get('answer_attempted'), 'Comparison must reach the unchanged answer/receipt entry'
                assert not any(value.get(key) for key in ['window_cleanup_error', 'daemon_cleanup_error', 'process_cleanup_errors']), value
                if label == 'parent-reconnect-answer' and result.returncode == 0:
                    assert value['status'] == 'PASS' and value['first_answer_receipt']['final_receipt']['ok'] is True, value
                    report['parent_answer_receipt'] = 'PASS'
                else:
                    assert result.returncode == 1 and value['status'] == 'INCOMPLETE'
                    assert any(event['type'] == 'request_rejected' and event['data']['result']['error'] == 'invalid_window_sequence'
                               for event in value['window_events']), value
                    assert 'First window_answer final receipt timed out' in value.get('error', '') or 'Question option unavailable' in value.get('error', ''), value
                    assert any('invalid_window_sequence' in alert for alert in value['failure_view']['alerts']), value
                    if label == 'parent-reconnect-answer':
                        report['parent_answer_receipt'] = 'FAILED_INVALID_WINDOW_SEQUENCE'
                    else:
                        report['answer_red_business_rejected'] = True
            else:
                assert result.returncode == 0 and value['status'] == 'PASS', value
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        # Dependencies are disposable build inputs in our private copy. Native
        # fixtures and every failure result remain for evidence archival.
        copied_dependencies = root / 'candidate/workbench/node_modules'
        if copied_dependencies.exists():
            try:
                shutil.rmtree(copied_dependencies)
            except OSError as error:
                report.update(status='INCOMPLETE', dependency_cleanup_error=str(error))
        with output.open('x', encoding='utf-8') as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write('\n')
        print(json.dumps(dict(status=report['status'], summary=str(output), error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
