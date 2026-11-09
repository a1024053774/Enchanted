# T-262 attempt 4 恢复交付记录（2026-11-09）

原字节恢复 PASS；T-262 整体 INCOMPLETE。本次按主控 #137 的 v4 任务卡，从 a3 交付 `e18e5207de94fd6ea56be9868de45c18c1f2991f` 恢复三份产品／测试文件和全部旧 worker 证据，只新增本说明。原完成条件、新候选的限定补证复核与门禁集成仍由执行主控安排。

**Works**：开始时 worktree 干净，HEAD 等于任务卡 base；三个路径相对共同祖先 B 没有他人变更。恢复后逐文件直接比较原始字节：三份产品／测试与 e18e、旧 C 均相同；123 份 worker 文件与 e18e 相同，其中旧 C 的 54 份文件也保持原样。恢复共 126 个文件、1,069,507 字节，未计算哈希。

**No regression**：产品和测试沿用原交付，无重新实现、预期调整或测试放宽；新增内容只有本中文说明。原始失败、审查员 Git 启动失败、两阶段键盘记录均保留。本次没有运行业务完成条件、全仓测试、ps、Electron 窗口或构建；历史 38 项绿态及变异结果属于下文标明的旧候选外部执行证据。

**Risk / undo**：本次候选仍需门禁验收与唯一一次限定补证复核，不能据字节一致提前宣布可集成。主仓库的部分旧证据原路径已经缺失，本次可用来源是 e18e 中的归档副本；地图检查仍有一处卡外 README stale，详见下文。需要撤回时，由执行主控通过正常门禁拒收或另派回退，保留旧交付及失败记录。未 push；额外可写目录为 `[]`，额外目录改动为 `[]`。

## 身份与恢复范围

| 字段 | 值 |
| --- | --- |
| task | `a2a+T-262-1` |
| attempt | `19862f27-ec13-420c-811d-8d2ae99b4fed` |
| session | `7b3bb869-49f9-4b60-a78a-029b4f6ea191` |
| fence / spec_rev | `4` / `4` |
| thread | `8165fa40-76d2-469a-ab76-2e952d848fc6` |
| base | `62faa87b9424e48a4739920b53920d111a057486` |
| B（共同祖先） | `3647a07bdacb514cdc303965be8c52b84d9356b2` |
| C（原产品） | `6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5` |
| S（本次恢复源，a3 交付） | `e18e5207de94fd6ea56be9868de45c18c1f2991f` |

| 产品／测试路径 | 恢复字节数 | base 与 B | 恢复后与 C、S |
| --- | ---: | --- | --- |
| `workbench/app/RecordsPage.tsx` | 12,824 | 相同 | 相同 |
| `workbench/app/records.css` | 7,240 | 相同 | 相同 |
| `workbench/tests/test_t262_records_e2e.py` | 43,568 | 两版均不存在 | 相同 |

`worker/` 的 123 份旧文件共 1,005,875 字节，包含完整 `recovery-a3/`；本次未改写它们的状态、时间、失败、来源或提交身份。新提交完整版本由 Git 提交与本次 submit 请求绑定，`A2A-*` 尾注交由钩子生成。

已读取 AGENTS、REVIEW、项目地图、术语表、intent 和本票，核对了行为与调用者：`renderer.tsx` 按项目挂载 RecordsPage；RecordsPage 合并两类记录、统一筛选与排序，并用活动请求标记阻止迟到结果覆盖；页面经 preload 的 `records`／`receipts` 到 main 的 `a2a:records`／`a2a:receipts`，再到后台 `user_input_records`／`relay_receipts`。CSS 作用域和现有 E2E 入口沿用 C，没有修改调用链、后台或冻结验收文件。

## 原证据及本次可用来源

历史原件根目录为 `/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/`。本次恢复的可用文本在 [recovery-a3/sources](../recovery-a3/sources/)，逐项原路径及旧比对结果见 [provenance.json](../recovery-a3/provenance.json)。下列结论来自读取这些归档内容，不是本 worker 重跑所得，也不是本次正式 reviewer verdict。

