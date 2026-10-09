# T-045 修复交付（2026-10-09）

**离线修复与相关检查 PASS；正式工作台用量显示 INCOMPLETE。** 候选为 fork `a2a-t045` 的独立提交 `4b64e4cdd43e1e8e4c1f7bfaa2c66776f3985fa8`，父版本为 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`。T-045 保持 open，最终界面确认及 integration 交主控处理。

本次执行 [修复任务书](../../brief-T-045-fix.md) 与 [主控决定 01](../controller-decision-01.md)，只修复代理 fake-IP 与用量地址策略不相容的情况。没有调整网络配置，没有访问真实 provider、兑换 refresh token、读取或改写用户凭据、重启正式工作台或 push。

## 改动及上游文件

| 上游文件 | 改动 |
| --- | --- |
| `packages/shared/src/outboundHttp.ts` | 为用量调用增加显式 opt-in；只允许固定 HTTPS origins `chatgpt.com`、`api.anthropic.com`、`api2.cursor.sh` 的 IPv4 `198.18.0.0/15`。条件在 DNS/pinned-address 边界一处，包含代理 fake-IP 原因及移除条件注释。 |
| `apps/server/src/providerUsage/http.ts` | 在现有用量 helper 中启用上述策略，继续要求 public address。 |
| `apps/server/src/providerUsage/httpProxyFakeIp.test.ts` | 通过真实 helper 与共享出站层验证放行范围、DNS 混合答案、字面量/映射地址以及普通出站请求的原策略。 |

完整提交见 [fork-candidate.patch](fork-candidate.patch)。没有增加依赖、重试、备用 transport、双写或平行入口。原有共享出站 Deep modules 继续负责 origin、地址、DNS pinning、超时和限额；Tracer bullet 经真实 `collectProviderUsageSnapshots` → 凭据 reader → HTTP policy/decoder → provider parser → snapshot，使用隔离假凭据与 socket 前的 transport 替身。Ubiquitous language 沿用项目的 provider、用量 snapshot 与门禁术语，不把 HTTP 放行称为正式界面验收。

## 红绿与反例

每个运行目录保留 `command.json`、`result.json` 和 `output.log`，后续运行还保存当时夹具、测试文件与 candidate diff；旧结果不覆盖。`offline-red` 是沿用的 action 名称，它在候选上应转绿。

| 信号 | 结果 | 证据 |
| --- | --- | --- |
| 修复前，原离线 batch 夹具 | 退出 1：三 provider 均 error、transport 0，复现原提示 | [原红态](offline-red-20261009T063659574301Z/output.log) |
| 新边界测试对修复前生产代码 | 退出 1：3 个固定主机名正例失败；15 个反例通过 | [边界红态](boundary-20261009T063729222680Z/output.log) |
| 补强后的最终 batch 夹具对父版本的生产源码 | 退出 1：17/47 两组输入均被地址策略拒绝，三个 snapshot error、transport 0 | [父版本反事实](counterfactual-20261009T064451750257Z/output.log) |
| 最终候选的同一 batch 信号 | 退出 0：3/3；三个 provider 为 ok，snapshot 用量分别忠实返回输入 17、47 | [候选绿态](offline-red-20261009T064508972870Z/output.log) |
| 最终边界测试 | 退出 0：18/18 | [边界绿态](boundary-20261009T064048141186Z/output.log) |
| 删除主机名/origin 限制的 mutant | 退出 1：5 个反例拒绝过宽放行 | [mutant 反例](mutant-20261009T064028657229Z/output.log) |
| 六个相关既有用量测试文件 | 退出 0：47/47 | [相关回归](baseline-20261009T064048130254Z/output.log) |
| 共享地址策略测试 | 退出 0：13/13 | [共享策略](shared-20261009T064048129086Z/output.log) |
| 修改的 3 个文件格式与 lint | 均退出 0，lint 0 warnings/errors | [格式](format-20261009T064048154677Z/output.log)、[lint](lint-20261009T064048171104Z/output.log) |
| shared/server 包 typecheck | 均退出 0 | [shared](types-shared-20261009T064048143423Z/output.log)、[server](types-server-20261009T064048152527Z/output.log) |

独立输入来自主控的固定主机名/网段契约，以及夹具提供的两组百分比；断言不读取生产白名单常量或 parser 生成的答案。HTTPS mock 发生在真实地址检查之后，核对 pinned lookup 地址后返回离线 JSON；不替换共享安全层。每组 batch 只有 4 个 mock transport 调用（Cursor 两个端点）；真实 socket、Keychain、OAuth refresh、Claude auth nudge 和凭据写入均为 0。Codex 成功路径会查询 reset credits，夹具只将该 helper 替换为返回 null 的 stub，实际 CLI 不执行；stub 调用 1 次，不冒称 helper 未被调用。假凭据内容的前后相等断言通过。

白名单内主机名的 `10/8`、`172.16/12`、`192.168/16`、`127/8`、`169.254/16`、`::1`、`fc00::/7` 和 IPv4-mapped IPv6 仍拒绝；混合 DNS 答案含私网时整次拒绝。非白名单、子域、相似后缀、IP literal 在 fake-IP 网段仍拒绝，非标准端口不享受例外。普通 outbound 请求访问同一主机名也不自动获得例外。网段两侧的公共地址仍沿用原公共地址策略。

## 保留的异常与夹具修正

- [第一次 batch 绿态尝试](offline-red-20261009T063826538890Z/output.log) 中 Claude、Cursor 为 ok，Codex 仍 error，日志为 `Unexpected Codex CLI probe`：旧诊断夹具禁止成功后查询 reset-credit helper。修正为上述无 CLI stub 后，重新取得父版本红态与候选绿态；没有改生产的 Codex parser 或认证行为。
- [首次 mutant](mutant-20261009T063958009198Z/command.json) 和 [首次 format-write](format-write-20261009T064003953146Z/command.json) 因 runner action 路由错误实际执行了 batch，而不是目标检查，均退出 0。这是夹具编排错误，不能算主机名 mutant 或格式证据；日志保留。修正路由后，目标 mutant 按预期退出 1，格式工具实际运行后退出 0。以保存的 argv 判定执行内容，不以目录名字代替证据。

## 复现

在 a2a 根目录执行；运行前外置盘必须已挂载，fork 依赖已安装。所有缓存与临时夹具继续经 fork 的标准 `a2a/scripts/bun` 放到外置盘，没有移动、替换或链接构建输出及依赖目录。

```sh
python3 evidence/2026-10-09-batch5/T-045/fix/run.py counterfactual
python3 evidence/2026-10-09-batch5/T-045/fix/run.py offline-red
python3 evidence/2026-10-09-batch5/T-045/fix/run.py boundary
python3 evidence/2026-10-09-batch5/T-045/fix/run.py mutant
python3 evidence/2026-10-09-batch5/T-045/fix/run.py baseline
python3 evidence/2026-10-09-batch5/T-045/fix/run.py shared
python3 evidence/2026-10-09-batch5/T-045/fix/run.py format
python3 evidence/2026-10-09-batch5/T-045/fix/run.py lint
python3 evidence/2026-10-09-batch5/T-045/fix/run.py types-shared
python3 evidence/2026-10-09-batch5/T-045/fix/run.py types-server
```

`counterfactual` 固定父版本，临时替换两个生产文件，结束后恢复保存的原字节；`mutant` 只删除 origin 限制并在结束后恢复。两者应退出 1。不能与其他 fork 写入或验证并发运行。最终 fork 工作树已核对干净。

## 独立审查

`behavioral-acceptance-review` 在新的只读上下文审查冻结的 fork 候选，结论 **PASS（仅离线策略修复）**，未发现可达契约违规；原文见 [acceptance-review.md](acceptance-review.md)。审查未重跑测试或操作外部系统，不作为门禁 acceptance。

审查指出早期反事实的首个失败断言是 transport 次数，且没有保存 runner/实际被测源码副本。随后只补强证据：把 status 契约断言提前，保存 runner、fixture、source mode 和实际被测两个生产文件，重新运行固定父版本（退出 1：三个 error）与同一冻结候选（退出 0）。fork 候选未改动。补强记录见上表及各目录的 `evaluated-source/`；这些追加运行由实现 worker 执行，没有补称为当时的独立审查。

## 验收边界与交接

本次仅证明离线地址策略与真实 batch 路径；没有证明代理的真实 TLS 路由、用户上游认证、限流或实际响应格式，也没有正式 UI 截图。按预算未跑 35 项场景、全仓 tests/format/lint/typecheck 或产品构建；只执行上表中的相关检查。

身份、CLI、skill 来源及版本边界见 [identity.json](identity.json)。历史启动请求不作为当前实际模型/tier 的证明；task 由任务书确定，attempt、session_id、fence 与门禁收据未提供，不声称已完成 submit、门禁 acceptance 或 integration。a2a 只提交本目录及 T-045 Resolution，保留其他 worker 的脏文件。

主控下一步合并本独立提交、按授权重启正式工作台，再由用户确认 Codex、Claude 用量显示。此项完成前 T-045 的最终业务验收仍为 INCOMPLETE。

交付检查见 [checks-final.txt](checks-final.txt)：项目地图 Problems 0、Stale living docs 0；fork 干净；实际被测父版本与候选源码已与完整 Git 版本逐字节核对，JSON/Python/UTF-8 与链接检查通过。staged 原始证据 whitespace 检查退出 2，详情见 [raw-whitespace-check.txt](raw-whitespace-check.txt)，原始日志/生成检查记录的末尾空行与 patch context 空白保留；只检查起草文档、配置与脚本退出 0，见 [authored-whitespace-check.txt](authored-whitespace-check.txt)。首次将生成记录 `checks-final.txt` 纳入起草文件检查时也退出 2；该原始记录保留，没有裁剪空行来制造通过。
