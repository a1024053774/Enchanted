# A-16／09C逐记录脱敏原件与外置清单

本契约落实用户rev 2的09B补证决定，并同样用于09C；依 [最小保留方案](../09B-MINIMAL-RAW-RETENTION-01.md)，不沿用A15“只留投影后删root”。**未捕获、未归档、未生成archive.json回执**；下面的树是未来实际记录布局，不是已存在文件。

```text
<scene>-raw-<new-run-label>/scene.tar.gz
  records/http/<role>/<actual-sequence>/request.body[.redacted].bin
  records/http/<role>/<actual-sequence>/response.body[.redacted].bin
  records/http/<role>/<actual-sequence>/meta.json
  records/hooks/<role>/<actual-trace-id>/started.json
  records/hooks/<role>/<actual-trace-id>/stdin[.redacted].bin
  records/hooks/<role>/<actual-trace-id>/stdout[.redacted].bin
  records/hooks/<role>/<actual-trace-id>/stderr[.redacted].bin
  records/hooks/<role>/<actual-trace-id>/finished.json (未完成则明确记缺，不补造)
  records/permissions/<phase>/original-screen.bin / full-capture.json / signed-approval.json / actual-write-receipts.jsonl
  records/state/pre-stop/<actual-table>.jsonl
  records/target/baseline.bin / received.bin
  records/identity/<actual-binding>.json
  inventory.json / redaction-map.json / independent-readback.json
```

外置父目录固定 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/`；A16用全新 `09b-a16-raw-<new-run-label>/`，C用 `09c-raw-<new-run-label>/`。只预留逻辑名，本轮不创建。外置盘未挂载、路径是符号链接/已存在、I/O不确定均BLOCKED，不回退内置，不覆盖旧包。

## 在真实边界捕获，不从summary重建

| 材料 | 必留内容和采集时点 |
|---|---|
| 每个POST | fake handler收取请求时、验证前分配真实序号；保留method/原path/实际body字节数、开始/完成UTC、角色/launch/native/prompt/实际dispatch及全局seq、真实请求ID和状态。拒绝、失败、CLI重试也保留，不只遍历accepted条目。Messages、count_tokens及其他path分开计，保留所有POST；未知调用仍停止场景，不能把额外请求藏成辅助计数 |
| 请求正文 | 从实际CLI request bytes留全messages/system/tools等允许内容，保留顺序、真实tool_use/result、Bash command schema和原文本，不投影成标准化样本。认证头从采集边界就不保留值；如正文/metadata确有敏感认证/账户字段，只对该value定点脱敏并留指针/字节范围/原长度；不要无理由删整段system或messages |
| 响应 | 实际状态/content-type/每次request对应关系和原始SSE/错误正文；保留message/content_block起止及delta、tool_use、完整message_stop/EOF。未知敏感文本停止对外归档待处理，不能只存错误码冒充原响应 |
| hooks | 原hookTrace每个目录的started、stdin、stdout/stderr、finished原件，含拒绝/异常/未完成。stdin保留事件名/native session/prompt、工具命令、Stop原内容；started/finished的launch/pid/time/exit/duration原值不改。不只选择预期的七/三次许可来导出 |
| 许可/输入 | 全部完整原屏、页链和最后EOF确认；签字件、实际PermissionRequest、单次窗口request→intent→written、action/CR；保留失败预检/拒绝/未知写入，不把它们改PASS。C-I3另外保留逐项比较实值、等待与时钟条件、消费一次的记录 |
| 事件/库行 | **仅停机前**一致只读事务导出相关实际行及表/seq/原JSON：dispatch、turn_submit/submitted、native信号/idle、relay请求/结果、inbox/投递历史、feedback、emergency interrupt及action。秘密字段定点脱敏；不能只导聚合计数、不能整库/WAL拷进归档。导出结束关闭读连接 |
| 身份/目标 | 实际card/dispatch/claim、attempt/session/fence/spec_rev/workspace、原API ready/PID/双读lstart/argv、两角色launch、初始及六次startup收据；target基线/最终原字节。manifest不含operator/worker/window capability值，不复制用户HOME/认证/history |

正常A16预期17 Messages、10UPS/10Stop/7PermissionRequest；正常C预期8 Messages、5UPS/5Stop/3PermissionRequest。**这些是oracle，不是枚举筛选上限**。多一条/少finished也有独立文件并记异常，不能为匹配数字丢原件。HTTP request_id和本地inbox request_id分别保留、用真实联系关联，不互相代填。

只有实际内容无需脱敏且逐字节相同才用原文件名并记redacted=false；改过内容用redacted文件名及映射，不能声称byte-identical原件。Authorization/Cookie/API key/token、capability、账户私密信息不进入Git或外置记录，原秘密值不以hash或旁路副本留存。结构白名单/批准fixture内容核对为主，关键词扫描只能补查，不能以“扫描0”代替审阅；不能把原文删到失去独立复核能力。

## `*.archive.json`与验证

每个本地逻辑原件在归档后生成同名 `.archive.json` 指针，统一字段见 [ARCHIVE-POINTER-CONTRACT](ARCHIVE-POINTER-CONTRACT.json)。必须列实际绝对archive路径、member路径、原/脱敏字节数、类型、codec、是否脱敏/映射、真实身份/序号及捕获时间、逐字节读回结果；批次总清单列全成员与缺失/未完成状态。不用校验和替代直接字节比较，不预填bytes:null/byte_readback=PASS蒙混。

打包前记录源目录全量枚举和服务最终序号，和每条POST/hook逐一对应；先复制/脱敏到本场受保护暂存区，逐条与批准保留规则核对，再只将**脱敏暂存区**归档外置。原始含敏感数据的root不整体打包；Git保留指针、规则/源码版本、必要小反例与重放命令，大原件留外置。tar每个普通文件和暂存文件逐字节相等，目录/符号链接分别核对类型/目标，采集根或原件路径链接到场景外一律拒绝、不沿链接读取；禁止路径穿越/额外成员，未认识类型不放宽。回收前主控/fresh reviewer从这个包直接重数HTTP/hook、关联许可/业务行与target，不能调用collector summary作为答案。

合并后必须先证明：额外失败POST/409、重复hook、缺finished、漏meta、截断屏幕、脱敏误删tool_result/身份字段、篡改archive成员，都能由逐记录检查检出；保留真实HTTP/signal和窗口路径红绿。当前只写这些验收契约，不宣告排练PASS。删除root以前包必须已可独立读回；否则阻止删除，不能重演F1。
