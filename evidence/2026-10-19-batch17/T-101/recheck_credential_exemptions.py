#!/usr/bin/env python3
"""复核固定试跑候选，并在借用只读对象的隔离 Git 副本中验证新命中拒绝。"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from slim_history import (BASE, EXEMPTIONS_PATH, CredentialScanRejected, credential_exemptions,
                          git, history_versions, mounted, no_links, public_native_sessions,
                          read, refs, require, save, scan, tree)


def private_git(repo, *args, data=None, index=None):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith('GIT_CONFIG_') and key not in (
                       'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES')}
    environment.update(GIT_AUTHOR_NAME='T101 negative fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                       GIT_COMMITTER_NAME='T101 negative fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    if index is not None:
        environment['GIT_INDEX_FILE'] = str(index)
    result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                            input=data, capture_output=True, env=environment)
    require(result.returncode == 0, '隔离 Git 操作失败；不打印可能含正文的输出：' + args[0])
    return result.stdout


def negative_probe(source, output, baseline, exemptions_path=EXEMPTIONS_PATH):
    output.mkdir(parents=True, exist_ok=False)
    before_refs = refs(source)
    mirror = output / 'negative.git'
    # --shared 只在隔离反例中借用原候选对象，不复制大 pack，不改原候选。
    # 不用于正式改写或正式备份；重放需要保留原候选。
    private_git(output, 'clone', '--shared', '--mirror', str(source), str(mirror))
    current = tree(mirror)
    approved_objects = {hit['object'] for hit in baseline['hits'] if hit.get('exempted') and 'object' in hit}
    choices = sorted(path for path, row in current.items()
                     if path.startswith('workbench/tests/') and row['mode'] in ('100644', '100755')
                     and row['oid'] in approved_objects and re.fullmatch('[A-Za-z0-9_./-]+', path))
    require(choices, '找不到当前树内具有精确已豁免命中的测试文件；不猜测反例来源')
    changed_path = choices[0]
    original = current[changed_path]
    original_bytes = git(mirror, 'cat-file', 'blob', original['oid'])
    synthetic = ('a2a-new-fake-' + uuid.uuid4().hex).encode('ascii')
    new_bytes = b'Bearer ' + synthetic + b'\n'
    # Git plumbing 创建必要的反例对象，避免在内置盘 checkout 整个候选；不生成凭据指纹。
    added_object = private_git(mirror, 'hash-object', '-w', '--stdin', data=new_bytes).decode().strip()
    changed_object = private_git(mirror, 'hash-object', '-w', '--stdin', data=original_bytes + b'\n').decode().strip()
    require(changed_object != original['oid'], '对象变化反例未形成新对象')
    index = output / 'negative.index'
    private_git(mirror, 'read-tree', 'HEAD', index=index)
    added_path = 'negative-fixture/new-credential.txt'
    require(added_path not in current, '反例路径已存在；不覆盖')
    private_git(mirror, 'update-index', '--add', '--cacheinfo', '100644,' + added_object + ',' + added_path, index=index)
    private_git(mirror, 'update-index', '--add', '--cacheinfo', original['mode'] + ',' + changed_object + ',' + changed_path, index=index)
    negative_tree = private_git(mirror, 'write-tree', index=index).decode().strip()
    parent = git(mirror, 'rev-parse', 'HEAD').decode().strip()
    commit = private_git(mirror, 'commit-tree', negative_tree, '-p', parent,
                         data=b'T101 credential exemption negative fixture\n').decode().strip()
    private_git(mirror, 'update-ref', 'refs/heads/credential-exemptions-negative', commit)
    rejected = False
    try:
        scan(mirror, output / 'negative-scan.json', exemptions_path)
    except CredentialScanRejected:
        rejected = True
    require(rejected, '新凭据反例未被拒绝')
    result = read(output / 'negative-scan.json')
    new_hits = [hit for hit in result['hits'] if not hit['exempted']]
    require(any(hit.get('object') == added_object and hit.get('type') == 'authorization-bearer' for hit in new_hits),
            '新增的假凭据没有作为未豁免命中被抓到')
    old_offsets = {hit['offset'] for hit in baseline['hits'] if hit.get('object') == original['oid'] and hit['exempted']}
    changed_hits = [hit for hit in new_hits if hit.get('object') == changed_object and hit.get('offset') in old_offsets]
    require(changed_hits, '同一原命中换对象后仍获豁免，或没有形成对象绑定反例')
    require(refs(source) == before_refs, '原候选 refs 改变；停止')
    proof = {'status': 'PASS', 'negative_scan_status': result['status'],
             'exempted_hit_count': result['exempted_hit_count'], 'unexempted_hit_count': result['unexempted_hit_count'],
             'new_synthetic_object': added_object, 'new_synthetic_path': added_path,
             'changed_path': changed_path, 'previously_exempted_object': original['oid'], 'changed_object': changed_object,
             'same_offsets_now_unexempted': sorted({hit['offset'] for hit in changed_hits}),
             'source_refs_unchanged': True, 'parent': parent, 'negative_commit': commit,
             'object_storage': '仅反例共享只读原候选的 objects；重放须保留原候选；非正式备份/改写',
             'output_policy': '报告不含原文；合成假值只存在于隔离反例 Git 对象'}
    save(output / 'proof.json', proof)
    return proof


def recheck(run, output):
    require(not output.exists(), '复核输出已存在；保留现场，用全新输出目录')
    no_links(output)
    output.mkdir(parents=True)
    source = run / 'candidate.git'
    source_refs = refs(source)
    baseline = scan(source, output / 'baseline-scan.json')
    require(baseline['hit_count'] == baseline['exempted_hit_count'] == 413 and baseline['unexempted_hit_count'] == 0,
            '本次固定试跑未满足 413 处全部豁免、0 未豁免；停止，不改清单')
    approved = credential_exemptions(EXEMPTIONS_PATH)
    observed = {(hit.get('object'), hit.get('offset')) for hit in baseline['hits'] if hit['exempted']}
    require(observed == approved, '试跑候选与批准的 413 个精确定位不一致')
    proof = negative_probe(source, output / 'counterexample', baseline)
    required = public_native_sessions()
    versions = history_versions(source)
    missing = [path for path, ids in required.items() if not ids <= set(versions.get(path, []))]
    require(refs(source) == source_refs, '复核期间原候选 refs 改变')
    result = {'status': 'PASS', 'scope': '旧试跑候选的精确豁免与新命中拒绝，不代表正式交付/发布通过',
              'hit_count': baseline['hit_count'], 'exempted_hit_count': baseline['exempted_hit_count'],
              'unexempted_hit_count': 0, 'objects_scanned': baseline['objects_scanned'],
              'counterexample': proof, 'session_retention': {'status': 'INCOMPLETE' if missing else 'PASS',
                  'required': len(required), 'present': len(required) - len(missing), 'missing_paths': missing,
                  'note': '旧候选由旧移出清单生成；新版正式 02 明确保留全部 23 个精确路径与版本，必须新 run 重做。恢复的文件如有新命中仍停。'},
              'source_refs_unchanged': True, 'exemptions_path': str(EXEMPTIONS_PATH)}
    save(output / 'result.json', result)
    print('PASS 豁免复核：413 总命中，413 已豁免，0 未豁免；新增假值/换对象反例均被拒绝')
    if missing:
        print('INCOMPLETE 旧候选只保留 ' + str(len(required) - len(missing)) + '/23 个会话路径；正式须新 run 重做')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.run_id), 'run id 无效')
    mounted()
    run = BASE / args.run_id
    output = args.output_dir or run / 'credential-exemptions-recheck-01'
    no_links(run)
    recheck(run, output)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print('NO_GO ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
