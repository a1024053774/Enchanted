"""T-243 triage: run each standalone non-Fixture test once and list processes it left behind.
A leftover is a process that started while the test ran, is still alive after it exits, and whose executable is
under /tmp or /private/tmp or whose HOME (ps -E) is there (the directory itself may already be deleted). This
session's own scratch directories (/private/tmp/claude-*) are excluded. Leftovers are recorded, then stopped (SIGTERM, then
SIGKILL), so the next test starts clean. Usage: triage.py OUTPUT_DIR [test-name ...]"""
import json, os, signal, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / 'workbench/tests'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

def tests(o):
    d, f = str(o / 'out'), str(o / 'summary.json')
    return {
        'test_daemon_recovery_e2e.py': ['--output', d], 'test_orchestrator_e2e.py': ['--output', d],
        'test_t078_cards_host_bootstrap.py': ['--output', d], 'test_t078_inbox_entry.py': ['--output', d],
        'test_t081_archive_ownership.py': ['--output', d], 'test_t081_duplicate_input.py': ['--output', d],
        'test_t078_input_entry.py': ['--source', str(ROOT), '--output', d],
        'test_electron_e2e.py': ['--source', str(ROOT), '--output', d, '--stage', 'window'],
        't078_input_failures.py': [d], 'test_t156_quality_host_credentials.py': ['--output', d],
        'test_t230_terminal_hc_isolation_e2e.py': ['--output', d],
        **{name: ['--summary', f] for name in ['test_t118_shell_env_e2e.py', 'test_t121_role_request_e2e.py',
            'test_t122_claude_worker_e2e.py', 'test_t123_project_identity_e2e.py', 'test_t124_controller_e2e.py',
            'test_t126_terminal_socket_e2e.py', 'test_t127_codex_home_e2e.py', 'test_t131_parallel_workers_e2e.py',
            'test_t193_multi_project_e2e.py', 'test_t195_native_link_e2e.py', 'test_t198_out_of_card_e2e.py',
            'test_t237_retrospective_end_e2e.py', 'test_t239_pane_invalid_utf8_e2e.py']},
        # Second round (one-off batch drivers whose inputs can be built here): the installed Electron dist.
        **{name: ['--source', str(ROOT), '--electron-dist', str(ROOT / 'workbench/node_modules/electron/dist'), '--summary', f]
           for name in ['run_t109_hierarchy.py', 'run_t111_flow.py']},
        'run_t108_native_e2e.py': ['--summary', f, '--electron-dist', str(ROOT / 'workbench/node_modules/electron/dist')],
        **{name: [f] for name in ['test_t096_archive_failed_02.py', 'test_t096_fixed_cleanup.py', 'test_t096_red_startup.py',
            'test_t096_restart_cleanup.py', 'test_t096_version_cleanup.py']},
    }

def dirs():
    # Never another tool's working directories (this session's scratchpad lives under /private/tmp/claude-*).
    return {str(p) for base in ('/private/tmp',) for p in Path(base).iterdir() if p.is_dir() and not p.name.startswith(('claude', 'com.apple'))}

def pids():
    return {int(l.split()[0]) for l in subprocess.run(['/bin/ps', '-axo', 'pid='], capture_output=True, text=True).stdout.split()}

def holders(earlier):
    listing = subprocess.run(['/bin/ps', '-axE', '-ww', '-o', 'pid=,command='], capture_output=True, text=True).stdout
    found = {}
    for line in listing.splitlines():
        pid = int(line.split(None, 1)[0])
        if pid == os.getpid() or pid in earlier:
            continue
        # Only a fixture's own processes: its executable is under /tmp (state/hc/bin/herdr-core), or its HOME is a
        # fixture directory (zsh and CLIs in fixture panes). Any /tmp path in the environment is not enough: the
        # first run killed two of the user's ssh ProxyCommand processes (Tailscale nc) whose environment named
        # SSH_AUTH_SOCK=/private/tmp/com.apple.launchd...
        command = line.split(None, 1)[1] if ' ' in line.strip() else ''
        if command.startswith(('/private/tmp/claude-', '/tmp/claude-')):
            continue
        if command.startswith(('/private/tmp/', '/tmp/')) or any(f' HOME={base}' in line and f' HOME={base}claude-' not in line
                                                                 for base in ('/private/tmp/', '/tmp/')):
            found[pid] = 'tmp'
    if not found:
        return []
    shown = subprocess.run(['/bin/ps', '-ww', '-o', 'pid=,ppid=,command=', '-p', ','.join(map(str, found))], capture_output=True, text=True).stdout
    return [dict(line=l.strip()[:300], fixture=found.get(int(l.split()[0]))) for l in shown.splitlines() if l.strip()]

names = sys.argv[2:] or sorted(tests(out))
for name in names:
    o = out / name.removesuffix('.py'); o.mkdir(exist_ok=True)
    argv = [sys.executable, str(T / name), *tests(o)[name]]
    env = dict(os.environ, ENCHANTED_HC_CACHE_DIR=str(ROOT.parent / 'hc-cache'))
    before = dirs(); earlier = pids(); started = time.time()
    try:
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=900, start_new_session=True)
        code, tail = run.returncode, (run.stdout + run.stderr)[-3000:]
    except subprocess.TimeoutExpired as expired:
        code, tail = 'timeout', str(expired)[-3000:]
    time.sleep(2)
    new = sorted(dirs() - before)
    left = holders(earlier)
    for item in left:
        try: os.kill(int(item['line'].split()[0]), signal.SIGTERM)
        except ProcessLookupError: pass
    time.sleep(1)
    for item in holders(earlier):
        try: os.kill(int(item['line'].split()[0]), signal.SIGKILL)
        except ProcessLookupError: pass
    record = dict(test=name, argv=argv, exit=code, seconds=round(time.time() - started), new_dirs=new, leftovers=left, tail=tail)
    (o / 'triage.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(test=name, exit=code, seconds=record['seconds'], leftovers=len(left),
                          kinds=sorted({l['line'].split()[2].rsplit('/', 1)[-1] for l in left}))), flush=True)
