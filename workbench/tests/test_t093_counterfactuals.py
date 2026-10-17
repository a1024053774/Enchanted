"""Frozen copies only: prove the fact tests reject specific faulty behaviors."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
if output.exists():
    raise SystemExit("preserve earlier evidence")
mutations = [
    ("forward_before_record", "claudeForwarder.ts", 'this.record({ kind: "request", sequence, method: req.method, path,',
     'if (sequence !== 1) this.record({ kind: "request", sequence, method: req.method, path,'),
    ("ignore_home_reference", "claudeLoginFacts.ts", 'if (typeof value === "string") return value.includes(home)',
     'if (typeof value === "string") return false'),
    ("disable_credential_scan", "claudeLoginFacts.ts", 'export function credentialHits(text: string, secrets: readonly string[]) {',
     'export function credentialHits(text: string, secrets: readonly string[]) { return 0;'),
    ("ignore_missing_record", "claudeLoginFacts.ts", 'counts_match: received === requests.length && sequences,', 'counts_match: true,'),
    ("publish_raw_terminal", "claudeLoginFacts.ts", 'export function safeTerminal(raw: string, secrets: readonly string[]) {',
     'export function safeTerminal(raw: string, secrets: readonly string[]) { return raw;'),
    ("hide_preflight", "claudeLoginFacts.ts", 'export function preflightObserved(raw: string) {',
     'export function preflightObserved(raw: string) { return false;'),
]
checks = []
for name, filename, old, new in [("unmodified_control", "", "", ""), *mutations]:
    with tempfile.TemporaryDirectory(prefix="t093-counterfactual-", dir="/private/tmp") as temporary:
        root = Path(temporary)
        (root / "src").mkdir(); (root / "tests").mkdir()
        (root / "package.json").write_text('{"type":"module"}')
        (root / "src/gates").symlink_to(source / "src/gates", target_is_directory=True)
        for module in ("claudeForwarder.ts", "claudeLoginFacts.ts"):
            text = (source / "src" / module).read_text()
            if module == filename:
                assert text.count(old) == 1
                text = text.replace(old, new)
            (root / "src" / module).write_text(text)
        (root / "tests/test_t093_forwarder.ts").write_text((source / "tests/test_t093_forwarder.ts").read_text())
        result = subprocess.run(["/opt/homebrew/bin/node", str(root / "tests/test_t093_forwarder.ts"), str(root / "result.json")],
                                capture_output=True, text=True, timeout=15)
        expected = result.returncode == 0 if name == "unmodified_control" else result.returncode != 0 and "AssertionError" in result.stderr
        checks.append({"name": name, "exit_code": result.returncode, "status": "PASS" if expected else "INCOMPLETE"})
value = {"status": "PASS" if all(row["status"] == "PASS" for row in checks) else "INCOMPLETE", "checks": checks,
         "scope": "isolated source copies; no CLI, auth, or model; raw failure stderr kept in memory only"}
output.write_text(json.dumps(value, indent=2) + "\n")
print(json.dumps({"status": value["status"], "checks": len(checks)}))
raise SystemExit(0 if value["status"] == "PASS" else 2)
