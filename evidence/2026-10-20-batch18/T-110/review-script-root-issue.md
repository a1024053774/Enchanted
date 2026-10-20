T-110 第一轮审查提供的 REVIEW-OUTSIDE-01.sh 真实入口分支有一个未运行的夹具配置问题（静态核对，不称已复现）：脚本第 18 行创建 /private/tmp/t110-review-01-* 根，第 109 行附近把 run_t108_native_e2e.py 的 mkdtemp dir 改到该根下。实际原生夹具的绝对路径因此以 /private/tmp/t110-review-01- 开头。

workbench/src/claudeLaunch.ts:37 对本地假 API 的隔离启动要求 root.startsWith('/private/tmp/t078-2-') 且 repo 位于 root/repo；上述路径不满足，预计会先报 isolated_controller_root_required，尚未到达断连业务断言。第一轮只运行了 --local，所以报告未声称该真实入口通过。

建议审查脚本的作者在下一轮脚本中使用满足原产品校验的私有根前缀，不修改产品的隔离根允许范围。本 worker 不改独立审查原件；自己的真实入口已使用 /private/tmp/t078-2-t110-* 私有根并把本轮夹具归并在里面，保留同一校验。
