"""产品页验收：在当前目录的 docs/ 上起临时静态服务，跑 check.mjs 和参数里追加的检查脚本。

用法：python3 acceptance/page/run.py [检查脚本 ...]
不带参数时跑 check.mjs；带参数时只跑参数里的脚本（门禁每条命令限时 60 秒，分开跑）。每个检查脚本收到输出目录（argv[2]）与环境变量 PAGE_BASE，全部通过时以 0 退出。
依赖：博客仓库里的 playwright-core 与本机 Playwright 的 Chromium（路径写在 check.mjs）。
"""
import os, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

root = Path.cwd()
checks = [root / arg for arg in sys.argv[1:]] or [Path(__file__).with_name('check.mjs')]
with socket.socket() as s:
    s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '-d', str(root / 'docs')],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
base = f'http://127.0.0.1:{port}/'
try:
    for _ in range(50):
        try: urllib.request.urlopen(base, timeout=1); break
        except OSError: time.sleep(0.1)
    out = Path(tempfile.mkdtemp(prefix='page-check-'))
    failed = []
    for check in checks:
        target = out / check.stem
        result = subprocess.run(['node', str(check), str(target)], env={**os.environ, 'PAGE_BASE': base}, capture_output=True, text=True)
        print(f'{check}: exit {result.returncode}, report {target}/report.json')
        if result.returncode != 0:
            failed.append(str(check)); print(result.stdout[-4000:], result.stderr[-4000:])
    sys.exit(1 if failed else 0)
finally:
    server.terminate()
