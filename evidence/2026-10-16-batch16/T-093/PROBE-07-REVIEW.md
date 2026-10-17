# T-093 probe-07 冻结候选独立隐私审查（2026-10-17）

审查员 `/root/terminal_export_review`，gpt-6.1-sol / xhigh，新上下文、只读。
保留原始 FAIL，不因后续 worker 修正改写结论。

```text
STATUS: FAIL
TARGET: T093-export-v8；基于 c7cf6e434fbe1b4784d38156c0cc8e4014ebd69f 的冻结未提交候选。
EVIDENCE:
- 已读 PROBE-07.md、候选源码、测试及合成检查摘要。
- 单项测试 python3 -B workbench/tests/test_t093_probe_safety.py ProbeSafety.test_terminal_export_redacts_variants_identities_and_preserves_diagnostics 通过。
- 独立随机哨兵验证：标准凭据形式及已知身份被替换；文件为 0600，诊断保留，返回指标无正文。
- 独立反例经实际 write_terminal_output 写入自己的临时目录，以下两类敏感内容均未被阻断；目录已清理。
FINDINGS:
- [P1] workbench/tests/probe_t093_normal_login.py:52 — URL 变体仅使用 quote 生成的大写百分号编码。
  将同一已知凭据的 %2F/%2B/%3F 改为等价的 %2f/%2b/%3f 后，正文原样写出，written=true、credential_scan_hits=0。
  替换与扫描共享同一遗漏。应按百分号转义的大小写等价关系匹配和扫描。
- [P1] workbench/tests/probe_t093_normal_login.py:93 — 标签和欢迎语规则要求行首只有空白，遗漏终端边框前缀。
  │ Welcome back, <随机账号>! │、│ Account: <随机账号> │ 均保留账号；前者已实际写盘。
  这是有标签身份，属于交接声明的识别范围。应识别受支持的终端装饰前缀后再执行标签匹配。
COUNTEREXAMPLE:
- 小写百分号编码：独立 unquote 确认仍还原为已知凭据；导出未拒绝。
- 带 │ 前缀的欢迎语及账号标签：随机账号未替换，扫描为零。
- 无填充 base64 也在内存检查中保留；未据此扩大上述主要结论。
LIMITATIONS:
- 未运行真实 Claude、真实探针、网络或沙箱应用；未读取真实凭据、额外身份来源或指定终端文件。
- 实际 probe-07 的隐私边界仍无运行证据；合成通过不能证明真实导出安全。
- 未修改候选、运行整套测试或重复变异检查。
RULE:
- 在 test_t093_probe_safety.py 增加独立生成的大小写混合百分号编码和带终端边框的标签/欢迎语反例；
  预期禁止值不得来自生产 secret_variants。随 check-probe.py 在真实导出前运行。
```

worker 后续处理：`terminal-export-review-red-07.json` 保存新增反例在冻结候选上的失败。
URL 百分号十六进制统一为大写（不改普通字符），替换和全部凭据扫描共用同一规则；补充普通/URL-safe base64 及无填充形式。
标签与欢迎语支持 ASCII 管道、加号及 Unicode 盒线前缀。新增单点变异分别恢复大小写遗漏、边框遗漏和无填充遗漏。
`probe-helper-checks-15.json` 保留了无填充反例未改变输入的缺口，相关修正复验见 `probe-helper-checks-16.json`。
追加 ANSI 合同红态及最终复验分别见 `terminal-export-ansi-red-07.json`、`probe-helper-checks-17.json`。
这是 worker 复验，未再次独立审查，真实边界仍为 INCOMPLETE。
