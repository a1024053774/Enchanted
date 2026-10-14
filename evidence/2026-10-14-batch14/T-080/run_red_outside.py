#!/usr/bin/env python3
"""主控沙箱外运行：冻结当前 main，保留 T-080 验收文件篡改红态。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[3]
REVISION = '87e954a2f4059d471e3e240872b565217e29b0b5'
WORKER_BASE = 'cdf8fe9b0eebfacf9f8d2ffeff3aecebf1e6eb37'
LIMIT = 5_000_000
OUT = None
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
ENV.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1',
           GIT_CONFIG_GLOBAL=os.devnull)


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sizes():
    large = [{'path': str(p), 'bytes': p.stat().st_size} for p in OUT.rglob('*')
             if p.is_file() and p.stat().st_size > LIMIT]
    if large:
        raise RuntimeError('证据单文件超过 5 MB；停止，保留现场：' + json.dumps(large))


def unpack_source(stream, destination):
    """仅在空目录中写出已核对的普通文件和目录；兼容 Python 3.9。"""
    if destination.is_symlink() or not destination.is_dir() or any(destination.iterdir()):
        raise RuntimeError('源码解包目标必须是新的空目录。')
    root = destination.resolve(strict=True)
    checked = []
    seen = set()
    for member in stream.getmembers():
        if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE) or member.issparse():
            raise RuntimeError('源码归档包含链接或特殊成员：' + repr(member.name))
        name = member.name[:-1] if member.isdir() and member.name.endswith('/') else member.name
        parts = name.split('/')
        if (name.startswith('/') or '\\' in name or '\x00' in name
                or any(part in ('', '.', '..') for part in parts)):
            raise RuntimeError('源码归档包含非法路径：' + repr(member.name))
        target = root.joinpath(*parts)
        if root not in target.resolve().parents or target in seen:
            raise RuntimeError('源码归档路径越界或重复：' + repr(member.name))
        if member.size < 0 or member.size > LIMIT or member.isdir() and member.size != 0:
            raise RuntimeError('源码归档成员大小不合法或超过 5 MB：' + repr(member.name))
        seen.add(target)
        checked.append((member, target))
    # 所有成员校验后才写出；不调用 extract/extractall，不跟随归档中的链接。
    for member, target in checked:
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = stream.extractfile(member)
        if content is None:
            raise RuntimeError('源码归档普通文件无法读取：' + repr(member.name))
        with content, target.open('xb') as output:
            shutil.copyfileobj(content, output)
        if target.stat().st_size != member.size:
            raise RuntimeError('源码归档普通文件内容不完整：' + repr(member.name))
        target.chmod(member.mode & 0o777)


def observe(argv, label):
    sizes()
    record = {'argv': list(map(str, argv)), 'cwd': str(ROOT)}
    with (OUT / (label + '.stdout.bin')).open('xb') as stdout, \
            (OUT / (label + '.stderr.bin')).open('xb') as stderr:
        result = subprocess.run(record['argv'], cwd=ROOT, env=ENV,
                                stdout=stdout, stderr=stderr, timeout=45)
    record['exit'] = result.returncode
    save(OUT / (label + '.command.json'), record)
    sizes()
    if result.returncode:
        raise RuntimeError('预检查失败：' + label)
    return (OUT / (label + '.stdout.bin')).read_text(encoding='utf-8').strip()


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    OUT = args.output.resolve()
    evidence_root = ROOT / 'evidence/2026-10-14-batch14/T-080'
    if OUT.parent != evidence_root or OUT == evidence_root:
        raise RuntimeError('输出必须是 T-080 证据目录的一个新子目录。')
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-080',
               'scope': '红态复现；不是修复验收', 'argv': sys.argv,
               'baseline_revision': REVISION, 'worker_base': WORKER_BASE,
               'real_model_calls': 0, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        main_ref = observe(['git', 'rev-parse', 'refs/heads/main'], 'main-ref')
        head = observe(['git', 'rev-parse', 'HEAD'], 'worker-head')
        observe(['git', 'status', '--porcelain=v1', '--untracked-files=all'], 'worker-status')
        if main_ref != REVISION or head != WORKER_BASE:
            raise RuntimeError('main 或 worker 起点已变；停止报告，不改基线。')
        paths = ['workbench', 'acceptance/entry/a2a_gates.py']
        same = observe(['git', 'diff', '--exit-code', WORKER_BASE, REVISION, '--', *paths], 'baseline-product-diff')
        if same:
            raise RuntimeError('当前 main 产品与指定起点不同。')
        node = observe(['node', '--version'], 'node-version')
        observe(['git', '--version'], 'git-version')
        if not node.startswith('v26.5.') or not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('需要 Node 26.5 和已挂载外置盘；不安装或回退。')
        dependencies = ROOT / 'workbench/node_modules'
        helper = dependencies / 'node-pty/prebuilds/darwin-arm64/spawn-helper'
        if not dependencies.is_dir() or not os.access(helper, os.X_OK):
            raise RuntimeError('已安装依赖或 spawn-helper 执行权限缺失。')
        # 受控夹具不执行 Git hooks；不归档 hooks 的符号链接入口。
        archive_paths = ['workbench/src', 'workbench/tests', 'workbench/hooks/hook.py',
                         'workbench/package.json', 'workbench/package-lock.json',
                         'workbench/LICENSE.synara', 'acceptance/entry/a2a_gates.py']
        archive = OUT / 'baseline-source.tar.gz'
        observe(['git', 'archive', '--format=tar.gz', '--output', archive, REVISION, *archive_paths], 'freeze-main')
        fixture = Path(tempfile.mkdtemp(prefix='t80r-', dir='/tmp')).resolve()
        source = fixture / 'source'
        source.mkdir()
        with tarfile.open(archive, 'r:gz') as stream:
            unpack_source(stream, source)
        (source / 'workbench/node_modules').symlink_to(dependencies.resolve(), target_is_directory=True)
        receipt.update(source=str(source), source_archive=str(archive), dependencies=str(dependencies),
                       archive_paths=archive_paths, git_hook_aliases_excluded=True)
        save(OUT / 'source-manifest.json', receipt)
        sys.path.insert(0, str(source / 'workbench/tests'))
        import test_quality_chain_e2e as quality
        from test_quality_tracer_e2e import Tracer

        class Red(Tracer):
            def id(self):
                return 'T-080.' + self.case

            def process(self, *a, **kw):
                sizes()
                result = super().process(*a, **kw)
                sizes()
                return result

            def acceptance_file_tamper(self):
                criterion = 'acceptance/criterion.py'
                original = ('from pathlib import Path\n'
                            'assert Path("src/value.txt").read_text() == "worker\\n", '
                            '"independent required product value"\n')
                path = self.repo / criterion
                path.parent.mkdir()
                path.write_text(original, encoding='utf-8')
                self.git('add', criterion)
                self.git('commit', '-m', 'Freeze independently supplied acceptance test')
                self.base = self.oid()
                save(self.evidence / 'declared-contract.json', {
                    'oracle_paths': [criterion], 'expected_refusal': 'oracle_modified',
                    'baseline_schema_has_no_oracle_paths': True,
                    'reviewer_input': '合成可合并结论，仅用于证明机械门禁缺口'})
                probe = self.process([sys.executable, '-I', '-B', criterion], cwd=self.repo)
                if probe.returncode != 1 or 'AssertionError: independent required product value' not in probe.stderr:
                    raise quality.HarnessFailure('起点测试没有在独立业务断言上失败。')
                self.card['paths'] = {'allow': ['.'], 'deny': []}
                self.card['goal'] = 'src/value.txt 必须为 worker 加换行，验收文件不可修改'
                self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', criterion]}]
                a = self.start_worker()
                c = self.commit(a, {criterion: 'pass\n'})
                changed = self.git('diff', '--name-only', '--no-renames', self.base, c).splitlines()
                if changed != [criterion]:
                    raise quality.HarnessFailure('候选必须只修改完成条件调用的测试。')
                submitted = self.worker_submit(c)
                if not submitted['ok']:
                    raise quality.HarnessFailure('合法身份的显式 submit 失败。')
                self.approve(c)
                verified = self.cli('status')['task']
                if verified['state'] != 'verified':
                    raise quality.HarnessFailure('未观察到当前门禁通过验收。')
                save(self.evidence / 'acceptance-observation.json', {
                    'base': self.base, 'candidate': c, 'changed_paths': changed, 'task': verified,
                    'events': self.events(), 'before_integration_ref': self.oid(),
                    'candidate_diff': self.git('diff', '--no-ext-diff', self.base, c)})
                self.integrate_scored(c, rounds=1)
                retained_value = (self.repo / 'src/value.txt').read_text(encoding='utf-8')
                original_probe = self.process([sys.executable, '-I', '-B', '-c', original], cwd=self.repo)
                if original_probe.returncode != 1 or 'AssertionError: independent required product value' not in original_probe.stderr:
                    raise quality.HarnessFailure('独立原始断言没有拒绝已集成的错误产品。')
                save(self.evidence / 'hole-observation.json', {
                    'verified': True, 'integrated': True, 'branch_ref': self.oid(),
                    'base': self.base, 'candidate': c, 'changed_paths': changed,
                    'product_value': retained_value, 'independent_assertion_exit': original_probe.returncode,
                    'events': self.events(), 'original_criterion': original})
                self.check('ORACLE-MODIFIED', False,
                           '改动验收文件必须以 oracle_modified 拒收，不能验收或集成',
                           {'accepted_and_integrated': True, 'branch_ref': self.oid(), 'product_value': retained_value})

        quality.run_cases(source, OUT / 'cases', ['acceptance_file_tamper'], case_type=Red, dialect='current')
        sizes()
        report = json.loads((OUT / 'cases/run.json').read_text(encoding='utf-8'))
        rows = report['cases']
        reproduced = (len(rows) == 1 and rows[0]['outcome'] == 'contract_failure'
                      and rows[0].get('failure_id') == 'ORACLE-MODIFIED' and not rows[0]['cleanup_failures'])
        with tarfile.open(OUT / 'fixtures.tar.gz', 'x:gz') as stream:
            stream.add(report['artifact_root'], arcname=Path(report['artifact_root']).name)
        sizes()
        receipt.update(status='PASS' if reproduced else 'INCOMPLETE',
                       red_contract_failure='ORACLE-MODIFIED' if reproduced else None,
                       artifact_root=report['artifact_root'], cases_report=str(OUT / 'cases/run.json'))
    except Exception as error:
        receipt.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        receipt['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(OUT / 'receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
