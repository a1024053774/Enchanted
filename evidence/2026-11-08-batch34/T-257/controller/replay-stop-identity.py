"""主控诊断：从已提交开发测试移除票据未要求的 Stop 标志前提。

不改 worker 文件、冻结验收或产品源码。仅把第二个 Stop 的识别改为同 turn 且
发生在续跑 UPS 之后；这是票据要求的身份与顺序，不要求某个 stop_hook_active 值。
原测试版本及首次 INCOMPLETE 输出均保留。本诊断不是门禁的完成条件通过证明。
"""
from pathlib import Path
import subprocess
import sys

root = Path('/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-257-1-a1')
relative = 'workbench/tests/test_t257_codex_stop_continuation_e2e.py'
source = subprocess.check_output(
    ['git', 'show', '1acebc00d617a04317164370dcfb21c1b21b3308:' + relative], cwd=root, text=True)
before = "row.get('turn') == first_turn and row.get('stop_hook_active') is True"
after = "row.get('turn') == first_turn and row['seq'] > starts[-1]['seq']"
assert source.count(before) == 1, '已提交测试的诊断锚点必须唯一'
sys.path.insert(0, str(root / 'workbench/tests'))
sys.argv[0] = str(root / relative)
exec(compile(source.replace(before, after), str(root / relative), 'exec'),
     {'__name__': '__main__', '__file__': str(root / relative)})
