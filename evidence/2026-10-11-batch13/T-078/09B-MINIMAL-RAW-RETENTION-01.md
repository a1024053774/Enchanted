# F1：若用户批准重跑09B，最小逐记录脱敏原件保留方案

2026-10-16，主控 #335。**只交方案，不决定重跑、不启动、不修改现有redactor/cleanup。** A15历史17 POST/七许可仍是“采集器当时报告PASS、独立终审INCOMPLETE”；旧root已删，不能补造其HTTP/hook原件。旧1,766字节tar、报告和全部失败保留。本方案供构思主控转用户判断重跑价值及保留范围。

## 必须保留的逐记录材料

下表的“原件”指在实际边界捕获、仅按列明字段脱敏的单条记录，**不是重新从汇总表合成**。每条记录有原相对路径、捕获UTC/monotonic、原始长度、脱敏后的长度、变更JSON指针/字节范围/原因；保持剩余字段、消息顺序、实际ID和事件原序。不得以独立request对象/工具oracle的标准化结果替代CLI实际输入。

| 来源 | 外置保留的最小文件 | reviewer可直接重算什么 |
|---|---|---|
| 每个实际HTTP POST（验证前分配序号） | `http/<role>/<seq>/request.body.redacted.bin`；一份meta含method/path、实际body_bytes、收/发时刻、status/content-type、dispatch_id/全局seq、native/session、实际request_id；失败/409/重试也各留一份，禁止只留accepted | 连续序号、每角色实际POST数、失败/额外请求、阶段/身份绑定；不依赖“6/11”总数 |
| 每次HTTP响应 | 同序号原始SSE body或原始错误body（只作必要脱敏），真实状态meta；保留content_block_start/delta/stop、tool_use id/input、message_stop等原字节 | 200/409、SSE是否真正完整、工具命令及第二条Messages中同ID tool_result；失败不能当免费 |
| 每次原生hook（包括拒绝/异常） | `hooks/<role>/<trace-id>/started.json`、真实`stdin.redacted.bin`、`stdout.redacted.bin`、`stderr.redacted.bin`、`finished.json`，原launch/pid/time/exit/duration不改；未finished要保留为未完成 | 独立数UPS/Stop/PermissionRequest及退出码；按native session/prompt_id对齐，不能只存一个计数或已批准的七项 |
| 七次工具许可 | 各自完整permission-screen.bin、严格分页capture/EOF收据、独立确认读屏、签字批准、实际PermissionRequest引用、按键前核对结果、window请求→write_intent→written回执与原action行；保留错误预检/拒绝 | 原屏命令/Yes是否匹配、读完后才Enter、每次恰一CR且form=action、不增根；不拿key attempt当已写入 |
| 原始业务事件/库行（停止前导出） | 逐行只读导出本场相关dispatch、turn_submit_intent/submitted、native信号、idle、relay_requests/results、inbox_records/delivery历史、feedback intent/registered、emergency interrupt及七action；每行保留原表/seq/实际JSON，秘密字段定点脱敏 | pending→queued→turn_submitted→delivered→原I2；原request/entry、真实角色、ack唯一/幂等、全局seq与CR根数 |
| 目标及身份 | target-baseline.bin、最终received.bin；真实card/dispatch/claim回执、两角色launch/runtime/process manifest、PID/lstart和归属快照、初始readiness与六次startup刷新原收据 | 目标恰一个1b、未reclaim/换attempt、角色未互换、首启键不提前delivered；身份文件中的capability值不得外传 |
| 总清单和代码 | 所有捕获条目的完整文件清单（含失败/未完成），实际服务最末POST序号及hook目录枚举，源码版本/闭包、批准与重放命令、脱敏规则版本 | 检查漏文件/跳号/只选成功条目；原summary只是索引，不能取代这些文件 |

HTTP request_id是供应商/协议的请求标识，inbox queued request_id是本地转交请求，两者均保留但不混同。`tool_result delivered:false`如实保留，后续真实Stop/relay生成entry的事实另由对应行证明，不在tool_result里合成entry。

## 脱敏边界

仅用于**假服务/夹具输入**的重跑。Authorization、Cookie、API key/token、capability/window/worker/operator秘密、账户metadata、用户设置/历史/认证绝不进入Git或外置原件。HTTP头只保留白名单（method/path/content-type/status和不敏感请求ID等），绝不记录认证值；request的system/账户metadata可定点替换为明确占位符，记录移除的JSON指针和原长度，不能删掉整条POST。

