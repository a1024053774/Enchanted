# T-093 probe-02 独立只读审查

STATUS: INCOMPLETE
TARGET: T093-keychain-query-v3；基线 `1d81ac724004aee61c654795a096f545d1a0e8d2`。

来源：干净上下文 reviewer，gpt-6.1-sol / xhigh；按 behavioral-acceptance-review 执行。
只读审查，未修改文件，未执行真实 security、Claude、凭据读取或模型回合。

EVIDENCE:

- 新增定向合成测试通过：精确服务、单一文件、`-w` 位于路径前，profile 与环境不变，只复制 claudeAiOauth，权限 0600，报告无合成 token。
- 独立合成检查确认：缺失文件和三种路径链接均在查询前停止；返回 44 时准确报告“已审范围不可见”。
- PROBE-02.md 区分观察、推断和未知，没有宣称 HOME 已被证明是唯一根因。
  [Apple 命令源](https://github.com/apple-oss-distributions/Security/blob/main/SecurityTool/macOS/security.c)与
  [路径展开代码](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_keychain/lib/DLDBListCFPref.cpp)
  支持该假设，不能证明本机结果。
- probe-01 保留；新命令指向 probe-02.json，输出仍使用独占创建。
- reviewer session 前后 project-map status 均为 0 problems、0 stale living docs。

FINDINGS:

- 未发现阻止交付 probe-02 命令的可复现问题；此次修正没有扩大权限或查询范围。

COUNTEREXAMPLE:

- 三个内存变异均被断言拒绝：省略显式钥匙串、把 `-w` 放到路径后、移除网络 deny。

LIMITATIONS:

- 未运行真实 security、Claude、凭据读取或模型回合。
- 实际 Keychain 查询、复制后的登录识别和本地路由仍为 INCOMPLETE，须由主控运行新探针取得当前候选的真实边界证据。
- 未重测未改变的编排流程。

RULE:

- N/A；无新增重复失败类别。
