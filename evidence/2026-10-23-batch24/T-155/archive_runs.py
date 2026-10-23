"""归档 T-155 已停止的原始证据；保留原件，不执行产品操作。"""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


HERE = Path(__file__).resolve().parent
VOLUME = Path('/Volumes/WD-Elements')
DEST = VOLUME / 'a2a-evidence/2026-10-23-batch24/T-155'
ROOTS = [Path('/private/tmp') / name for name in (
    't155-dogfood-lv2rm2nt', 't155-dogfood-ohzs_78v',
    't155-dogfood-9lz6vh2i', 't155-readback-erpqx1w4',
    't155-final-readback')]


def inventory(root):
    files, directories, sockets = {}, [], []
    def fail(error):
        raise error
    for parent, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        for name in sorted(dirs + names):
            path = Path(parent) / name
            relative = str(path.relative_to(root))
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                files[relative] = info.st_size
            elif stat.S_ISDIR(info.st_mode):
                directories.append(relative)
            elif stat.S_ISSOCK(info.st_mode):
                sockets.append({'path': relative, 'mode': oct(info.st_mode),
                                'reason': 'Unix socket 不是可重放文件；仅保留路径与类型，原件不删除'})
            else:
                raise RuntimeError('拒绝未核对的链接或特殊文件：' + str(path))
    return files, directories, sockets


def main():
    if not os.path.ismount(VOLUME):
        raise RuntimeError('外置盘未挂载；不回退内置盘')
    for root in ROOTS[:2]:
        if (root / 'state/daemon.pid').exists() or (root / 'state/control.sock').exists():
            raise RuntimeError('后台停止尚未核对：' + str(root))
        config = json.loads((root / 'instance.json').read_text(encoding='utf-8'))
        if config['root'] != str(root) or config['source'] != str(HERE.parents[2]):
            raise RuntimeError('实例归属不符：' + str(root))
    processes = subprocess.run(['/bin/ps', '-axo', 'pid=,command='],
                               capture_output=True, text=True, check=True).stdout
    for line in processes.splitlines():
        if any(str(root) in line for root in ROOTS[:2]):
            raise RuntimeError('仍有实例进程，保留原件：' + line)
    native = Path('/Users/luckye/.claude/projects')
    owned_native = [p for p in sorted(native.glob('*t155-dogfood*'))
                    if p.name.startswith(('-private-tmp-t155-dogfood-lv2rm2nt-',
                                          '-private-tmp-t155-dogfood-ohzs-78v-'))]
    if not owned_native:
        raise RuntimeError('本票原生会话目录缺失')
    sources = [(p, DEST / p.name) for p in ROOTS]
    sources += [(p, DEST / 'native-claude' / p.name) for p in owned_native]
    # 全部预检后才开始复制；已有归档绝不覆盖。
    prepared = []
    for source, target in sources:
        if not source.is_dir() or target.exists():
            raise RuntimeError('源目录缺失或目标已存在：' + str(source))
        prepared.append((source, target, inventory(source)))
    DEST.mkdir(parents=True, exist_ok=False, mode=0o700)
    entries = []
    for source, target, (files, directories, sockets) in prepared:
        target.mkdir(parents=True, exist_ok=False, mode=0o700)
        for relative in directories:
            (target / relative).mkdir(parents=True, exist_ok=True)
        for relative in files:
            shutil.copy2(source / relative, target / relative)
        copied, _, _ = inventory(target)
        if files != copied or inventory(source)[0] != files:
            raise RuntimeError('归档前后文件数或字节数不一致：' + str(source))
        # 逐字节比较，不计算摘要；异常保留两侧现场。
        for relative in files:
            with (source / relative).open('rb') as left, (target / relative).open('rb') as right:
                while True:
                    a, b = left.read(1024 * 1024), right.read(1024 * 1024)
                    if a != b:
                        raise RuntimeError('归档内容不一致：' + relative)
                    if not a:
                        break
        entries.append({'original': str(source), 'archive': str(target),
                        'files': len(files), 'bytes': sum(files.values()),
                        'special_files': sockets, 'original_retained': True,
                        'replay': '只读查看该目录；启动复现见同票 PLAN.md、SESSION-NOTES.md 与 RESULTS.md。原生日志按根 user 消息重计，不能作为自动业务重放脚本。'})
    manifest = {'status': 'PASS', 'scope': '仅归档完整性，不代表产品流程通过',
                'verification': '源/目标逐文件大小、文件数、总字节和内容相等；未计算哈希；未删除原件',
                'command': 'python3 evidence/2026-10-23-batch24/T-155/archive_runs.py',
                'entries': entries}
    with (HERE / 'runs.archive.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': 'PASS', 'directories': len(entries),
                      'files': sum(e['files'] for e in entries),
                      'bytes': sum(e['bytes'] for e in entries)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
