# T-201 非 Git 目录的侧栏状态露出原始报错（2026-10-27）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，无问题，见 `review-1.md`。审查在 LIMITATIONS 里提到：没有 `.git` 的目录若位于上层 Git 仓库之内，git 会报上层仓库的状态；这不属本票的“not a git repository”场景，未改。

## 做法

`workbench/src/sidebar.ts` 的 `gitFacts`：git 读状态失败时，若目录存在、目录里没有 `.git`、且 git 报 `not a git repository`，状态写“不是 Git 仓库”；其余照旧写“无法读取 Git：”加原因。

只看报错文字不够：实测 git 对 HEAD 写坏的仓库、`.git` 不可读的仓库也报 `not a git repository`（索引损坏、目录不存在则是别的报错）。所以以“没有 `.git`”为准，坏掉的真仓库仍显示原因。

## 测试

`workbench/tests/test_t201_non_git_status_e2e.py`：真实后台、git 与 Electron 窗口，零模型调用。打开普通目录、HEAD 写坏的仓库、打开后被删的仓库。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | `--revision a3ae46cf2` | 失败：普通目录显示 `无法读取 Git：Error: Command failed: git -C … fatal: not a git repository …` |
| `green-1.json` | 修后 | 通过：普通目录“不是 Git 仓库”；坏仓库仍是原始原因；被删的“目录不存在”；正常仓库 `main · 无上游` |
| `mutant-message-only.json` | 只看报错文字 | 只在“坏仓库仍显示原因”失败 |

截图见 `screenshots.archive.json`（外置盘）。复现：`python3 test_t201_non_git_status_e2e.py --summary <新路径> [--revision a3ae46cf2 | --mutant message-only]`
