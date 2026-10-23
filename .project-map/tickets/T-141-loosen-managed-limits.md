---
id: T-141
title: 放宽受管会话限制：网络全开、不再 strict-mcp-config、Codex 与用户自己的配置一致，文件写入范围为唯一硬边界
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 在本 session 逐字（第 4 条）：“4. 网络全开,去掉--strict-mcp-config,codex 和用户自己的一致,文件写入范围当硬边界”

现状（`src/panes.ts`、`claudeLaunch.ts`）：Codex `network_access=false`、`network_proxy=false`、`-a never`、`projects=untrusted`；Claude `--strict-mcp-config`、`--setting-sources ""`、沙箱默认网络隔离。

改为：
1. 网络全开：Codex 不再设 `network_access=false`/`network_proxy=false`；Claude 沙箱放开网络（核对沙箱设置里实际要配什么，以实测为准）。
2. 去掉 Claude worker/reviewer 的 `--strict-mcp-config`。
3. Codex 与用户自己的 `~/.codex` 一致：不再用 `-c` 覆盖信任、沙箱细节与工具；只保留写入范围这一个沙箱约束。**`-a never` 保留**（用户 2026-10-23：“-a never 应该可以吧,让他通过我们软件的问题上报界面来上报,然后执行主控可以通过这个接口来回复他们”）：需要审批或判断的事，worker 用 `issue` 上报，出现在问题面板，执行主控用现有的 `answer`/`disposition` 接口回复；worker 不会因审批卡住。验收里要覆盖这条路径。
4. 文件写入范围是硬边界：worktree、请求目录、T-140 的额外目录；Git 公共目录禁写与两条 git 例外保持。
5. 门禁（路径边界、验收文件不可改、红态、独立审查）不变。

同步：AGENTS.md 里“worker 沙箱关网络”“Codex untrusted”相关条目与 T-075 的 socket 放行说明，须由构思主控在本 ticket 关闭时核对更新。

## Acceptance

- [x] 真实 worker（Claude 与 Codex 各一）能访问外网（例如 curl 一个公开地址）并成功。
- [x] Claude worker 能使用用户 Claude 里配置的 MCP 工具之一（实测）。
- [x] 真实 Codex worker 遇到要审批的动作时：没有卡在审批上，经 `issue` 上报，问题面板出现，执行主控回复后 worker 收到并继续。
- [x] 写入范围外的路径仍写失败（红态保留）。
- [x] 启动 argv 记录完整，门禁不按这些参数拒绝。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-23 关闭，PASS。

- 用户裁定：MCP 选 A、Codex 信任提示“不自动选”（20261023T125315Z ideation answer）；T-127 冲突选 A，只有 Codex 审查员一次性副本仍以 untrusted 打开，worker 与 monitor 沿用用户配置（20261023T151224Z）；授权改受保护 `test_t127_codex_home_e2e.py` 中按“worker 强制 untrusted”写的四处 worker 期望（20261023T153252Z）。执行主控裁定 `test_t140` 只信任其隔离 CODEX_HOME 里它自己创建的 demo 仓库（`evidence/2026-10-23-batch23/T-141/controller-decision.md`）。
- 代码：分支 `exec/t141`（起点 3f8813b0e，交付 65ca19f8b），合并 `1204f2e0e`：网络放开、Claude 不再 strict-mcp-config 而加载用户 MCP（MCP 写入不在写入边界内，README 写明）、Codex 沿用用户配置且 `-a never`、写入范围（worktree 加额外目录）是唯一硬边界，Codex 审查员副本 untrusted 且门禁核对。
- 受保护验收文件：T-127 改授权的四处 worker 期望（三个检查改名在授权内）与变异定位；审查员侧断言全部保留。T-140 只加 demo 仓库信任。
- 验收（执行主控沙箱外，真实原生 CLI 加夹具里的脚本化模型端，没有调用真实模型）：第 5 轮 `outside05-jYDNPNbR` 29 场中 25 场符合预期；第 6 轮 `outside06-pOPgrnDF` 修正 4 场判据（证据读取、按实际拒绝层分类、paused 终态），5 场全部符合预期。覆盖 Claude 与 Codex 外网 curl 成功、Claude 使用用户 MCP、Codex 审批经 issue 上报并在执行主控回复后继续、写入范围外与共享临时目录写失败，红态与四个变异失败。
- 独立审查：agy gemini-3.8-flash-high，PASS（两条 P3：用户 MCP 不受写入沙箱约束；未信任目录需用户自己信任一次，均为已裁定行为）。
- 合并后：回归 05 发现两个测试夹具仍按旧契约写（T-148 修复）；回归 06（b21fcf930）31 项全部通过。还有其他历史测试的断言按旧契约写，T-148 已清点上报（20261023T172046Z），等用户决定。
