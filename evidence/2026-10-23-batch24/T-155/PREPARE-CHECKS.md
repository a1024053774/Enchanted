# 准备阶段检查（2026-10-23）

task：T-155-1；attempt：a1；worker：b24-t155。产品基线：`f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697`。

整体状态：INCOMPLETE。此文件只证明准备阶段，不能用作真实使用验收结果。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 项目地图 | PASS | session 开始及交接前 `project_map.py status --root .`：Problems 0、Stale living docs 0，frontier 为 T-155 |
| 前置票 | PASS | T-150～T-154 的 frontmatter 均为 `status: closed` |
| 起点与范围 | PASS | 分支 `exec/t155`，起点 `f3412fb4a`；开始时 worktree 干净；修改仅在本票 evidence 目录 |
| Python 语法与帮助入口 | PASS | `ast.parse` 成功；`python3 .../app_lifecycle.py --help` 退出 0 |
| Shell 语法 | PASS | `sh -n .../START-APP.sh .../STOP-APP.sh` 退出 0 |
| UTF-8 回读 | PASS | 本轮四个新文件 UTF-8 解码成功；源码与中文说明已回读 |
| 一次性仓库建法 | PASS | `python3 evidence/2026-10-23-batch24/T-155/app_lifecycle.py prepare` 退出 0 |
| 路径检查 | PASS | `load()` 验证实例归属与 repo、state、user-data、socket、credential 路径；`SOURCE` 为本 worktree |
| 产品未改 | PASS | `git diff --quiet f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697 -- workbench` 退出 0 |
| 应用构建、启动、停止、重开 | INCOMPLETE | 未执行，按派发要求交主控沙箱外运行 |
| Computer Use 与模型回合 | INCOMPLETE | 本阶段均为 0；等窗口就绪后开始 |

实际准备实例：`/private/tmp/t155-dogfood-9lz6vh2i`；种子仓库：该目录下 `demo-repo/`。目录完整保留，未创建 daemon socket 或操作员凭据，未启动应用。主控可直接对该路径执行 `START-APP.sh <路径>`，也可无参数创建另一个全新实例。

种子提交：`40b5320b5ac718d85a9af23960b32a25d797ac23`（初始化一次性食材清单）。`git status --short` 输出为空，`git remote -v` 输出为空。只含 README 与五项食材 JSON，不含业务结果、登录副本或测试应用数据。

Python `3.9.6`、Node `v26.5.0`；现有 `workbench/node_modules` 已存在。本轮没有安装依赖、构建产品、读取认证内容、申请代批或操作用户应用。

重放准备检查使用仓库根目录为 cwd：

```sh
python3 evidence/2026-10-23-batch24/T-155/app_lifecycle.py --help
sh -n evidence/2026-10-23-batch24/T-155/START-APP.sh evidence/2026-10-23-batch24/T-155/STOP-APP.sh
python3 evidence/2026-10-23-batch24/T-155/app_lifecycle.py prepare
git diff --check
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```
