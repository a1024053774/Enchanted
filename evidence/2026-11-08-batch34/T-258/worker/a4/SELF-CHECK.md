# T-258 a4 实现者自查

这是任务卡要求的实现者自查，不是正式独立审查。范围固定于新基线 `172b2f17566f923b2e0be8f7d21fc0b189b83fa2` 加三个逐字节恢复文件和本目录精简证据；最终 SHA 由 submit 绑定。目标、非目标和版本边界见 [RESULTS](RESULTS.md)。没有再开 reviewer 或执行真实 CLI。

## design-integrity-review

STATUS: PASS（实现者结构自查）

SUMMARY: 无已确认的范围内结构性缺陷；没有新增实现。

TARGET: 上述固定恢复内容，相对新基线。

FINDINGS:

- 无确认缺陷。恢复仍由产生启动期限失败的 Panes 所有：daemon 先校验 launch 身份，signal 完成 envelope 和原始派发来源检查，confirmLateCodexStart 在异步观察前后核对当前 worker/review/运行时，先写恢复事件后清错。没有绕过 Stop、relay 或门禁，没有双写、重发或平行 API。
- 唯一产品差异为恢复历史修复的 65 行新增、2 行删除；没有修改 questions.ts 或 T-259 core.ts。未新增异常边界或兼容恢复分支。
- 恢复的模块测试捕获异常记录 FAIL 后原样抛出，finally 关闭自身数据库。E2E 的 Responses 异常记入 api.error 并返回 HTTP 500，主等待检查该错误；主流程把 Defect 判 FAIL、其他异常判 INCOMPLETE；清理失败另记 cleanup_errors 并判 INCOMPLETE。诊断异常写入 diagnostic_errors，供主控核对。这些处理归属于测试诊断与清理，不是产品 fallback。
- 本轮小运行器不吞异常，不覆盖既有摘要；只有逐案断言及清理状态已保存后才删除自身原始大摘要和副本。异常退出保留已有摘要与未清理资源；检查时同时核对退出码和 cleanup，不能只看测试 status 字段。本轮五次运行清理均成功。

LIMITATIONS:

- design-scan.json 是定位器，无命中不等于通过证明；测试 E2E 只作静态核对，本 worker 未执行它。
- 正式独立审查由主控在最终冻结候选上安排，不能用本自查替代。

RULE:

- 本轮没有新发现或修补缺陷；不增加治理规则或复审轮次。

## behavioral-acceptance-review

STATUS: INCOMPLETE

SUMMARY: 本轮模块与定向回归证据齐全；真实入口、独立审查及整票验收尚未完成。

TARGET: 上述固定恢复内容及本轮五份逐案摘要。

EVIDENCE:

- 预期来自冻结 T-258 Acceptance、任务卡限定的可信恢复契约和 T-257/原生来源要求。恢复测试是被检查的证据，不是独立 oracle。
- 编排/异步：真实 Panes、Store、drain、rollout 解析和 signal；包含 0～2 次 scan/旧 Stop 排列、Stop await 重叠、观察中替换 attempt/追加失败、两个 reviewer 正例及 11 个反例。117 项通过不外推成任意时序证明。
- 身份/范围：无原生身份、辅助会话、错误 prompt/cwd/file/session/turn、过期 attempt/fence/spec、review/candidate/verification 不一致等继续拒绝；当前范围冻结文件未改。
- 交互/外部副作用：模块用转交计数及写入次数核对无重复；终端与 processInfo 为边界替身，不能证明真实请求受理、真实工作中回收拒绝或完成后回收。真实入口是本轮必须补齐的证据。
- 文件/运维：真实 SQLite 和 rollout 读写在自身夹具中执行，清理状态已保存；未触碰正式后台、用户 hc、全局配置或额外目录。
- 检索/记忆：N/A，本票没有此能力。供应商模型理解、成本、吞吐及正式发布：N/A，本卡不主张这些能力。

FINDINGS:

- 无已复现且仍未修复的范围内缺陷；下列缺口保持 INCOMPLETE，不用历史 PASS 填补。

COUNTEREXAMPLE:

- 新基线父版用同一模块输入得到 75 项失败，失败断言指向可信晚启动仍未恢复或合法 UPS 身份尚未采集；exit 1。
- 将恢复核验调用替换为直接清错的源码副本得到 32 项失败，21 个恢复守卫反例及 11 个 reviewer 拒绝反例被检出；exit 1。
- 旧真实入口的父版/候选证据只对应历史版本；旧 SIGSTOP 仍为 INCOMPLETE/NO_GO，不作为新基线红态。

LIMITATIONS:

- 本 worker 是恢复与证据整理者，不具独立 reviewer 身份。主控须补新冻结候选真实 Codex CLI 红绿并新开只读审查。
- 模块不验证真实 processInfo、hc、hook transport、relay 或 reclaim；真实 reviewer 的 review_submit/reclaimReview 同样未在本轮验证。
- `workbench/README.md` 为卡外 stale living doc，已排队 issue，请主控同步；请求排队不等于已处理。

RULE:

- 本轮执行既有不变式及反事实，不扩大实现、不修改验收要求。
