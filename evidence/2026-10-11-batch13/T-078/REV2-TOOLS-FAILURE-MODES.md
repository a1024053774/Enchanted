# rev2 测试工具的失败方式（主控 #339）

本轮只改测试工具。Tracer bullet 是“实际文件/分页读屏 → 判定 → 一次副作用 → 原件收据”；Deep modules 以原件归档与条件按键两个接口隐藏核对细节；Ubiquitous language 沿用 POST、hook、pending/delivered、control action。不改产品、protocol、预算，不启动真实角色 CLI 或模型。后续源码绑定仍等 T-090 合并。

归档失败方式：只保留 summary；漏失败/重试/未完成记录；认证头泄漏；脱敏吞掉整条业务正文；成员缺失、多出、类型变或字节不符；归档未读回就停机；独立读回未签；PID/argv/lstart/root 不符；API 身份串用；停机时产生新 hook/POST；停机后再读 SQLite；重复信号/重复删除；外置盘不可用时回退。验收以普通文件逐字节、完整成员集、生命周期调用日志和 root 是否存在为准，不以工具自报 PASS 为准。

09C 失败方式：伪造或重置 created_at；墙钟跳变；单调时钟不足；超 130 秒才开始 Enter 或超 150 秒结算；期间收到 ack/撤销要求/目标换身份；读一页或没有 EOF；total 改变/零进度；模板与实际 command/argv/stop/target/launch/session/prompt/dispatch/global seq/permission/window/generation 任一不符；误选永久许可；未知写入后重试；控制字节记 message；API 额外 POST/重试被漏计；把早期拒绝或排队当实际中断。

新工具先跑同一契约入口，缺实现标为“新增契约尚未实现”红态，不称为旧产品缺陷。实现后用真实临时文件、严格 reader、确定性窗口/生命周期替身取绿及拒绝反例；再用去掉关键检查的坏实现证明 oracle 会失败。真实 loopback HTTP 和 >120 秒时钟排练交沙箱外脚本，未运行前明确 INCOMPLETE。夹具时间注入只用于边界单测，不能作为真实时钟证据。
