---
id: T-269
title: 编排事件表没有索引，后台主线程被全表扫描占满
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## 事实

2026-11-09 14:19Z 重启后，正式后台（PID 80941）CPU 一直在 97% 左右。10 秒采样里，主线程 5026 个样本全部落在同一个连接读回调中的 SQLite `.get()` 上，其中大部分是 `pread`。

- `orchestration_events` 有 208,537 行，`data` 列约 170 MB。表上只有主键，没有其他索引。
- 代码里按 `launch`、`type` 查这张表的地方有几十处。用正式数据的只读连接、后台自己的 SQLite 实测：
  - 查一条不存在的事件：17.2 ms；
  - 角色申请列表（每 5 秒一次）：28.1 ms；
  - 轨迹归档里 45 个 Codex 会话的扫描（每 30 秒一次）：873 ms，加上 Claude 部分共约 1 s。
- 在副本上加 `(launch,type,seq)`、`(type,seq)` 两个索引后，四项分别降到 0.0、0.2、52.3、0.6 ms。副本用完已删除。
- 同一时段 worker 的 `signal` 请求最长 63.6 s。T-268 的提交提示词 hook 晚了约 15 s，以 `prompt_submit_deadline_passed` 被拒。T-266 转交审查结论时读到半截 JSON。这些现象与主线程被占满相符，但各自是否只由它造成，还要在修复后复验。

采样看不到 JS 函数名，最热的具体调用点没有定位。

审查 01 补上了这一点。`panes.ts` 有 12 处、`daemon.ts` 有 1 处 `store.read().filter(e => e.launch === X)`，每次都把整张表读出来、逐行解析，再在内存里按 launch 过滤。hook 处理（Stop 信任检查、问题回答）和界面每秒一次的窗格快照（`questions()`）都走这条路。正式数据上，这样读一次 1,415 ms；改用按索引只读一个会话的 `launchEvents`，9.1 ms。索引对这条路径本身没有帮助，所以修复包括把这 13 处换掉。

## 决定

用户 2026-11-09 在 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 里批准由该会话直接修，Codex 开只读会话审查，然后打包、安装、重启后台：

> 好，先修索引

## Acceptance

- [ ] 新建的状态文件，以及没有这两个索引的旧状态文件，打开后都有 `(launch, type)` 和 `(type)` 两个索引；再次打开不报错；表里的行数不变，只追加触发器仍然生效。
- [ ] 后台常用的几条按 launch、type 的查询（`lastEvent`、按 launch 读取、角色申请列表、轨迹归档来源、窗格布局、执行设置），查询计划都不再遍历整张表，带索引的遍历也算；按 launch 的查询要用 launch 缩小范围。在父版本上，这条测试判红；去掉 `(launch, type)` 索引的变异也判红。
- [ ] 不再有调用方读全表、再按 launch 过滤。按 launch 读取的结果和顺序都与原来一样。改回读全表的变异、去掉排序的变异都判红。
- [ ] 装到正式版后，后台 CPU 不再持续满载；hook 请求的处理时长回到秒级以下；有采样和请求时长作为证据。
- [ ] Codex 只读审查完成。

## 当前状态

进行中。
