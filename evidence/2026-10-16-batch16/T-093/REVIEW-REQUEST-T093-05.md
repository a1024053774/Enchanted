# T-093 平级 profile 边界探针冻结 05

**INCOMPLETE：权限已明确，等待 OS 边界实测；这不是可验收、集成或关闭的产品候选。**
task T-093 / attempt a1 / ready_rev 1，worker s16-t093；session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
最后交接的 FROZEN SHA 绑定本快照，不代替 submit 或独立审查。

主控 #83 已决定 F 的独立受保护进程与配置上游网络权限，旧请求 04 的授权问题已解决。当前不再询问此权限。
尚待核对的是新 OS profile 组合本身；嵌套失败已说明不能只依据脚本语法声称产品可用。实施前方案、每个进程的 profile 和反例预期见 [计划 02](PARALLEL-PROFILES-PLAN-02.md)。

本快照新增无凭据边界探针与本地端点夹具，只验证独立 F/C、单端口、目录写限制、真实 HOME 拒写和合成删规则。没有修改产品源码、原审查或既有链断言；新产品改造和全链证据仍待完成，不能拿旧 PASS 补足。

主控在沙箱外执行，参数中的 SHA 使用本次最终 FROZEN 完整值，输出选择全新路径：

```sh
bash evidence/2026-10-16-batch16/T-093/PROBE-PARALLEL-01.sh \
  /Users/luckye/Documents/Code/a2a-wt-t093 \
  FULL_FROZEN_SHA \
  /private/tmp/t093-parallel-profile-01.json
```

日志如需重定向，只能放真实 HOME 外。脚本不读 auth、不启动供应商 CLI、不用模型协议、不访问真实接口。它会尝试独占创建真实 HOME 新文件，要求拒绝；合成删规则变异会实际创建、立即删除自己的唯一文件并记录删除。
输出保留首个业务失败，清理另外记录；元数据差异只报告。结果回来后继续产品路径改造，不再重复询问已定权限；若探针需要扩大权限才能通过，保持 INCOMPLETE 回主控。
