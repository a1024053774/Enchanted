# 差异检查说明

PASS（产品与测试源码空白检查）：`git diff --cached --check -- workbench` 退出 0。
完整 staged diff 的 `--check` 非零来自保留的原始日志尾部空白、补丁上下文空行，以及 README 三方合并失败原文中的冲突标记；这不是产品文件中的未解决冲突。原始证据不为使检查变绿而重写。

提交后模式检查发现普通 patch 没有恢复 RUN-OUTSIDE-T249.sh 在 C 中的执行位；已按原 C 恢复 100755，文件内容仍逐字节相同。见 mode-restoration.json。
