# /private/tmp 测试夹具清理 01（2026-10-15）

来源：构思主控转达用户选择（逐字）"删三个已关票目录 + 让执行主控清 /tmp (Recommended)"，系统盘仅剩 2.4G。构思主控已删 a2a-wt-t077/t080/t083。

规则（tmp_cleanup.py）：本用户所有；名称匹配 a2a 测试夹具前缀白名单（a2a-、t78/t078/t073、q76、q81obs、t081/t81、t084、t077/t77p、t80、s3f-/s3-、s76、a4r-/a76、m76-、r77-）；不在保留清单（A-09 活现场 t078-2-09b-run-jyat2h5s、其静态 root t078-2-09b-executable-h12u7zgs、claude-501、cc-socks、T-081 作证据保留的 t081-capability-01 与 t081-capability-recheck-01/-02）；30 分钟内无改动；不被任何运行进程命令行引用。非 a2a 项（codex-daemon、socket、chrome 日志、t167 等其他项目、root 所有文件）一律不碰。

结果：dry-run.json 候选 1682（4,515,372,166 字节），0 项含 auth.json/.credentials.json，0 项被进程占用；delete.json 实删 1684（4,515,376,172 字节；两次运行之间又有 2 项满 30 分钟），failed 0、remaining 0。跳过：近期改动 204 项（含 T-081 6e 运行与 T-078 换行回归），保留 5 项。保留的 T-081 夹具已核对无 auth.json。系统盘可用 12G → 17G。近期项待相关运行结束后再清。
