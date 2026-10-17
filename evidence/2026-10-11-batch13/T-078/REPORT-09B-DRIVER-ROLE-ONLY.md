# 主控 #189：role_file 单路径收紧交接

已先保存双路径旧实现红态：`root/role.md` 被接受，结果见 `09b-role-file-red/results.json`。现已删除 fallback，`claudeLaunch` 只接受 `roles/<preset>/role.md`；root role card 绿态拒绝为 `controller_launch_config_required`，见 `09b-role-file-green-rejection/results.json`。

P1 generator、run_p1、profile/budget tests 已迁到 preset role card；旧 root role 不再创建。新输出目录重跑：profile、6-root budget、slice1 relay22、permission3、entry6、empty17、driver red/green 和 seq-reset/identity/duplicate-esc 反例均保存并通过对应 oracle。旧目录保留。

提交脚本 [commit-09b-driver.sh](commit-09b-driver.sh) allowlist 已加入 role boundary test、role-only 输出、README 和最新 driver evidence；预检无 unowned 文件，shell/diff/node/Python 语法检查通过。脚本首提交后静态生成 `09b-executable-materials-01`，source tar、双 role approval、独立目录、target card oracle_paths 和空审批，明确 `launch_status=NO_GO`；不启动任何真实 CLI/API/目标。

主控请运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-driver.sh
```

T-078 09B-DRIVER READY
