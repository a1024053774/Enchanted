# T-203: does a real Codex session (real model, isolated CODEX_HOME) see and call the reviewer's review_submit MCP tool?
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
out = Path(sys.argv[1]); assert not out.exists()
home = Path(tempfile.mkdtemp(prefix='t203-real-codex-home-', dir='/private/tmp'))
work = Path(tempfile.mkdtemp(prefix='t203-real-codex-work-', dir='/private/tmp'))
req = Path(tempfile.mkdtemp(prefix='t203-real-req-', dir='/private/tmp'))
report = dict(home=str(home), work=str(work), request_dir=str(req))
try:
    shutil.copyfile(Path.home() / '.codex/auth.json', home / 'auth.json'); (home / 'auth.json').chmod(0o600)
    (home / 'config.toml').write_text(f'[projects."{work}"]\ntrust_level = "trusted"\n')
    (req / 'review-template.json').write_text('{"schema": 1}\n')
    node = shutil.which('node')
    src = '/Users/luckye/Documents/Code/a2a/workbench/src/reviewResult.ts'
    mcp = ['-c', f'mcp_servers.enchanted.command={json.dumps(node)}', '-c', 'mcp_servers.enchanted.args=' + json.dumps([src, 'mcp', str(req)]),
           '-c', 'mcp_servers.enchanted.env={ELECTRON_RUN_AS_NODE="1"}', '-c', 'mcp_servers.enchanted.default_tools_approval_mode="approve"']
    prompt = ('T-203 实测：调用 enchanted MCP 服务器的 review_submit 工具一次，参数 verdict 为 "可合并"，findings 为空数组，'
              'report 为 {"完成条件与变异检查": "探针"}。不要运行 shell 命令。工具返回后把返回内容原样告诉我。')
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'LANG') if k in os.environ}; env['CODEX_HOME'] = str(home)
    argv = ['codex', 'exec', '--skip-git-repo-check', '-C', str(work), '-s', 'read-only', '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort=high', *mcp, prompt]
    report['argv'] = argv[:-1] + ['<prompt>']
    run = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    report.update(returncode=run.returncode, stdout=run.stdout[-4000:], stderr=run.stderr[-6000:])
    rollouts = list((home / 'sessions').rglob('rollout-*.jsonl'))
    calls = []
    for path in rollouts:
        for line in path.read_text().splitlines():
            row = json.loads(line); p = row.get('payload', {})
            if p.get('type') in ('custom_tool_call', 'function_call', 'custom_tool_call_output', 'function_call_output', 'mcp_tool_call_end') or 'review_submit' in json.dumps(p, ensure_ascii=False)[:20000] and row.get('type') == 'response_item':
                calls.append(json.dumps(p, ensure_ascii=False)[:1500])
    report['tool_items'] = calls
    report['result_file'] = (req / 'review-result.json').read_text() if (req / 'review-result.json').exists() else None
finally:
    for d in (home, work, req): shutil.rmtree(d, ignore_errors=True)
    report['removed'] = not home.exists()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report.get('returncode'), len(report.get('tool_items', [])))
