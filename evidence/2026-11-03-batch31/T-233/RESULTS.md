# T-233 结果（2026-11-03，HEAD `3aaeb41e0` 加工作区改动）

结论：**PASS**（GPT 审查与复审对本票无阻塞，见 `../cu-review/`）。

## 改动

`workbench/tests/test_t212_shell_hc_e2e.py`：

- 侧栏行选择器 `[data-terminal-launch=…]` 改为界面实际的 `[data-agent-launch=…]`。
- Electron 场景在打开窗口前，在同一项目里多开一个终端窗格（`decoy_launch`）。这样指定窗格要被点到才会显示，选择器错了测试会失败。

## 证据

| 运行 | 选择器 | 结果 |
| --- | --- | --- |
| `red-old-selector/run.json` | 旧 `data-terminal-launch`，两个窗格 | INCOMPLETE：`超时：接回的项目终端窗格`（清理 PASS） |
| `green/run.json` | 新 `data-agent-launch`，两个窗格 | PASS，xterm 459 行编号与 hc 一致 |
| `green-mismatched/run.json` | 同上，加 `--mismatched-screen` | PASS，467 行 |

红态与绿态之间只差选择器这一处，红态即反事实。

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <新目录>
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output <新目录>
```

红态：把选择器改回 `data-terminal-launch` 后运行第一条。
