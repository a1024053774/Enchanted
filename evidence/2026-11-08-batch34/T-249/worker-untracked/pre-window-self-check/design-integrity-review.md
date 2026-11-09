STATUS: PASS
SUMMARY: 限定结构自查未发现已复现缺陷。按任务卡在实现会话内自查；不是主控安排的干净只读独立审查。
TARGET: scoped-repair.patch；起点 18c108fcaed1c4ecf51831f2272578a3b09427be，仅三个产品文件及两份开发测试的新改动。
FINDINGS:
- 无。
LIMITATIONS:
- 扫描器标记 GitGraphPanel.tsx:285 的 catch。该边界原 C 已有，负责把当前 diff 读取错误显示给用户；此次增加选择身份核对，过期结果不覆盖新选择。没有吞掉当前请求的错误，没有新增重试或替代数据源。
- gitHost.ts 只为精确 no-index 形式把 Git 文档规定的“有差异”退出码 1 且无 stderr 转为既有 GitResult 成功码；不是出错后假装成功。独立 Git 探针与真实宿主场景验证过这一形式。
- 路径约束在实际执行 Git 的主进程，diffArgs 只生成参数，沿用既有接口与展示层，没有平行 API。文本预期由原始文件与独立 Git 命令给出。
- 不重新审原 C 的整套面板、RUN-OUTSIDE 或其他设计；恢复一致性见 scope-check.json。新窗口、迟到结果和几何断言尚待沙箱外执行；此结构自查不证明它们已经通过。
RULE:
- 新增读取路径必须通过同一个 gitRead 边界，并由 test_t249_git_host.mjs 的真实 Git 与元数据字节检查验证；不靠子命令名或源码字符串证明只读。
