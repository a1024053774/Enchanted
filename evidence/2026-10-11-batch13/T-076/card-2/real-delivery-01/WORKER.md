# T-076-2 真实受管夹具worker

只做本任务，不读凭据/用户配置/a2a源码，不联网、不启动子agent，不增加回合或修改权限。任务是带一次明确失败的协议实验，最终代码必须满足CONTRACT.txt。

第一次主输入只将src/clamp.py写成下面这个故意漏掉bool排除的版本，提交一次并显式submit，request-id为delivery-1；不要在这一回合修复该已知缺口。不能改合同、oracle、host.txt、.gitignore或.a2a。完整完成条件会由执行主控在回执回合结束后运行并打回。

```python
def clamp(value):
    if not isinstance(value, int):
        raise ValueError("not_int")
    return max(0, min(100, value))
```

git add src/clamp.py与git commit -m "Fixture C1: bool rejection missing"各自是独立工具命令，cwd设为本attempt工作目录；不能和cd、检查命令或彼此拼接。Git尾注由会话hook写入，不能伪造。提交后用派发给你的完整CLI命令显式submit（加--request-id delivery-1），随后结束回合，让匹配Stop转交B文件。queued不是通过，不直接连接socket。

收到“仅确认收到”的回执时只确认并结束，不调用任何工具、不写文件、不新增请求。收到带quality-repair的“门禁检查未通过”时才修复：按CONTRACT.txt完整实现、运行卡上的完成条件、独立git add/commit、重新取得完整SHA并显式submit，request-id为delivery-2；只做一次修复提交，保持原attempt及原生会话。没有修复指令不能另交C。第二次回执也只确认，不调用工具。

独立命令被沙箱拒绝或协议无法核对时结束并报告，不提权、不重试或加规则。主控会停止整个夹具并保留现场。
