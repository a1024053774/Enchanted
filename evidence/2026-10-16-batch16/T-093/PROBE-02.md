# T-093 probe-02 查询目标修正（2026-10-17）

状态：INCOMPLETE。probe-02 尚未执行；只修探针，不写产品代码，不运行真实模型回合。
task T-093 / attempt a1 / session `67f986cc-92e4-4089-9c22-802a1143b645` / ready_rev 1。
修正起点 `1d81ac724004aee61c654795a096f545d1a0e8d2`；本轮未收到新 fence 值。

目标：让原本已存在的同一精确服务查询，显式使用一个已核对的钥匙串文件；保留全部权限限制。
非目标：扩大 Mach、文件读写、网络、fork 权限，改变 CLI 的 HOME，枚举其他条目，修改门禁或产品。
验收：命令限定同一服务和一个文件，profile、环境不变，只复制登录对象；真实成功仍以主控返回的新探针结果为准。

## 证据与判断

- **observed**：`probe-01.json` 为主控在沙箱外执行的原始摘要，rc 2，`login_credential_not_found`；
  本地与真实上游请求均为 0，凭据扫描命中 0，隔离目录已删除。
- **observed（主控 #58 原话）**：执行 `security find-generic-password -s "Claude Code-credentials"`，
  “不带 -w，没有读取密码，输出丢弃”，rc 0。这个对照与 probe-01 的 HOME/profile 并不相同，不能只归因于其中一项。
- **observed**：精确 security 查询使用的 profile 是 `(version 1)(allow default)(deny file-write*)(deny network*)(deny process-fork)`，
  没有 Mach 拒绝规则。Security 名称正则拒绝仅位于 CLI 的另一个 profile。因此没有添加 Mach allow 的依据。
- **observed**：本 worker 只读 lstat 确认 `~/Library/Keychains/login.keychain-db` 是普通文件、不是最终路径符号链接；未读取正文。
- **source**：Apple 的 [security 命令源](https://github.com/apple-oss-distributions/Security/blob/main/SecurityTool/macOS/security.c)
  说明未指定钥匙串时使用默认搜索列表；
  [DLDBListCFPref.cpp](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_keychain/lib/DLDBListCFPref.cpp)
  的 `getPwInfo`/`ExpandTildesInPath` 会用 HOME 展开用户路径。
- **inferred**：隔离 HOME 使默认搜索位置不同，是当前最小解释；尚未证明它是本机该次失败的唯一原因。
- **unknown**：单一显式文件查询能否在原限制下成功，以及复制后的登录识别与本地路由是否可用。

## 变更与边界

精确元数据查询改为：

```text
/usr/bin/security find-generic-password -s Claude Code-credentials <真实HOME>/Library/Keychains/login.keychain-db
```

仅在成功后，以 `-w` 位于路径前的同一命令读该条目，内容只留内存并写入隔离 HOME 的登录凭据副本。
显式路径将搜索缩到一个文件，不增加服务名、不列举其他条目。该路径或 Library/Keychains 祖先为链接、文件缺失时停止。
原来的 readonly profile、隔离 HOME 与清理规则保持不变。不会把 HOME 设回真实 HOME，不取消任何 deny。
若仍返回 44，报告“在已审范围不可见”，不再推断“登录凭据不存在”；报告额外保存精确查询与读密码步骤的退出码，始终丢弃原始 stdout/stderr。
不自动尝试其他钥匙串或无 profile 查询。需要额外权限时停下交主控。

probe-01 的一处 JSONL 差异保留。主控已说明它来自 sitecraft-ai 中用户正在运行的 Claude 会话；
此说明按主控提供的信息记录。脚本继续列出差异并“不推断因果”，不增加排除项或把有差异报告改成 PASS。

## 主控在沙箱外执行

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-02.json
```

输出须为新文件，脚本使用 `open(..., "x")`，不会覆盖 probe-01 或已存在的 probe-02。
本 worker 没有执行该命令，没有调用真实 security/Claude，也没有请求升级。

## 本地验证

失败方式：遗漏显式钥匙串、丢失精确服务限制、放宽 profile、改变 HOME、复制非 auth 内容或泄漏 token。
新增合成检查在修正前以 `AssertionError: 'login_credential_not_found' is not None` 失败，记录见 `keychain-query-red-01.json`；
修正后同一检查通过。它核对完整命令、原 profile 和环境、文件 0600、只复制 claudeAiOauth，以及报告不含合成 token。
capture 为合成边界，不据此宣布实际 Keychain 通过；真实 probe-01 与主控对照是已有外部证据。
完整辅助套件及单点反例另存新的 `probe-helper-checks-05.json`，不覆盖此前结果。
