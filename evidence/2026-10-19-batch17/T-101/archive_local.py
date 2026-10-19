#!/usr/bin/env python3
"""逐项归档本票本地夹具；缺失源记录为 INCOMPLETE，继续处理其他源。"""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
import uuid

from slim_history import ARCHIVES, HERE, REL, disk_tree, mounted, no_links, read, require, save


def replay(report, data):
    if report.name.startswith('followup-'):
        return ['python3', '-B', str(REL / 'run_followup_checks.py'), '--report', 'NEW_REPORT.json'], []
    if report.name.startswith('local-checks-'):
        return ['python3', '-B', str(REL / 'run_local_checks.py'), '--report', 'NEW_REPORT.json'], []
    commands = [row['argv'][:-1] + ['NEW_ARTIFACT_DIRECTORY'] for row in data['checks']]
    return commands[0], commands[1:]


def main():
    mounted()
    invocation = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    results = []
    reports = sorted(set(HERE.glob('*checks-*.json')) | set(HERE.glob('followup-*.json')))
    for report in reports:
        data = read(report)
        if 'artifact_root' not in data:
            continue
        source = Path(data['artifact_root'])
        require(source.is_relative_to(Path('/private/tmp')) and source.name.startswith('a2a-t101-'), '不是本票隔离产物')
        target = ARCHIVES / 'local-preparation' / report.stem
        no_links(source)
        no_links(target)
        manifest = report.with_suffix('.archive.json')
        if manifest.exists():
            entry = read(manifest)
            require(entry['original'] == str(source) and entry['archive'] == str(target), '已有清单归属不符')
            inventory = disk_tree(target)
            require(target.is_dir() and all(v[0] == 'file' for v in inventory.values())
                    and len(inventory) == entry['files'] and sum(v[1] for v in inventory.values()) == entry['bytes'],
                    '已有归档文件数/字节数不符；保留现场')
            if source.is_dir():
                require(disk_tree(source) == inventory, '原件与已有归档不符；不覆盖')
            results.append({'report': report.name, 'status': 'PASS', 'result': 'already_archived',
                            'source_present': source.is_dir(), 'manifest': str(manifest)})
            continue
        if not source.exists():
            missing = report.with_name(report.stem + '.missing-' + invocation + '.json')
            save(missing, {'status': 'INCOMPLETE', 'original': str(source), 'archive': None,
                           'bytes': None, 'files': None, 'reason': 'source_not_found',
                           'report': report.name, 'at': invocation,
                           'note': '未归档，不补称为已保存；继续处理其他源'})
            results.append({'report': report.name, 'status': 'INCOMPLETE', 'result': 'source_not_found',
                            'record': str(missing)})
            continue
        require(source.is_dir(), '源不是目录')
        require(not target.exists(), '已有归档但缺清单；保留部分现场，需主控核对')
        expected = disk_tree(source)
        require(all(row[0] == 'file' for row in expected.values()), '夹具中有链接或特殊类型，停止')
        shutil.copytree(source, target, symlinks=True)
        require(expected == disk_tree(source) == disk_tree(target), '文件数/字节数不一致')
        command, other = replay(report, data)
        save(manifest, {'original': str(source), 'archive': str(target),
                        'bytes': sum(row[1] for row in expected.values()), 'files': len(expected),
                        'replay': command, 'additional_replay': other,
                        'environment': '现有套件重放只在子进程移除继承的 GIT_CONFIG_*；见 RESULTS.md',
                        'note': '保留 /tmp 原件；目录复制核对完成，未删除原件'})
        results.append({'report': report.name, 'status': 'PASS', 'result': 'archived', 'manifest': str(manifest)})
    status = 'INCOMPLETE' if any(row['status'] != 'PASS' for row in results) else 'PASS'
    summary = HERE / ('archive-local-' + invocation + '.json')
    save(summary, {'status': status, 'results': results,
                   'exit_semantics': '0 表示遍历完成；缺失源仍为 INCOMPLETE，不代表所有原始现场都已归档'})
    print(status + ' 归档遍历完成：' + str(summary))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print('NO_GO ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
