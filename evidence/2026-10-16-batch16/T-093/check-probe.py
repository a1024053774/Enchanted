#!/usr/bin/env python3
"""用合成数据验证探针辅助检查和单点反例。不得执行真实凭据探针。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).absolute()
    if output.exists() or not output.parent.is_dir():
        raise SystemExit("输出须为已有目录中的新文件。")
    repo = Path(__file__).resolve().parents[3]
    source = repo / "workbench/tests/probe_t093_normal_login.py"
    test = repo / "workbench/tests/test_t093_probe_safety.py"
    original = source.read_text(encoding="utf-8")
    cases = [
        ("scanner_omits_secrets", "return sum(data.count(value) for value in variants if value)", "return 0",
         "test_scanner_detects_sentinel_and_encoded_forms"),
        ("sink_accepts_wrong_bearer", 'self.headers.get("Authorization") == "Bearer " + expected', "True",
         "test_real_sink_separates_matching_and_wrong_bearer_without_leak"),
        ("inventory_omits_scope", "for scope in SCOPES:", "for scope in ():",
         "test_inventory_detects_metadata_change_without_following_symlink"),
        ("timeout_reported_as_success", 'raise StopProbe("command_timeout") from None', 'return 0, b"", b""',
         "test_capture_stops_a_process_that_ignores_sigterm"),
        ("sink_reloads_writable_credential", 'self.headers.get("Authorization") == "Bearer " + expected',
         'self.headers.get("Authorization") == "Bearer " + json.loads((root / "home/.claude/.credentials.json").read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]',
         "test_real_sink_separates_matching_and_wrong_bearer_without_leak"),
        ("keychain_uses_isolated_default_search_scope", 'guarded(read_only, [*command, str(keychain)])',
         'guarded(read_only, command)',
         "test_exact_keychain_query_uses_one_explicit_keychain_with_unchanged_guards"),
    ]
    records = []
    baseline = subprocess.run([sys.executable, str(test)], cwd=repo, capture_output=True, text=True, timeout=20)
    records.append({"case": "baseline", "exit_code": baseline.returncode,
                    "stdout": baseline.stdout, "stderr": baseline.stderr})
    valid = baseline.returncode == 0
    for name, before, after, method in cases:
        if original.count(before) != 1:
            raise SystemExit("变异目标不唯一，停止。")
        with tempfile.TemporaryDirectory(prefix="t093-probe-mutant-") as temp:
            root = Path(temp)
            (root / source.name).write_text(original.replace(before, after), encoding="utf-8")
            (root / test.name).write_text(test.read_text(encoding="utf-8"), encoding="utf-8")
            result = subprocess.run([sys.executable, str(root / test.name), "ProbeSafety." + method],
                                    cwd=root, capture_output=True, text=True, timeout=15)
            caught = result.returncode == 1 and "FAIL:" in result.stderr and "AssertionError" in result.stderr
            valid = valid and caught
            records.append({"case": name, "exit_code": result.returncode, "rejected_by_assertion": caught,
                            "stdout": result.stdout, "stderr": result.stderr})
    report = {"task": "T-093", "status": "PASS" if valid else "INCOMPLETE",
              "scope": "合成凭据辅助逻辑与单点变异；不证明真实 CLI、钥匙串、OS 沙箱或产品通路",
              "real_cli_starts": 0, "real_credential_reads": 0, "records": records}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "cases": len(records),
                      "real_cli_starts": 0, "real_credential_reads": 0}))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
