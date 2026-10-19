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
    ("empty_credential_variants", "claudeLoginFacts.ts", 'export function credentialVariants(secrets: readonly string[]) {',
     'export function credentialVariants(secrets: readonly string[]) { return [];'),
    ("ignore_missing_record", "claudeLoginFacts.ts", 'counts_match: received === requests.length && sequences,', 'counts_match: true,'),
    ("publish_raw_terminal", "claudeLoginFacts.ts", 'export function safeTerminal(raw: string, secrets: readonly string[]) {',
     'export function safeTerminal(raw: string, secrets: readonly string[]) { return raw;'),
    ("hide_preflight", "claudeLoginFacts.ts", 'export function preflightObserved(raw: string) {',
     'export function preflightObserved(raw: string) { return false;'),
    ("empty_injection_cases", "test_t093_forwarder.ts", '\n];\nconst assertCredentialFree',
     '\n].slice(0, 0);\nconst assertCredentialFree'),
    ("skip_injection_loop", "test_t093_forwarder.ts", 'for (const fixture of fixtureVariants) {\n    writeFileSync',
     'for (const fixture of []) {\n    writeFileSync'),
    ("omit_injection_write", "test_t093_forwarder.ts", 'writeFileSync(leak, fixture.value);',
     '// MUTANT: omit injection write.'),
]
required_assertions = {
    "empty_credential_variants": "credential injection must be detected",
    "empty_injection_cases": "credential injection cases must not be empty",
    "skip_injection_loop": "credential injection must execute at least one case",
    "omit_injection_write": "credential injection file must exist",
}
checks = []
for name, filename, old, new in [("unmodified_control", "", "", ""), *mutations, ("pre_control_payload_fix", "", "", "")]:
    with tempfile.TemporaryDirectory(prefix="t093-counterfactual-", dir="/private/tmp") as temporary:
        root = Path(temporary)
        (root / "src").mkdir(); (root / "tests").mkdir()
        (root / "package.json").write_text('{"type":"module"}')
        (root / "src/gates").symlink_to(source / "src/gates", target_is_directory=True)
        for module in ("claudeForwarder.ts", "claudeLoginFacts.ts"):
            text = (source / "src" / module).read_text()
            if name == "pre_control_payload_fix" and module == "claudeLoginFacts.ts":
                text = subprocess.run(["git", "show", "ff625c371:workbench/src/claudeLoginFacts.ts"], cwd=source,
                                      capture_output=True, text=True, check=True).stdout
            if module == filename:
                assert text.count(old) == 1
                text = text.replace(old, new)
            (root / "src" / module).write_text(text)
        test = (source / "tests/test_t093_forwarder.ts").read_text()
        if filename == "test_t093_forwarder.ts":
            assert test.count(old) == 1
            test = test.replace(old, new)
        (root / "tests/test_t093_forwarder.ts").write_text(test)
        result = subprocess.run(["/opt/homebrew/bin/node", str(root / "tests/test_t093_forwarder.ts"), str(root / "result.json")],
                                capture_output=True, text=True, timeout=15)
        business_assertion = "AssertionError" in result.stderr
        required = required_assertions.get(name)
        if required:
            business_assertion = business_assertion and required in result.stderr
        expected = result.returncode == 0 if name == "unmodified_control" else result.returncode != 0 and business_assertion
        checks.append({"name": name, "exit_code": result.returncode, "status": "PASS" if expected else "INCOMPLETE",
                       "expected_business_assertion": required,
                       "business_assertion_observed": business_assertion,
                       "fixture_missing_error": "ENOENT" in result.stderr})
value = {"status": "PASS" if all(row["status"] == "PASS" for row in checks) else "INCOMPLETE", "checks": checks,
         "scope": "isolated source copies; no CLI, auth, or model; raw failure stderr kept in memory only"}
output.write_text(json.dumps(value, indent=2) + "\n")
print(json.dumps({"status": value["status"], "checks": len(checks)}))
raise SystemExit(0 if value["status"] == "PASS" else 2)
