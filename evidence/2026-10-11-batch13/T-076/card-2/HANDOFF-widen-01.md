# T-076-2 加宽与 reviewer 异常红态交接

状态：**INCOMPLETE**。主控 #39 授权的实现与探针已准备，本页两项动态阶段尚未运行。被测真实 Codex 回合 **0/8**；无 P-review 启动路径。当前 HEAD 为 `d3f2c2cf3b838d8f56e8a57629a19b9d282ea64f`，产品改动尚未提交。

前次 `outside-focused-tracer-01` 已读回：Tracer bullet、10项协议对照、8项既有边界对照通过，9个变异体命中原定编号。`commands.jsonl` 第8条命令调用旧 `scripts/score.validate_scores`，exit=0，stdout=`schema-1 payload accepted\n`，stderr为空。原产物保留。

执行顺序如下；每项输出只写新目录。出现非预期失败即停止，保留现场并交回，不换标签重试产品行为。

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh review-red reviewer-red-01
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh wide-green wide-green-01
```

`review-red` 从 `outside-focused-tracer-01/candidate-source.tar.gz` 解出已通过首条路径的旧产品，配当前测试夹具；先于相应异常处理修复取得契约红态：

| 故障输入 | 预写失败编号 | 合同预期 |
| --- | --- | --- |
| reviewer的PTY创建明确抛错 | REVIEW-CREATE-PAUSE | unknown/paused，保存执行主控issue |
| review仍待结论时关闭自建后台、重开同一state | REVIEW-RESTART-PAUSE | 保留原review身份，标未知并上报，不续接/重建 |
| reviewer收到有效结论，但PTY退出回调未确认 | REVIEW-RECLAIM-PAUSE | 暂停并上报，不能写成功回收 |

这是新契约的预期红态；外层PASS仅表示三项按编号失败。该阶段不计任何模型回合，也不修产品。创建和退出故障只由测试进程的PTY边界显式供给；后台/门禁/relay/状态均执行旧产品。结果不符或出现其他协议异常时交主控，不把它归为预期红态。

`wide-green` 冻结当前产品与测试，先跑15个用例，再跑13个单点变异体。范围：

- 显式测试路径校验；B仅带入声明的新测试、C与M独立；B非零/C为0；检查顺序和规则冻结；非法项目配置拒绝注册。
- 放弃只填结果与理由；升级需完整评分；缺分/字段错误不终结；终结只记一次分；原attempt回收不改写终结结果。
- 真实旧 `scripts/score` 在自建records目录生成执行主控及用户行；后台只读校验三行混合输入，旧校验器反向验证后台记录；重复attempt、缺事实、错误用户关联、放弃夹带facts和不完整尾行均拒绝。
- 使用Recovery既有Git事务屏障，分别在CAS前后中断本夹具后台；确认原PID、state、socket inode后只清本夹具残留端点，重启后拒绝变更评分，恢复原score_id/data，只补缺少的Git效果，最终评分恰好一次。Recovery源码只读，未改其9项断言。

13个变异体的替换文本、预写断言编号在 `run_t076_quality_widen.py` 的 `mutations` 列表；运行时另存完整 `*.mutation.json`。其中三项补足测试路径越界、symlink测试与坏配置被静默忽略的反事实。任何语法、导入、环境、清理或未预期协议错误都不会计作业务红态。

需要沙箱外：自建Unix socket、`ps`身份核对、后台启动/停止、只对自建后台PID的SIGKILL、Git屏障与恢复、旧评分脚本的隔离文件锁。每个后台脱离调用者进程组；不启动真实Codex、不复制auth、不安装真实hook、不运行Electron。依赖使用已存在的外置盘缓存，缺盘立即报错。

静态准备检查另存 `widen-preparation-checks.json`，再生成时换新的输出文件：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-widen-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/widen-preparation-checks.json
```

后续仍需：读回本次结果，取得reviewer异常红态后修复；按W01–W06/F01–F04迁移并跑完整8/9/18及T-075/T-076-1回归；P-review准确argv/home/hook逐次审批；真实完整流程；T-077联验；本卡fresh-context只读交付审查。T-077的worker名额释放及原生home归属衔接已另报 `20261011T180613Z-worker:s13-t076-2-issue-001`，当前保留S1的单worker约束。
