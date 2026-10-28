# T-201 独立审查报告

本审查基于 [`/private/tmp/t-201-review/BRIEF.md`](file:///private/tmp/t-201-review/BRIEF.md) 的要求，以只读方式（仅使用文件读取，未执行任何 shell 命令、未修改任何文件、未启动后台或应用进程）对候选改动 [`change.diff`](file:///private/tmp/t-201-review/change.diff)、相关代码、测试及运行证据进行了独立审查。

---

## 1. 根因层、边界与设计完整性核对

1. **修复位置与根因分析**：
   - **根因**：工作台侧栏的项目状态统一由 [`workbench/src/sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L89-L105) 中的 [`gitFacts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L89-L105) 函数提供。原先在执行 `git -C <repo> status --porcelain=v2 ...` 失败时，`catch` 块直接将原始进程报错格式化输出（`'无法读取 Git：' + String(error)`），导致普通非 Git 目录露出底层命令调用细节（如 `Error: Command failed: git -C ... status ... fatal: not a git repository ...`）。
   - **修复**：在 [`gitFacts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L101-L102) 内部直接通过 `!existsSync(join(repo, '.git')) && existsSync(repo) && String((error as { stderr?: unknown }).stderr).includes('not a git repository')` 区分“本身无 `.git` 的合法普通目录”与“真正损坏的 Git 仓库/其他错误”，直接返回 `{ branch: null, upstream: null, ahead: null, behind: null, error: '不是 Git 仓库' }`。修改处于事实产生的最底层单一来源，属于最小充分的根因修复。

2. **“不做”项约束核对**：
   - 票 [`.project-map/tickets/T-201-non-git-project-status.md`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-201-non-git-project-status.md#L27-L30) 中声明的“不做”为：
     > 禁止添加非 Git 目录；在非 Git 目录里建任务。
   - 改动仅调整了侧栏状态读取时的报错格式化分支与配套 E2E 验证测试，未向项目打开流程引入 Git 仓库强制校验，亦未触碰任务创建逻辑，完全遵守了“不做”约束。

3. **异常吞噬、兼容分支与平行路径核对**：
   - **无异常吞噬**：判断条件显式要求同时满足“不存在 `.git`”、“目录本身存在”及“git stderr 包含 `not a git repository`”。对于 `.git/HEAD` 损坏但存在 `.git` 的仓库，由于 `!existsSync(...)` 为 `false`，将继续穿透至兜底的 `无法读取 Git：...` 分支保留原始报错；对于目录已被删除的情况（`existsSync(repo)` 为 `false`），亦不会命中该分支；遇到命令超时、权限异常或 Git 二进制缺失等错误，同样如实保留原始报错。
   - **无兼容分支或平行路径**：未引入多余的 wrapper、重试策略或回退逻辑。

---

## 2. 文案与代码事实一致性核对

逐项核对相关文档与代码行为：

1. **[`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L400)**：
   > 目录里没有 `.git` 且 git 说不是仓库时显示“不是 Git 仓库”，有 `.git` 却读不了（例如 HEAD 坏了）照旧显示“无法读取 Git”和原因（T-201）。
   - **事实核对**：与 [`workbench/src/sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L101-L103) 代码逻辑完全一致。当 `git.error` 为 `'不是 Git 仓库'` 时，[`workbench/app/renderer.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L73) 的 `projectGit` 直接显示该错误文本；当 `git.error` 为 `'无法读取 Git：...'` 时，界面同样如实呈现原因。

2. **[`evidence/2026-10-27-batch28/T-201/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/RESULTS.md#L7-L9)**：
   > `workbench/src/sidebar.ts` 的 `gitFacts`：git 读状态失败时，若目录存在、目录里没有 `.git`、且 git 报 `not a git repository`，状态写“不是 Git 仓库”；其余照旧写“无法读取 Git：”加原因。
   > 只看报错文字不够：实测 git 对 HEAD 写坏的仓库、`.git` 不可读的仓库也报 `not a git repository`（索引损坏、目录不存在则是别的报错）。所以以“没有 `.git`”为准，坏掉的真仓库仍显示原因。
   - **事实核对**：准确反映了代码为什么要同时检查 `!existsSync(join(repo, '.git'))` 与 `stderr`，事实与代码行为一致。

3. **代码注释与测试意图**：
   - [`workbench/src/sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L99-L100) 注释与 [`workbench/tests/test_t201_non_git_status_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t201_non_git_status_e2e.py#L4-L15) 文档字符串中的失败场景定义、变异方式均与代码实现及运行证据一致。

---

## 3. 测试与证据有效性核对

核对测试脚本 [`workbench/tests/test_t201_non_git_status_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t201_non_git_status_e2e.py) 及三份运行报告：

1. **测试设计与预期来源**：
   - 测试基于真实 Electron 窗口、后台常驻守护进程与真实 Git 命令，通过 CDP 读取 DOM 中的 `[data-project-git]`，无任何模型调用。
   - 预期直接来自需求（T-201 与试用发现 3）：普通目录显示“不是 Git 仓库”且不得包含 `Command failed`、`fatal:`、`git -C` 等底层报错；坏 HEAD 仓库保留“无法读取 Git”及底层原因；已删除目录显示“目录不存在”；正常仓库保持分支状态。预期非循环印证实现输出。

2. **修前红态核对（[`red-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/red-1.json)）**：
   - 运行参数：`--revision a3ae46cf2`。
   - 运行状态：`FAIL`。
   - 失败断言：`plain_says_not_git` 与 `plain_hides_raw_error` 失败。
   - 实际捕获细节：侧栏读取到完整底层报错 `无法读取 Git：Error: Command failed: git -C /private/tmp/t201-nhz9l6io/plain-dir status --porcelain=v2 --branch --untracked-files=no\nfatal: not a git repository (or any of the parent directories): .git\n`。这确切复现了试用时发现的问题。

3. **修后绿态核对（[`green-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/green-1.json)）**：
   - 运行状态：`PASS`。
   - 检查项全通：
     - `plain_says_not_git`: `"不是 Git 仓库"`
     - `plain_hides_raw_error`: `"不是 Git 仓库"`
     - `broken_repo_shows_reason`: `"无法读取 Git：Error: Command failed: ... fatal: not a git repository ..."`
     - `gone_repo_shows_missing`: `"目录不存在"`
     - `normal_repo_unchanged`: `"main · 无上游"`

4. **变异体反例敏感度核对（[`mutant-message-only.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/mutant-message-only.json)）**：
   - 变异操作：移除 `!existsSync(join(repo, '.git')) &&`，仅根据错误文本判断。
   - 运行状态：`FAIL`。
   - 失败断言：`broken_repo_shows_reason`。
   - 实际捕获细节：损坏的 Git 仓库被误判为 `"不是 Git 仓库"`。此反例证明了 `.git` 存在性检查的不可或缺性。

5. **表格与 JSON 一致性**：
   - [`evidence/2026-10-27-batch28/T-201/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/RESULTS.md#L15-L20) 中的表格数据与 `red-1.json`、`green-1.json`、`mutant-message-only.json` 完全一致。
   - 截图归档清单 [`screenshots.archive.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/screenshots.archive.json) 符合 T-088 规范，且包含重现命令与原始大小。

---

## 4. 票面验收条件逐条核对

| 验收条件 | 证据 | 核对结果 |
| --- | --- | --- |
| 1. 修前版本经真实入口：非 Git 目录的侧栏状态含原始命令报错；修后显示“不是 Git 仓库”之类的一句话。 | [`red-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/red-1.json) 记录修前真实报错；[`green-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/green-1.json) 记录修后显示“不是 Git 仓库”。 | **PASS** |
| 2. Git 仓库读取真的出错时（例如目录被删）仍显示原因，不被这句话盖掉。 | [`green-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/green-1.json) 记录损坏仓库如实报错、被删仓库显示“目录不存在”；[`mutant-message-only.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-201/mutant-message-only.json) 证明反例。 | **PASS** |
| 3. 通用：先在真实入口留红态再修根因；不写 `~/.claude`、`~/.codex` 等全局配置；独立审查。 | 红态归档完备；diff 仅涉及项目内代码与测试；本报告为独立审查。 | **PASS** |

---

## 问题清单

经深度代码比对与异常边界分析，未发现 P1、P2 或 P3 缺陷。

---

## 结论

**`可合并`**

---

## LIMITATIONS

1. **父级目录为 Git 仓库的普通子目录**：若用户添加的项目目录本身没有 `.git`，但其位于某个父级 Git 仓库的工作树内部，Git 命令默认会向上查找并返回父仓库的分支状态，而不会报告“not a git repository”。此行为属于 Git 原生向上搜寻工作区的机制，非 T-201（针对 Git 抛出“not a git repository”场景）所辖范围。
2. **只读审查环境限制**：本次审查严格遵循独立审查员只读约束，仅通过静态文件读取、代码比对、差异审查与既有 JSON/文档证据比对进行验证，未在本轮会话中重新执行 Python 测试脚本或拉起 Electron 图形界面。相关执行证据的真实性依赖已归档的 `red-1.json`、`green-1.json`、`mutant-message-only.json` 及其对应的环境回放命令。