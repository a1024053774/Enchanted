#!/bin/zsh
# T-108 第二轮独立审查补证：仅本地假 API，不读取登录凭据，不调用真实模型。
# 在沙箱外由执行主控运行；本 reviewer 只检查脚本，不启动 Electron。
# 运行：zsh evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-02.sh
# 可选参数：源仓库、依赖目录、内置盘 Electron dist。
set -eu
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
SOURCE=${1:-/Users/luckye/Documents/Code/a2a-wt-t108}
DEPENDENCIES=${2:-$SOURCE/workbench/node_modules}
ELECTRON_DIST=${3:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
REVIEW_RUN=$(mktemp -d /private/tmp/t108-review-outside-02-XXXXXX)
export REVIEW_RUN SOURCE DEPENDENCIES ELECTRON_DIST
print -r -- "本次独立临时目录：$REVIEW_RUN"
/usr/bin/python3 -B - <<'PY'
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

assert sys.version_info[:2] == (3, 9), '本脚本要求 Python 3.9'
revision = 'a6c7c161ba101f4dc58870ace9dfa3ae4b1e8fe4'
root = Path(os.environ['REVIEW_RUN']).resolve(strict=True)
source = Path(os.environ['SOURCE']).resolve(strict=True)
dependencies = Path(os.environ['DEPENDENCIES']).resolve(strict=True)
dist = Path(os.environ['ELECTRON_DIST']).resolve(strict=True)
assert not str(dist).startswith('/Volumes/'), 'Electron 必须在内置盘'
assert (dist/'version').read_text(encoding='utf-8').strip() == '43.4.1'
assert (dist/'Electron.app/Contents/MacOS/Electron').is_file()
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))
       and k not in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0',
           GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
archive = subprocess.check_output(['git', '-C', str(source), 'archive', revision, 'workbench'], env=env)
candidate = root/'candidate'
candidate.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    members = tar.getmembers()
    assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
    assert not any(m.islnk() for m in members)
    tar.extractall(candidate, members=[m for m in members if not m.issym()])
    # 仓库的 Git hook 链接展开成普通文件；不新建任何符号链接。
    for member in members:
        if member.issym():
            path = candidate/member.name
            target = (path.parent/member.linkname).resolve(strict=True)
            assert candidate in target.parents
            path.write_bytes(target.read_bytes())
            path.chmod(member.mode)
shutil.copytree(dependencies, candidate/'workbench/node_modules', symlinks=False)
for helper in (candidate/'workbench/node_modules/node-pty/prebuilds').glob('darwin-*/spawn-helper'):
    helper.chmod(0o755)
assert not any(path.is_symlink() for path in candidate.rglob('*'))
# 已确认仍有两项未知状态缺陷；本脚本只补当前候选的正常完整入口证据，
# 即使运行 PASS，也不能据此关闭 independent-review-02.md 中的发现。
# git archive 没有 .git。仅把测试的版本来源替换成已指定的冻结 SHA；
# 产品、业务断言、原生 CLI、Electron 驱动和假 API 逻辑全部保持原文。
runner = candidate/'workbench/tests/run_t108_native_e2e.py'
text = runner.read_text(encoding='utf-8')
old = "        revision=run(['git','rev-parse','HEAD']).strip()"
assert text.count(old) == 1
runner.write_text(text.replace(old, '        revision='+repr(revision)), encoding='utf-8')
(root/'manager-home').mkdir()
env.update(HOME=str(root/'manager-home'), TMPDIR='/private/tmp',
           ELECTRON_OVERRIDE_DIST_PATH=str(dist))
command = ['/usr/bin/python3', '-B', str(runner), '--summary', str(root/'native-e2e.json'),
           '--electron-dist', str(dist)]
metadata = {'candidate': revision, 'source': str(source), 'archive_copy': str(candidate),
            'command': command, 'model_calls_expected': 0, 'vendor_calls_expected': 0,
            'harness_change': '仅 git archive 的版本来源；无产品改动；符号链接展开为文件'}
(root/'run.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
# 先跑当前候选的信号合同；完整入口仍必须独立通过。
focused = ['node', str(candidate/'workbench/tests/test_t108_questions.mjs'), str(root/'questions.json')]
with (root/'questions.stdout').open('xb') as out, (root/'questions.stderr').open('xb') as err:
    focused_result = subprocess.run(focused, cwd=candidate, env=env, stdout=out, stderr=err, timeout=60)
assert focused_result.returncode == 0
with (root/'stdout.txt').open('xb') as out, (root/'stderr.txt').open('xb') as err:
    completed = subprocess.run(command, cwd=candidate, env=env, stdout=out, stderr=err, timeout=600)
metadata['exit'] = completed.returncode
summary = json.loads((root/'native-e2e.json').read_text(encoding='utf-8'))
metadata['status'] = summary['status']
metadata['model_calls'] = summary['model_calls']
metadata['vendor_calls'] = summary['vendor_calls']
(root/'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False))
assert completed.returncode == 0 and summary['status'] == 'PASS'
assert summary['model_calls'] == 0 and summary['vendor_calls'] == 0
PY
