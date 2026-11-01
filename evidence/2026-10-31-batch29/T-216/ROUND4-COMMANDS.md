# 第四轮命令

工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-216`。本轮未改生产代码；在 hc 参数事实核对阶段停止。

已运行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git show main:.project-map/tickets/T-216-issues-pushed-to-controller.md
git show main:evidence/2026-10-31-batch29/T-211/RESULTS.md
/private/tmp/t216-r2-rklei589/state/hc/bin/herdr-core send --help
/private/tmp/t216-r2-rklei589/state/hc/bin/herdr-core schema > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4-hc-schema.json
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4_hc_probe.py
```

最后一条是第一次运行时的命令，其原始脚本保留为 `round4_hc_probe-01.py`，结果为 `round4-hc-probe-01.json`。脚本只在自己新建的 `/private/tmp/t216-r4-hc-*` 夹具内启动 core，显式指定 HC_SESSION、HC_SOCKET、XDG 状态与配置目录，最后停止它。使用既有测试夹具里固定的 0.1.15 二进制，没有连接该旧夹具的 core。

现有 `round4_hc_probe.py` 仅增加必填输出参数及禁止覆盖检查。重跑使用新文件名：

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4_hc_probe.py \
  --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4-hc-probe-02.json \
  > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4-hc-probe-02.log 2>&1
```

收尾（实际运行）：

```sh
git diff --check
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round4_delivery_check.py
```

完整候选保存方式：`git diff --binary HEAD`，然后对 `git ls-files --others --exclude-standard` 列出的每个新文件追加 `git diff --no-index --binary -- /dev/null <文件>`。退出 1 是 no-index 存在差异的正常结果。产物 `round4-candidate.patch` 与 `round3-candidate.patch` 逐字相同。
