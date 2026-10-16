#!/bin/bash
# T-078 冻结候选的沙箱外回归；由执行主控运行，reviewer 不执行。
# 不启动供应商 CLI 或模型，不读取 auth，不修改全局配置。
# 运行时夹具在 /tmp 自建 Git 仓库；其标准测试会提交夹具基线。
# 产品仓库只读；新构建使用标准命令和外置盘新 slot，不复用或替换旧输出。
set -u
TASK_REPO=/Users/luckye/Documents/Code/a2a-wt-t078
TASK_CANDIDATE=7039840565754f7999b27061191b6506e61ef9d2
TASK_FREEZE=4b48664fd689aab8d52a8721098939067928847e
TASK_OUT=$(mktemp -d /private/tmp/t078-pending-review-outside-01.XXXXXX) || exit 1
echo "新输出目录：$TASK_OUT"
TASK_FINAL=0

echo "01 核对冻结版本与源码边界"
python3 -B - "$TASK_REPO" "$TASK_CANDIDATE" "$TASK_FREEZE" <<'PY' >"$TASK_OUT/01-freeze.stdout.txt" 2>"$TASK_OUT/01-freeze.stderr.txt"
import json, subprocess, sys
from pathlib import Path
repo, candidate, freeze = sys.argv[1:]
def git(*argv):
    return subprocess.check_output(['git', *argv], cwd=repo, text=True).strip()
assert git('rev-parse', candidate) == candidate
assert git('rev-parse', 'HEAD') == freeze, '冻结记录已变化；停止，不追逐新候选'
paths = ['workbench', 'acceptance', 'scripts', 'fixtures']
assert not git('diff', '--name-only', candidate, freeze, '--', *paths)
assert not git('diff', '--name-only', '--', *paths)
assert not git('diff', '--cached', '--name-only', '--', *paths)
assert Path('/Volumes/WD-Elements').is_mount(), '外置盘未挂载；不回退内置盘'
print(json.dumps({'status':'PASS','candidate':candidate,'freeze':freeze,'source':repo}, ensure_ascii=False))
PY
TASK_RC=$?
echo "$TASK_RC" >"$TASK_OUT/01-freeze.exit-code.txt"
echo "01 退出码：$TASK_RC"
if [ "$TASK_RC" -ne 0 ]; then
  echo "最终退出码：$TASK_RC；输出：$TASK_OUT"
  exit "$TASK_RC"
fi

echo "02 只解出必要源码，建立一次性后端副本"
python3 -B - "$TASK_REPO" "$TASK_CANDIDATE" "$TASK_OUT" <<'PY' >"$TASK_OUT/02-snapshot.stdout.txt" 2>"$TASK_OUT/02-snapshot.stderr.txt"
import io, json, subprocess, sys, tarfile
from pathlib import Path
repo, candidate, output = sys.argv[1:]
root = Path(output) / 'candidate'
root.mkdir()
paths = ['workbench', 'acceptance', 'scripts', 'fixtures']
paths = [p for p in paths if subprocess.run(['git','cat-file','-e',candidate+':'+p],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0]
data = subprocess.check_output(['git','archive',candidate,*paths],cwd=repo)
with tarfile.open(fileobj=io.BytesIO(data)) as archive:
    archive.extractall(root)
(root/'workbench/node_modules').symlink_to(Path(repo)/'workbench/node_modules',target_is_directory=True)
print(json.dumps({'status':'PASS','root':str(root),'paths':paths,'dependencies':'只读复用现有依赖；不安装'},ensure_ascii=False))
PY
TASK_RC=$?
echo "$TASK_RC" >"$TASK_OUT/02-snapshot.exit-code.txt"
echo "02 退出码：$TASK_RC"
if [ "$TASK_RC" -ne 0 ]; then
  echo "最终退出码：$TASK_RC；输出：$TASK_OUT"
  exit "$TASK_RC"
fi

echo "03 真实 Electron、node-pty、worker 收件箱回归（零模型）"
python3 -B - "$TASK_REPO" "$TASK_OUT" <<'PY' >"$TASK_OUT/03-runtime.stdout.txt" 2>"$TASK_OUT/03-runtime.stderr.txt"
import json, os, subprocess, sys, time
from pathlib import Path
repo, output = map(Path, sys.argv[1:])
snapshot = output/'candidate'
env = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
env['PYTHONDONTWRITEBYTECODE'] = '1'
# 前端、驱动和客户端来自已核对的原工作树；后端来自精确候选副本。
# 使用原 source 让夹具读取 Git 版本；不为副本伪造版本或共享 Git 写入口。
argv = [sys.executable,'-B',str(snapshot/'workbench/tests/test_t078_input_entry.py'),
        '--source',str(repo),'--backend-source',str(snapshot),
        '--output',str(output/'worker-inbox'),'--worker-inbox']
record = {'argv':argv,'cwd':str(repo),'status':'INCOMPLETE','real_model_turns':0}
(output/'runtime-command.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
start = time.monotonic()
try:
    response = subprocess.run(argv,cwd=repo,env=env,start_new_session=True,timeout=240)
    record['exit_code'] = response.returncode
    result_path = output/'worker-inbox/results.json'
    result = json.loads(result_path.read_bytes()) if result_path.is_file() else {}
    record['assertions'] = len(result.get('checks',[]))
    passed = response.returncode == 0 and result.get('status') == 'PASS' and bool(result.get('checks')) and all(x.get('status') == 'PASS' for x in result['checks'])
    record['status'] = 'PASS' if passed else 'INCOMPLETE'
except subprocess.TimeoutExpired:
    record.update(exit_code=124,error='硬期限耗尽；保留现场；不自动重试或回收未知进程')
    passed = False
finally:
    record['elapsed_seconds'] = round(time.monotonic()-start,3)
    (output/'runtime-command-result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
sys.exit(0 if passed else record.get('exit_code') or 1)
PY
TASK_RC=$?
echo "$TASK_RC" >"$TASK_OUT/03-runtime.exit-code.txt"
echo "03 退出码：$TASK_RC"
if [ "$TASK_RC" -ne 0 ]; then TASK_FINAL=$TASK_RC; fi

echo "04 复核运行期间冻结对象未变化"
git -C "$TASK_REPO" diff --exit-code "$TASK_CANDIDATE" -- workbench acceptance scripts fixtures >"$TASK_OUT/04-source.stdout.txt" 2>"$TASK_OUT/04-source.stderr.txt"
TASK_RC=$?
echo "$TASK_RC" >"$TASK_OUT/04-source.exit-code.txt"
echo "04 退出码：$TASK_RC"
if [ "$TASK_RC" -ne 0 ]; then TASK_FINAL=$TASK_RC; fi
echo "$TASK_FINAL" >"$TASK_OUT/final.exit-code.txt"
echo "最终退出码：$TASK_FINAL；输出：$TASK_OUT"
exit "$TASK_FINAL"