| 材料 | 可核对事实与执行归属 |
| --- | --- |
| [behavior-results-08.json](../recovery-a3/sources/controller/behavior-results-08.json) 及同目录原报告 | 执行主控外部执行：父版在倒序和双区任务筛选上出现业务红态；green-outside-04 为 38 项 PASS；原四变异命中业务断言。green-outside-02 的 INCOMPLETE 和 green-outside-03 的 FAIL 保留。 |
| [审查员原运行](../recovery-a3/sources/review-01/mutation-results.json)、[candidate.stderr](../recovery-a3/sources/review-01/candidate.stderr) 及四份 `.diff` | 独立审查员 `4900e31c-18a1-4e29-b460-b064605abcd3` 构造补丁。原副本缺 `.git`，执行在 `git rev-parse HEAD` 退出 128，没有到达业务断言；原始结果保持 INCOMPLETE。 |
| [external-01/summary.json](../recovery-a3/sources/review-01/external-01/summary.json) 及五份 JSON | **独立审查员构造，主控外部执行**：C checkout 上正确候选 38 项 PASS／退出 0；四个错误实现均 FAIL／退出 1，原 JSON 的 failed 含对应业务断言，error 为 null。没有把启动失败算作变异检出。 |
| [KEYBOARD-COMPLETION.md](../recovery-a3/sources/controller-test/KEYBOARD-COMPLETION.md) 与四份 `keyboard-*.txt` | 主控在已打包 C 的真实 Test 窗口使用原生 typeahead、Tab、Enter：T-1 输入 4／回执 3；worker-one 为 3／3；T-3 为 0／1；完整回执展开含 `r-only`。本次读到的 AX 文本与这些数字一致。 |
| [CUA-RESULTS.md](../recovery-a3/sources/controller-test/CUA-RESULTS.md) | 初次点击／方向键等操作未完成，原 INCOMPLETE 保留。后续键盘补证没有证明原菜单展开路径成功。 |
| [source-binding.json](../recovery-a3/sources/controller-test/source-binding.json)、[package-command.json](../recovery-a3/sources/controller-test/package-command.json) | 历史打包材料绑定 C。本次独立核对当前三文件与 C、S 的字节，并确认归档的审查员 `RecordsPage.original.tsx` 与当前页面相同。当前没有再次启动该包。 |

四个审查变异对应的独立预期：`no-sort` →「每区最新在前，同时间按记录身份稳定排列」；`receipt-task` →「任务筛选同时约束双区」；`ignore-session` →「同一 launch 的输入与回执一起筛选」；`no-full-receipt` →「完整回执与原始存储一致」。原执行命令与清理记录见上述 summary 和 [run_external_mutations.py](../recovery-a3/sources/review-01/run_external_mutations.py)。本次未执行该脚本。

原 review cancelled，额度前草稿不是正式结论；状态滞留由 T-264 跟踪。本次没有扩大为整体盲审或另起 reviewer。

## a3 未进入业务检查的记录

本次只读读取了下列主仓库文件，未覆盖：

- [verify-v3-01.json](/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/verify-v3-01.json)：退出 1，`feedback_identity_unknown`。
- [verify-v3-02.json](/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/verify-v3-02.json)：退出 1，`repair_submission_required`；保留 e18e 前次 completion 输出 `status=INCOMPLETE`、`checks=[]`、`failed=[]`，错误是 `daemon start deadline`，另有夹具后台残留的 cleanup_error。
- [verification-startup-cleanup-01.json](/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/verification-startup-cleanup-01.json)：主控核对 PID 61028 所属自有夹具后发送 SIGTERM，记录 `process_gone=true`、`remaining=[]`，删除前记录 133 文件／2,571,542 字节。

任务卡说明此轮处于文稿权限等待；上述测试原始输出直接证明业务断言没有运行。这里按环境未就绪记 INCOMPLETE，不归为产品业务红态，也不因清理完成宣称验收通过。

## 本次核对与缺口

本次恢复核对只读取 Git 对象和本地文件字节，不计算指纹。以下命令从本 worktree 根目录运行，可复现产品一致性、123 份旧 worker 文件保留及路径范围核对：

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess
B = '3647a07bdacb514cdc303965be8c52b84d9356b2'
C = '6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5'
S = 'e18e5207de94fd6ea56be9868de45c18c1f2991f'
BASE = '62faa87b9424e48a4739920b53920d111a057486'
products = ['workbench/app/RecordsPage.tsx', 'workbench/app/records.css',
            'workbench/tests/test_t262_records_e2e.py']
prefix = 'evidence/2026-11-08-batch34/T-262/worker/'
def git(*args):
    return subprocess.check_output(['git', *args])
