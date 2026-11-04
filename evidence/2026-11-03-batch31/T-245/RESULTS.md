# T-245 结果（2026-11-03）

结论：**PASS**（第三轮审查 `../review-3/REPORT.md` 无阻塞；只证明本机 Claude Code 2.1.317 与该夹具场景）。修后 `test_t124_controller_e2e.py` PASS，夹具路径下没有进程，也没有装官方插件市场；修前与反事实都装上了。

## 触发条件与依据

依据是本机 Claude Code 2.1.317（`~/.local/share/claude/versions/2.1.317`）里的代码（官方插件市场自动安装 `official-marketplace-check`），按顺序：

1. 读全局配置（HOME 下的 `.claude.json`）：`officialMarketplaceAutoInstallAttempted` 为真且已装过，或失败原因是 `policy_blocked`，就跳过。
2. 环境变量 `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` 有值也跳过，并把 `policy_blocked` 写回全局配置。
3. 否则从 `downloads.claude.ai` 下载（10 秒超时）。
4. 下载失败才走 git：先跑 `ssh -T -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=yes git@github.com`，回答里有 `successfully authenticated` 就用 `git@github.com:anthropics/claude-plugins-official.git` 克隆，否则用 HTTPS。

ssh 按账户主目录读 `~/.ssh` 与 `~/.ssh/config`，不看 HOME，所以第 4 步用的是用户真实的 ssh 身份：只读认证，并克隆一个公开仓库到夹具 HOME。T-243 里的两次残留就是第 4 步（下载失败时）；本票三次运行下载都成功，装上的是第 3 步的结果。

t124 里运行真实 Claude 的是受管 worker 与监视器。它们的环境按白名单传递（`panes.ts` 的 worker 环境），并带 `--setting-sources ""`，所以只设环境变量或写夹具的 `settings.json` 到不了它们；它们都读 HOME 下的 `.claude.json`（夹具本来就在这里写 `hasCompletedOnboarding`）。

## 改动

- `workbench/tests/scripted_claude.py`：`MARKETPLACE_SKIPPED`，即 Claude 在第 2 步写下的三项；`stop_fixture_core` 收尾时，夹具目录或其下一级目录里出现 `.claude/plugins/marketplaces` 就失败（原生 CLI 不锁版本，字段一变会直接报出来）。
- 29 个写夹具 `.claude.json` 的测试与探针都并入 `MARKETPLACE_SKIPPED`。没改：`test_t093_*`、`t093_fake_login_peer.py`、`probe_t093_normal_login.py`（核对登录流程写下的确切内容，或是产品登录路径）。

## 证据

| 文件 | 内容 |
| --- | --- |
| `red-t124.json`、`red-t124.log` | 修前（只加收尾检查）：INCOMPLETE，夹具 HOME 下有 `.claude/plugins/marketplaces` |
| `green-t124.json`、`green-t124.log` | 修后：PASS，无残留 |
| `reverted-t124.json`、`reverted-t124.log` | 反事实：`MARKETPLACE_SKIPPED` 临时置空，又装上了；之后恢复 |

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t124_controller_e2e.py --summary <新文件>.json
```

## 范围外

产品里 Claude worker 用用户真实的 HOME（那里已装过），不受影响。登录流程的临时 HOME（`claudeLogin.ts`）与 `claudeLaunch.ts` 的 normal 分支理论上也会触发，未处理。