必须保留CLI实际messages的角色/顺序、根正文和标记、tool_use/tool_result全部已批准业务字段、真实tools Bash command schema、native hook的event/session/prompt/真实command、Stop内容。夹具文本/命令逐条与批准来源核对；非批准文本或新字段无法判断时**停止归档/删除**，保留受保护现场给主控处理，不用关键词删除整段直到测试变绿。仅关键词扫描“0命中”不足以证明安全；结构白名单是主规则，扫描只补查泄漏。stdout/stderr也先检查，不因名为日志就全拷。

JSON脱敏优先保留未改区域的原字节：只替换已明确的敏感value范围；若使用重序列化，文件明确标作redacted JSON，另记转码规则/原总字节数，不宣称逐字节原件。API响应在假模型固定文本/批准工具范围内可完整保留。原始秘密值不以哈希或旁路备份保存。最终SQLite整库/WAL含凭据，不作为最小保留物；只在daemon运行时快照事务中逐行导出上述相关行并关闭读连接，之后不再依赖数据库。

## 删除前的验收门

1. 新捕获器/归档器先用真实HTTP与真实signal入口做无模型排练；额外第18 POST/409、重复hook/缺finished、缺一页许可屏、脱敏误删tool_result、缺一个meta等已知坏输入，都必须被逐文件oracle拒绝。不能仅让两个由同一collector生成的summary相等。
2. 全场结束后只读枚举**所有**POST与hook，而不是遍历批准清单筛选七项；将每条保留物写到外置新目录，类型/目标/文件字节逐成员读回，清单不得漏项或跳号。每个已脱敏文件在受保护root中与它要归档的脱敏副本逐字相同；未脱敏原件在此时仍在root，不进入外置。
3. 请主控或fresh reviewer从外置包重新、独立地数17 POST、全部响应、UPS/Stop/七PermissionRequest并核对七许可、原I2与target，不调用worker summary当答案；实际异常POST也算预算。缺项即INCOMPLETE，**root先不删**，外置盘I/O卡住也不跳过。
4. 确认该包足够复核后另签owner-bound cleanup：正常daemon_stop关角色/target，每API一次SIGTERM、确认退出，停机后只验已存归档字节/成员和原pre-stop收据，不读SQLite；最后删该新root。slot另列。删除决定不替验收通过。

这会改变A15“只保留小汇总后删root”的证据保留流程，必须随用户是否重跑09B的决定一起批准；本轮没有改旧清理脚本或把新要求回填成过去已经遵守。

## 代价估计（估计，不是已测大小/耗时）

重跑协议/根预算保持不变：**两真实Claude会话、真实Codex0、模型0；ideation4根/6 POST、executor6/11，合计17 POST/七工具许可**。保留原件不新增模型、CLI或Messages；仍需两个角色各六个首启单键及七次工具一次性Yes，源冻结/权限预检/实际根时序不能省。执行耗时主要由这19次单键/工具审签和阶段读回决定，未实测不承诺几分钟完成，不拿A15含长暂停的总时长当性能基线。

至少17组HTTP请求/响应/meta、约27组原生hook（正常10UPS＋10Stop＋7许可；有额外/失败时更多，不能以27为筛选上限）、七套许可原屏与实际写入证据。A15七许可完整参考长度合计约0.32MiB；HTTP/hook原件已删，不能补算其实际字节。按既有固定fixture请求/短SSE估计，最小脱敏包未压缩约1～5MiB，先留20MiB外置空间余量；累计终端输出/诊断可能更大，以实际测量为准，不用硬截断压进估计。原始行/屏幕一份即可，各阶段报告引用同一实际文件，避免重复保存全历史。

I/O代价是逐条捕获、一次结构化脱敏及一次外置逐成员读回；内存按单请求/页处理，无需多开Codex/子代理。压缩率、脱敏CPU和复验耗时未知，须在排练记录。>5MiB按现行规则直接外置，Git保留manifest/必要小反例/定位与重放命令；外置盘缺失不回退内置。新redactor测试/独立复核是必要的额外准备工时，不能靠直接复制含认证raw日志节省。
