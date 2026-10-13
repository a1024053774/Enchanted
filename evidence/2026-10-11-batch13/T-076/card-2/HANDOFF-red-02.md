# T-076-2：red-02 沙箱外交接

状态：**INCOMPLETE**。主控 #34 回传的red-01已核对：stage-1 PASS；stage-2取得9个预写契约红态，在第10项夹具读取错误处停止；第11项和stage-3未运行。真实Codex仍 **0/8**，产品源码未改。

## 诊断与修正

原始证据保持在[red-01 stage-2](outside-red-01/stage-2/)；不改其报告、输出或归档。`red_run_reject_preserves_worker/run-result.json`显示`oracle_failed`、`verification_failed`和`reclaimed=true`；数据库读回的原attempt为`revoked/reclaimed=true`，事件58–63记录完成条件失败、拒收、reclaim意图、撤销、reclaimed和run结束。任务变为ready、current_attempt=null、Git仍为认领起点。

这与旧产品`run → reclaim → invalidate`代码相符，是批准计划已经预期的起点行为。夹具在形成RED-RUN-REPAIR前直接对null取下标，故为测试错误，不是额外产品协议异常。

只修改`workbench/tests/test_quality_chain_e2e.py`：

- RED-RUN-REPAIR先保存完整run/task/ref及原attempt历史，再检查当前attempt存在、仍为原ID、reclaimed严格为false且ref未变。current_attempt为空或被替换均形成业务失败。
- 同样保护两个相关绑定断言RED-FEEDBACK.identity、RED-RESUBMIT.binding，避免“原attempt丢失”被误报为TypeError；各自原成功条件不放松。
- 不捕获TypeError来硬改状态，不伪造current_attempt，不改产品回收行为、不改旧acceptance断言。

修改前源码、诊断、局部diff及离线复放在[harness-repair-01](harness-repair-01/)中。离线使用原readback执行修改前/后的**实际断言方法**：前者TypeError且没有断言，后者记录RED-RUN-REPAIR失败并保存读回。该检查PASS只证明夹具分类修复，不计为第10项新的真实入口红态，也不改red-01的INCOMPLETE。

## 按新标签重新冻结

脚本本身不需修改；它会拒绝混用旧冻结测试。请依次执行，每阶段核对报告后再运行下一条：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-1 red-02
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-2 red-02
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-3 red-02
```

新输出为`outside-red-02/`，目前尚不存在/未运行。完整阶段边界、受控面、停止和归档要求沿[首次交接](HANDOFF-red-01.md)，不启用真实P-review、模型、auth复制或hook安装。遇新的夹具/真实协议异常仍保存现场并停下回传。
