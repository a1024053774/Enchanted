# T-077：relay 修复提交后的统一回归

2026-10-11，回应主控 #73。**INCOMPLETE**：relay-check-02 的 preimage 已取得业务红态（1 failure、0 errors），候选完整闭环 PASS。修复、测试及相关失败/通过证据已提交为 `da44c6733f5046f7c645028352859a80070f15b9`，九项尾注齐全。提交前将候选与通过时归档的 24 个文件逐字节核对，全部一致。

## 执行命令

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh relay-regression-01
```

固定上述提交，父提交为 `93094e7be82c21448c460436c360ffb0f75a3412`。每组前后检查 HEAD、父提交以及产品/测试/acceptance/分页夹具零差异，只允许本票证据变化。任一步失败即停，不重试；新输出统一为 `outside-relay-regression-01-*`，不覆盖先前运行。

| 检查 | 本阶段执行次数与通过条件 |
| --- | --- |
| S3 完成条件 | 全部 25 项一次，含冲突 7 项；0 failures/errors/skipped |
| 原 8/9/18 回归 | coop 8、recovery 9、run 18，各一次；收证据完成 |
| CAS、cards | 1、15，各一次；收证据错误为空 |
| 窗格、原生末尾记录、派发状态 | 4、9、1，各一次；原有检查全部通过 |
| 身份、停机 | 各 4 项一次；包含先前修正 cwd 的夹具 |
| relay 冲突交付闭环 | 候选一次；新 attempt 用同一编号交付、身份绑定、重验与集成通过；不重复已确认的 preimage |
| relay 作用域、core、cli | 各一次；作用域 5 项以及原有正反例全部通过 |
| 全库去重变异体 | 只选 `global-lookup` 一次；须检出跨 attempt、跨任务两处业务失败，0 异常 |

变异体脚本新增可选选择参数，原默认三变异体行为保持；本阶段不重复另外两个变异体。所有业务测试与断言使用刚提交的版本，没有为本次回归修改。

最后由 `summarize-relay-regression-01.py` 读取全部 16 组收据，核对数量、失败、跳过、版本和收证据错误，生成 `outside-relay-regression-01-summary.json`；同时保存 map status、Panes 现场，按原规则将超过 5 MB 的新证据逐字节核对后归档至外置盘，仓库留路径和重放命令。未执行或收据缺失的组不能记为 PASS。

## 准备检查与边界

本次只做语法、命令清单、版本和范围检查。范围审计为 `relay-regression-scope-01.json`：17 个受保护文件 PASS，审计器自检 PASS。准备收据为 `relay-regression-readiness-01.json`。复现命令：

```sh
python3 -B workbench/tests/audit_s3_assertions.py --base 457e02a867bfdc5d8b06a9d14214eb7a429c48c2 --output /tmp/t077-relay-regression-scope-replay.json
bash -n evidence/2026-10-11-batch13/T-077/outside-sandbox.sh
```

这些准备检查不算行为通过。原真实场景仍为 INCOMPLETE、预算已用 **4/4**；本阶段新增真实回合 **0**。没有准备新的真实启动材料。额外真实预算等待用户决定，独立审查按主控要求留到真实场景之后；本 worker 在 READY 后停下等待。
