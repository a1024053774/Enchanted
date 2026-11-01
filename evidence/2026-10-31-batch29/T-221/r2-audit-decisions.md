### 同类写法普查清单

范围：当前 workbench/src、workbench/app、workbench/tests、acceptance、scripts、docs/assets；排除历史 evidence、records、findings、reports 和依赖。主扫描覆盖 660 份源码／脚本／样式文件，共 48 个命中；每个命中均列在下表，另补 4 个修后不再匹配旧模式的上下文位置。扩大日期与数字搜索见 r2-audit-wide.log；原始模式与每行源码见 r2-audit.log。

本轮没有发现尚未修复的“固定 24 小时／固定偏移跨本地日期”产品路径。定时产品的 setHours/setDate 顺序问题是另一种根因，单列为 INCOMPLETE，未把它报成安全或已修复。

| 位置 | 状态／处理 | 是否在夏令时出错及理由 |
| --- | --- | --- |
| `workbench/src/trajectoryArchive.ts:84` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/trajectoryArchive.ts:102` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/panes.ts:1246` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/retrospective.ts:60` | INCOMPLETE；不改定时产品；不同根因，需主控决定 | setDate 本身不含固定 24 小时；09:00/10:00 跨回拨正确。但 59 行先 setHours、再在此回退日期，春季跳过当天会污染有效周一 02:30；独立产品反例已保存。 |
| `workbench/src/retrospective.ts:61` | INCOMPLETE；不改定时产品；不同根因，需主控决定 | setDate 本身不含固定 24 小时；09:00/10:00 跨回拨正确。但 59 行先 setHours、再在此回退日期，春季跳过当天会污染有效周一 02:30；独立产品反例已保存。 |
| `workbench/src/nativeLink.ts:141` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/codexScanDays.ts:5` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `workbench/src/codexScanDays.ts:7` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `workbench/src/codexScanDays.ts:9` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `docs/assets/showcase.js:120` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/showcase.js:121` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/demo.js:714` | PASS；不改 | 只从当前 Date 取月日时分秒展示记录，不跨日推算。 |
| `workbench/app/style.css:14` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/demo.css:14` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `acceptance/page/check.mjs:11` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `acceptance/page/check.mjs:73` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/app/main.ts:842` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/app/renderer.tsx:95` | PASS；不改 | 将 now - Date.parse(iso) 的已流逝秒数换成小时／24 小时时长单位，既不生成日历日期，也不要求日界对齐。 |
| `workbench/app/renderer.tsx:96` | PASS；不改 | 将 now - Date.parse(iso) 的已流逝秒数换成小时／24 小时时长单位，既不生成日历日期，也不要求日界对齐。 |
| `workbench/app/MetricsPage.tsx:23` | PASS；不改 | 从本地 T00:00:00 解析 date input，终点用 setDate 加一天；23/25 小时日会保留本地午夜边界。 |
| `scripts/inbox:12` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:13` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:14` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:38` | PASS；不改 | 把已有时区的同一时刻转成 UTC 供时长比较，无日期增减；403 行的 now 也是 UTC。 |
| `workbench/tests/test_t139_layout_store.mjs:120` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t107_daemon_readonly.mjs:42` | PASS；不改 | 日志目录取当前本地日期；40 行仅把启动时间设成日志前 60 秒（时长），不把一分钟当日历日。 |
| `workbench/tests/test_t195_native_link_e2e.py:391` | PASS；不改 | naive 本地 datetime 加一天只用于 strftime 年/月/日路径，不转换为 epoch 或附固定偏移；这是日历字段运算，跨 DST 仍取明天日期。 |
| `workbench/tests/test_t137_reflect_e2e.py:159` | PASS；本轮修复时钟来源；159/160 行日历算法保留 | 原 after 来自无参数 astimezone()，跨两天／七天会保留旧偏移，已实测红态。179、265 行改用 ZoneInfo 时钟后，此处 timedelta 按具名时区的日历日期计算。 |
| `workbench/tests/test_t137_reflect_e2e.py:160` | PASS；本轮修复时钟来源；159/160 行日历算法保留 | 原 after 来自无参数 astimezone()，跨两天／七天会保留旧偏移，已实测红态。179、265 行改用 ZoneInfo 时钟后，此处 timedelta 按具名时区的日历日期计算。 |
| `workbench/tests/test_t091_regression_collection.py:35` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t091_regression_collection.py:41` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/t093_fake_login_peer.py:65` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/t093_fake_login_peer.py:69` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t181_question_text_e2e.py:104` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t136_retrospective_e2e.py:289` | PASS；本轮已修；13 项全套通过 | 原固定偏移加两天跨回拨差一小时；现用与后台相同 IANA 时区的 local_now + timedelta，保持墙钟 10:00。 |
| `workbench/tests/test_t136_retrospective_e2e.py:294` | PASS；不改 | 先在具名本地时区确定 10:00，再加／减一分钟；转 UTC 只序列化同一时刻，原协议与断言未改。 |
| `workbench/tests/test_t136_retrospective_e2e.py:295` | PASS；不改 | 先在具名本地时区确定 10:00，再加／减一分钟；转 UTC 只序列化同一时刻，原协议与断言未改。 |
| `workbench/tests/test_t136_retrospective_e2e.py:305` | PASS；随时钟来源修复；日历算法与断言不改 | 原 slot 固定偏移时，跨周也会错；slot 改为 ZoneInfo 后加七天按日历处理，最后才把同一时刻序列化为 UTC。关闭后不触发断言已真正执行。 |
| `workbench/tests/test_t162_role_records_metrics_e2e.py:174` | PASS；不改 | 174 行以 new Date(年,月,日+1) 构造本地次日午夜；179 行只格式化本地日期输入值，均没有固定 24 小时。 |
| `workbench/tests/test_t162_role_records_metrics_e2e.py:179` | PASS；不改 | 174 行以 new Date(年,月,日+1) 构造本地次日午夜；179 行只格式化本地日期输入值，均没有固定 24 小时。 |
| `workbench/tests/test_t091_pane_ipc.mjs:60` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t124_controller_e2e.py:386` | PASS；不改 | 配额夹具的 resets_at 是未来 epoch 秒，+86400 仅安排另一个较晚重置时刻；没有约定为本地明天某个墙钟时间。 |
| `workbench/tests/test_t170_failed_launch_reclaim_e2e.py:17` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/run_t093_login_chain.py:206` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t221_codex_scan_days.ts:51` | PASS；不改 | 只将产品给出的 Date 格式化成本地年/月/日；预期数组另行写死，不做跨日算术。 |
| `workbench/tests/test_t221_calendar_clocks.py:34` | PASS；不改 | 被测对象是新的具名本地时钟；日历加两天／七天后与手工写死的春、秋、月末、年末日期和偏移比对。固定偏移变异在四组 DST 断言失败。 |
| `workbench/tests/test_t167_codex_start_e2e.py:77` | PASS；不改 | HTTP 配额 header 的 reset-at 是 now 后 86400 秒的到期时刻，不是本地日历日程；用时长正确。 |
| `workbench/tests/controlled_quality_pty.ts:35` | PASS；不改 | 只格式化写记录时的当前本地日期，无跨日推算。 |
| `workbench/tests/test_t137_reflect_e2e.py:162` | PASS；本轮改为 when.isoformat() | 已有具名时区的日程直接序列化；删除多余无参数 astimezone，不在序列化前冻结偏移。 |
| `workbench/tests/test_t137_reflect_e2e.py:179` | PASS；本轮改用 local_now(fixture.env) | 原 datetime.now().astimezone() 冻结当前偏移，使下周一 09:00 跨 DST 时错误；改用具名 ZoneInfo。 |
| `workbench/tests/test_t137_reflect_e2e.py:265` | PASS；本轮改用 local_now(fixture.env) | 第二次下周一计算也必须修；不能只修默认关闭场景的第一次时钟。 |
| `workbench/tests/local_calendar.py:10` | PASS；新增共享测试时钟 | 从 fixture.env 下的 Node 读取 IANA zone，再用 datetime.now(ZoneInfo(name))；不猜固定偏移、不切 UTC、无 fallback。 |