def listed(rev, *paths):
    return git('ls-tree', '-r', '--name-only', rev, '--', *paths).decode().splitlines()
assert not git('diff', B, BASE, '--', *products)
for path in products:
    assert Path(path).read_bytes() == git('show', C + ':' + path) == git('show', S + ':' + path)
old = listed(S, prefix)
assert len(old) == 123
assert sum(len(Path(p).read_bytes()) for p in old) == 1005875
for path in old:
    assert Path(path).read_bytes() == git('show', S + ':' + path), path
for path in listed(C, prefix):
    assert Path(path).read_bytes() == git('show', C + ':' + path), path
actual = {str(p) for p in Path(prefix).rglob('*') if p.is_file()}
assert actual - set(old) == {prefix + 'recovery-a4/RESULTS.md'}
changed = git('diff', '--name-only', BASE).decode().splitlines()
untracked = git('ls-files', '--others', '--exclude-standard').decode().splitlines()
assert all(p in products or p.startswith(prefix) for p in changed + untracked)
print('PASS: 三份产品、123 份旧证据原字节一致；新增仅 recovery-a4/RESULTS.md；变更均在卡内')
PY
git diff --check -- workbench/app/RecordsPage.tsx workbench/app/records.css workbench/tests/test_t262_records_e2e.py
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

恢复时的逐字节检查退出 0，产品 diff 检查退出 0。新增说明按 UTF-8、无 BOM 保存并回读；历史文件不改编码或空白。暂存核对使用同一字节标准，并对产品、测试及本说明运行 `git diff --cached --check`，不清理旧证据原有空白。

补充检查主仓库原路径时，读取 `recovery-a3/provenance.json` 的 60 个 `copied.source` 和 3 个 `green04_snapshot_comparisons.snapshot`，按 `Path.is_file()` 检查后直接比对；该命令退出 1，`assert not missing and not mismatch` 抛出 AssertionError，missing 为清单中的全部 63 条路径，mismatch 为空。随后只读 `Path.stat()` 确认这 63 条均为 FileNotFoundError，未发现其他异常。**原路径复核 INCOMPLETE**，不能把 a3 的原件核对结果冒充本次重新完成。已恢复的 S 归档副本逐字节核对 PASS；副本与原件之间的历史来源声明仍由 a3 provenance 记录。本次没有补造原件、改变证据或因目录缺失重跑业务。

此新发现已按同一入口排队非阻塞 issue，request_id 为 `5dd612d9-ca43-44bc-b82c-e9284fdd4ae3`，路径 `/private/tmp/a2a-requests-Z05A3g/5dd612d9-ca43-44bc-b82c-e9284fdd4ae3.json`；返回 `queued=true, delivered=false`，尚非主控答复。建议限定复核读取本候选的 `recovery-a3/sources/` 和 S 提交。没有重复等待既有权限问题。

project-map 开始时退出 0：Problems 0 / Stale 0。恢复后退出 1，输出摘要为：

```text
Problems (0):
Stale living docs (1):
  - workbench/README.md: uncommitted changes to covered files without a doc edit: workbench/app/RecordsPage.tsx, workbench/app/records.css
Frontier (9): T-235、T-249、T-255、T-256、T-260、T-261、T-262、T-264、T-265
```

README 与地图不在本卡写入范围；此项与 a3 已知交接一致，由执行主控集成时处理，本次未重复 issue 或修改卡外路径，未把地图状态写为 PASS。

## 交付与后续职责

本次未运行产品测试：v4 卡明确要求不重跑 Electron、ps 或构建。执行主控在本次 merge candidate 根目录、按原分工从受管沙箱外执行的准确完成条件仍为：

```sh
/usr/bin/python3 workbench/tests/test_t262_records_e2e.py
```

独立 reviewer 按卡读三文件、调用链、完成条件与原四变异，独立判断外部业务红态、键盘证据及新候选字节是否补齐原缺口；需要新增真实执行时保存补丁、独立预期和准确命令，执行主控只做外部执行并原样返回，不由 worker 预判可合并。

worker 完成 Git 提交后，用本次 attempt/session/fence/spec_rev 显式 submit 一次；提交请求与 issue 请求都只留在本 attempt 请求目录，不进入 Git。`queued=true` 表示请求已排队，不代表门禁验收或集成通过。
