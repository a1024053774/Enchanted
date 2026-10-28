# T-200 中文目录名的项目显示为 project（2026-10-27）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-1.md`；一条 P3：送审 diff 里 `renderer.tsx` 混有 T-202、T-204 的改动，提交时注意范围（三票同批提交）。

## 做法

项目号与生成规则不变（门禁只认 `[A-Za-z0-9_.-]`，中文目录的项目号是 `project`）。`workbench/app/renderer.tsx` 加 `projectName`：按项目登记的目录取最后一段作为名字；另有已打开项目同名时，在名字后带上项目号（`我的 项目 · project`）。用在侧栏、窗口标题、任务眉标、角色申请横幅三处文案、“在 X 里开一个终端”、移除项目对话框、通知卡片、流程页。侧栏标题的 `title` 属性仍是项目号。

## 测试

`workbench/tests/test_t200_project_names_e2e.py`：真实后台与 Electron 窗口，零模型调用。打开 `我的 项目`、`另一个项目` 和另一处的同名 `我的 项目`，并让第一个项目的终端发一个待批的角色申请。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1-weak-banner-check.json` | `--revision a3ae46cf2` | 3 项失败；横幅那项写错了（修前也算通过），改测试后保留为记录 |
| `red-2.json` | `--revision a3ae46cf2` | 4 项失败：侧栏、同名区分、横幅、标题都显示 project / project-2 / project-3 |
| `green-1.json` | 修后 | 7 项通过；项目号仍是 project、project-2、project-3，ASCII 项目 demo 不变 |
| `mutant-no-twin-suffix.json` | 同名不带项目号 | 只在“同名可区分”失败 |

截图见 `screenshots.archive.json`（外置盘）。复现：`python3 test_t200_project_names_e2e.py --summary <新路径> [--revision a3ae46cf2 | --mutant no-twin-suffix]`

## 没做

主进程发出的系统通知、`a2a` 回执里的项目仍是项目号（命令与门禁的标识）。
