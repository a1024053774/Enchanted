---
id: T-026
title: 把构建缓存与工具链放到外置盘
type: task
status: open
blocked_by: []
claimed_by:
supersedes:
---

## Question

按 T-020，把 a2a 与 Enchanted 的构建输出和缓存放到 `/Volumes/WD-Elements`：

- 定下 `CARGO_TARGET_DIR`、`CARGO_HOME`、Zig 缓存与 npm 缓存的配置方式；
- 外置盘未挂载时构建必须报错，不回退到内置盘；
- 实测机械盘上的首次编译与增量编译耗时，以及多个 worker 同时编译时的争用；
- 引擎编译需要的 Zig 工具链一并处理（本机尚未安装）。

## Resolution

未执行。
