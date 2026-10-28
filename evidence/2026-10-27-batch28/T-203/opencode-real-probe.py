# T-203: does a real opencode session (user's own HOME and login, T-187) see and call the reviewer's review_submit MCP tool
# given through OPENCODE_CONFIG_CONTENT, as the managed reviewer launch gives it (terminalClis.ts)?
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
out = Path(sys.argv[1]); assert not out.exists()
work = Path(tempfile.mkdtemp(prefix='t203-real-opencode-work-', dir='/private/tmp'))
req = Path(tempfile.mkdtemp(prefix='t203-real-opencode-req-', dir='/private/tmp'))
report = dict(work=str(work), request_dir=str(req))
try:
    (req / 'review-template.json').write_text('{"schema": 1}\n')
    src = '/Users/luckye/Documents/Code/a2a/workbench/src/reviewResult.ts'
    config = {'mcp': {'enchanted': {'type': 'local', 'command': [shutil.which('node'), src, 'mcp', str(req)], 'environment': {'ELECTRON_RUN_AS_NODE': '1'}}}}
    prompt = ('T-203 实测：调用 enchanted MCP 服务器的 review_submit 工具一次，参数 verdict 为 "可合并"，findings 为空数组，'
              'report 为 {"完成条件与变异检查": "探针"}。不要运行 shell 命令。工具返回后把返回内容原样告诉我。')
    env = dict(os.environ, OPENCODE_CONFIG_CONTENT=json.dumps(config))
    argv = ['opencode', 'run', '--standalone', '--auto', '--format', 'json', prompt]
    report['argv'] = argv[:-1] + ['<prompt>']; report['config'] = config
    run = subprocess.run(argv, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    redact = lambda t: re.sub(r'[\w.+-]+@[\w-]+(\.[\w-]+)+', '<email>', t)
    report.update(returncode=run.returncode, stdout=redact(run.stdout[-12000:]), stderr=redact(run.stderr[-3000:]))
    report['tool_calls'] = [l[:1500] for l in run.stdout.splitlines() if 'review_submit' in l and '"tool' in l]
finally:
    for d in (work, req): shutil.rmtree(d, ignore_errors=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report.get('returncode'), len(report.get('tool_calls', [])))
