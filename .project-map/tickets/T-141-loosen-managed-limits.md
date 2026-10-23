---
id: T-141
title: 放宽受管会话限制：网络全开、不再 strict-mcp-config、Codex 与用户自己的配置一致，文件写入范围为唯一硬边界
type: build
status: open
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

- [ ] 真实 worker（Claude 与 Codex 各一）能访问外网（例如 curl 一个公开地址）并成功。
- [ ] Claude worker 能使用用户 Claude 里配置的 MCP 工具之一（实测）。
- [ ] 真实 Codex worker 遇到要审批的动作时：没有卡在审批上，经 `issue` 上报，问题面板出现，执行主控回复后 worker 收到并继续。
- [ ] 写入范围外的路径仍写失败（红态保留）。
- [ ] 启动 argv 记录完整，门禁不按这些参数拒绝。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

