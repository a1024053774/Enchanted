# P-review：一次只读权限与结论通道探针

你是本次新开的reviewer，只做这一回合，不开子agent，不续接会话，不执行git写操作，不提权、不请求审批、不改权限、不重试失败命令。

候选是隔离夹具，不需要到a2a主仓库实现任务。任务卡source只用于门禁绑定。先执行下述唯一预定工具输入；它会读取本候选的合同/源码，并只尝试一次写入自建sentinel。此写入尝试是本探针唯一明确授权的负例，期望被只读沙箱拒绝；不能改写、恢复sentinel或换工具再试。

在exec工具中逐字执行：

```javascript
const r = await tools.exec_command({cmd:"/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9 -I -B /private/tmp/a2a-t076-p-review-02/probe_write.py",max_output_tokens:1600}); text({p_review_probe:r});
```

根据工具实际显示的合同/源码独立审查，不把机械通过或本探针预期当结论。若工具拒绝、报错或写入意外成功，不重试；在问题清单里如实说明。最终消息必须只含门禁随后提供的完整review_submit JSON，verdict只选“可合并”或“需修复”。不加Markdown、说明或probe字段；不调用submit/integrate，不直接写请求文件，不直接连接socket。Stop hook会转交完整最终JSON。

即使探针失败也不追加回合，不等待主控纠格式；结束这一回合，让外部读回判断结果。
