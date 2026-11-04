# T-244 结果（2026-11-03）

结论：**PASS**（复审 `../review-3/REREVIEW.md` 无阻塞；并发首次安装只有代码判断）。第二版改为每个固定值装进自己的目录；固定值改变时仍在运行的 core 照样能起新终端，修前（`20f1d8581`）同一场景失败于 `no holder`。

## 原因

开发态（未打包）下，`hcBinary` 每次后台启动都调用 `installHc`，用 `tar -xzf` 把 hc 重新解包到 `state/hc/bin`。文件换成新 inode，mtime 与大小不变（`hc-reinstall-inode.json`：281673966 → 281673971）。core 在后台重启后继续运行，它之后按路径起的 holder 来自新文件，构建号（dev:inode:mtime:size）与 core 不同，于是新开终端失败：`no holder: holder build … differs from core build …`。打包版用固定的已签名文件，不受影响。

## 改动（第二版）

第一版在 `state/hc/bin/release.json` 记固定值，一致就复用；它挡不住“固定值变了、旧 core 还在跑”——新版本照样写到 core 正在用的路径上。审查的两条遗留（并发首次启动、没有端到端改固定值）也出在“同一路径原地重装”上，所以第二版换掉这个做法：

- `workbench/src/hcDistribution.mjs`：`hcInstallName = herdr-core-<版本>-<SHA-256 前 8 位>`。`hcBinary` 先用打包的文件；否则用 `state/hc/<hcInstallName>/herdr-core`，已存在就直接用；不存在才在 `state/hc/.install-*` 临时目录里解包，整个目录一次 `rename` 到位。两个后台同时首次安装时，后到的 `rename` 遇到 ENOTEMPTY/EEXIST 就用先到的那份，临时目录在 `finally` 里删除。已装好的文件从不被改写，所以 core 用的文件身份不变；中途中断只留下临时目录，下次重装。标记文件与大小、mtime 核对都删掉了。
- 旧的 `state/hc/bin` 不删（可能有旧 core 正在用它），写在 `workbench/README.md`。
- 测试辅助：`scripted_claude.py` 的 `hc_installs(state)` 列出所有安装，`hc_binary(state)` 断言至多一份；t212、t228、t230 改用它们。

## 证据

| 文件 | 内容 |
| --- | --- |
| `pin-change-red-head.json`、`.log` | 修前：`test_t244_pin_change_e2e.py --revision 20f1d8581`，固定值改变后新终端失败于 `no holder`（前三项检查通过，说明场景成立） |
| `pin-change-green.json`、`.log` | 修后：七项检查 PASS，两份安装各在自己的目录，core 仍用第一份，第一份的 inode 未变 |
| `regress-t123.json`、`.log` | 修后 `test_t123_project_identity_e2e.py`（后台重启、同一固定值）PASS |
| `regress-t212b/`、`.log` | 修后 `test_t212_hc_boundaries_e2e.py` 五个场景 PASS（含损坏缓存不留安装目录与临时目录） |
| `reverted-t123.json`、`green-t123.json` | 第一版时的反事实与绿态（换回 HEAD 的 `hcDistribution.mjs` 即失败于 `no holder`） |
| `pin-change-green-2.json`、`.log` | 第三轮审查后的代码再跑：PASS |
| `partial-install-red.json`、`partial-install-green.json` | `partial_install_probe.mjs`：目标目录在、不空、缺 `herdr-core` 时，修前返回不存在的路径，修后报 `ENOTEMPTY` |
| `pin-probe.json`、`pin-probe-2.json` | 第一版标记文件的探针，第二版已不适用，保留作记录 |

### 测试本身的失败（保留，不是产品缺陷）

| 文件 | 原因 | 处理 |
| --- | --- | --- |
| `pin-change-harness-exit.*` | 早期版本等待终端退出的断言没有带消息 | 改为按 `live == 0` 等待 |
| `pin-change-harness-sequence.*` | `invalid_window_sequence`：每个窗口各自计输入序号，测试按全局计 | 按窗口计 |
| `pin-change-harness-glob.*` | `hc/*/herdr-core` 也匹配到 `hc/state/herdr-core` | 改为 `hc/herdr-core-*/herdr-core` |
| `pin-change-head-shared-holder.*`、`pin-change-green-shared-holder.*` | 修前也“通过”：新终端交给了仍在运行的空 holder，core 没有新起 holder。实测一个 holder 托管多个终端，终端都退出后它仍常驻 | 先让终端都退出，再结束这个空 holder（核对是夹具进程） |
| `pin-change-holder-wait-1.*`、`-2.*` | 等 holder 消失时没有先让终端退出 | 同上 |

另有一次后台重启撞上 `operator.json` 已存在（EEXIST），那份摘要因测试自身缺陷被我删掉了，没有保留；改为重启前把凭据改名（与 t123 的重启做法相同）。

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t244_pin_change_e2e.py --summary <新文件>.json [--revision <版本>]
```

## 第三轮审查（`../review-3/REPORT.md`）

非阻塞，均处理或如实记下：

- 目标目录在但缺文件时返回不存在的路径：复现成立（`partial-install-red.json`）。改为 rename 失败时只有已有完整安装才沿用，否则抛出原错误（`partial-install-green.json`）。
- 并发首次安装、`rename` 的其他错误码：**没有运行证据**，只有代码判断（`rename` 一个目录到已存在的非空目录会失败，后到者沿用先到者）。从 `hc/bin` 起的旧 core 升级到新路径也没有运行。
- 删掉的那份 EEXIST 摘要：违反“保留异常结果”的规则，已无法恢复；它是测试重启前没改名凭据的失败，原因与处理写在上面。

## 第一版（标记文件）的审查记录

`../review-2/REPORT.md`：

- 第 4 条“中断的重装会留下与固定值相符的旧标记”：成立，已改为重装前先删标记。“二进制之后被截断或替换”与“两个后台同时首次启动同一数据目录”：修改前的代码同样没有防护（修改前每次都重新解包，并发时同样会互相覆盖），不在本票范围，未改。
- 第 5 条“缺少修后反事实”：成立，已补 `reverted-t123.json`。`pin-probe.json` 只改了标记文件，没有端到端地改变固定值。

复审 `../review-2/REREVIEW.md`：第 4 条“文件之后被截断或替换仍沿用”驳回不成立——修改前每次都重新解包，会自愈。已加大小与 mtime 核对（`pin-probe-2.json`）。不变式：core 使用数据目录期间，它启动所用的二进制文件身份不变；文件被改过就重装。“两个后台同时首次启动同一数据目录”仍可能都解包：`hcBinary` 在后台的 endpoint 与 pid 文件排他之前运行。修改前同样存在且每次启动都会发生，现在只剩首次；作为已知限制写在代码注释里，未改。第 5 条：固定值改变仍只有探针（改标记文件），没有改真实固定值的端到端运行。
