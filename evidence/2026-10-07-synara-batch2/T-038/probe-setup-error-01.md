# 首次 HTTP 探针的夹具异常（2026-10-08）

首次命令为 `python3 evidence/2026-10-07-synara-batch2/T-038/http-probe.py membership-red-01 http://127.0.0.1:5811`。urllib 自动跟随了不存在 API 的 302 dev 首页跳转，随后 `URLError: <urlopen error [Errno 61] Connection refused>`。进程 exit 1；异常发生在写 JSON 前，故该次没有 JSON 文件。原始 traceback 保留在本 worker session 的工具输出；没有补称为完整文件证据或产品红态。

同一服务器的 `/ws/negotiate` 返回 200。随后 curl 的首个响应确认 `/api/a2a/membership` 是 `HTTP/1.1 302 Found`、Location `http://localhost:7771/`；Vite 监听 localhost，127.0.0.1:7771 的请求失败。探针改为记录首个响应，不跟随跳转；新的标签 `membership-red-02` 才作为接口合同红态。
