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
        ("auth_diagnostic_leaks_stdout", 'report[name + "_output"] = {"exit_code": code, "stdout": output_shape(stdout), "stderr": output_shape(stderr)}',
         'report[name + "_output"] = {"exit_code": code, "stdout": output_shape(stdout), "stderr": output_shape(stderr), "raw": stdout.decode("utf-8")}',
         "test_auth_status_keeps_only_safe_structure_and_stops_on_non_json"),
        ("auth_accepts_json_after_warning", 'data = json.loads(stdout)',
         'data = json.loads(stdout[stdout.find(b"{"):])',
         "test_auth_status_keeps_only_safe_structure_and_stops_on_non_json"),
        ("auth_ignores_exit_code", 'require(code == 0 and all(report[name][key] for key in',
         'require(all(report[name][key] for key in',
         "test_auth_status_keeps_only_safe_structure_and_stops_on_non_json"),
        ("profile_uses_rejected_numeric_host", '(remote tcp4 "localhost:{port}")',
         '(remote tcp4 "127.0.0.1:{port}")',
         "test_bound_profile_compiles_without_applying_it"),
        ("profile_failure_gate_is_skipped", 'code == 0 and report["precredential_bound_profile_probe"]["version_matches"]',
         'True', "test_bound_profile_failure_stops_before_credential_read"),
        ("terminal_queries_are_not_answered", 'replies.append(reply)', 'pass',
         "test_route_peer_needs_terminal_reply_and_records_external_prompt"),
        ("terminal_process_denials_always_empty", '"process_denial_operations": process_denials',
         '"process_denial_operations": []',
         "test_terminal_process_denials_and_host_failures_keep_only_categories"),
        ("official_host_mention_is_reported_as_failure", '"official_host_connectivity_failure": host_connection_failure',
         '"official_host_connectivity_failure": "api.anthropic.com" in normalized',
         "test_terminal_process_denials_and_host_failures_keep_only_categories"),
        ("official_host_failure_uses_nearby_unrelated_text", 'host_connection_failure = any(match[1].rstrip(".") == "api.anthropic.com"\n                                  for pattern in targets for match in re.finditer(pattern, normalized))',
         'host_connection_failure = bool(re.search(r"\\b(?:failed|unable) to connect.{0,160}\\bapi\\.anthropic\\.com\\b", normalized))',
         "test_terminal_process_denials_and_host_failures_keep_only_categories"),
        ("exited_child_still_receives_keys", 'if child.poll() is not None:\n                continue\n            screen +=',
         'if False:\n                continue\n            screen +=',
         "test_route_drains_output_from_a_child_that_already_exited"),
        ("terminal_raw_output_is_saved", '"terminal": terminal_facts(captured, PROMPT)',
         '"terminal": {**terminal_facts(captured, PROMPT), "raw": captured.decode("utf-8", "replace")}',
         "test_route_drains_output_from_a_child_that_already_exited"),
        ("submission_reader_follows_home_symlink", 'child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)',
         'child = os.open(part, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory)',
         "test_submission_reader_does_not_follow_an_ancestor_symlink"),
        ("home_references_always_empty", 'def home_references(value, home, field="launch"):\n',
         'def home_references(value, home, field="launch"):\n    return []\n',
         "test_home_references_include_policy_and_duplicate_executable_fields"),
        ("terminal_export_omits_encoded_credential_replacements", 'for value in sorted(secret_variants(secrets), key=len, reverse=True):',
         'for value in secrets:', "test_terminal_export_redacts_variants_identities_and_preserves_diagnostics"),
        ("terminal_export_loses_auth_identity_values", 'return account_values(data)', 'return set()',
         "test_terminal_export_redacts_variants_identities_and_preserves_diagnostics"),
        ("terminal_export_skips_prewrite_credential_scan", 'require(hits == 0, "terminal_export_credential_scan_failed")',
         'require(True, "terminal_export_credential_scan_failed")',
         "test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths"),
        ("terminal_export_mode_is_644", 'os.fchmod(stream.fileno(), 0o600)', 'os.fchmod(stream.fileno(), 0o644)',
         "test_terminal_export_redacts_variants_identities_and_preserves_diagnostics"),
        ("terminal_export_follows_parent_link", 'child = os.open(ancestor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)',
         'child = os.open(ancestor, os.O_RDONLY | os.O_DIRECTORY, dir_fd=directory)',
         "test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths"),
        ("terminal_export_accepts_other_destinations", 'require(terminal_output == TERMINAL_OUTPUT, "terminal_export_path_not_authorized")',
         'require(True, "terminal_export_path_not_authorized")',
         "test_terminal_export_wrong_destination_stops_before_private_setup"),
        ("terminal_export_url_case_is_not_normalized", 'return re.sub(r"%[0-9a-fA-F]{2}", lambda match: match[0].upper(), text)',
         'return text', "test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths"),
        ("terminal_export_ignores_box_prefixes", '[ \\t|+\\u2500-\\u257f]*(?:welcome', '[ \\t]*(?:welcome',
         "test_terminal_export_redacts_variants_identities_and_preserves_diagnostics"),
        ("terminal_export_scan_omits_unpadded_base64", 'encoded, encoded.rstrip("="), url_encoded, url_encoded.rstrip("=")',
         'encoded, url_encoded', "test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths"),
        ("terminal_export_accepts_incomplete_control_strings", '(?![\\[\\]PX^_])[ -/]*[0-~]', '[ -/]*[@-Z\\\\-_]',
         "test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths"),
        ("onboarding_state_has_wrong_value", 'stream.write(encode({"hasCompletedOnboarding": True}))',
         'stream.write(encode({"hasCompletedOnboarding": False}))',
         "test_onboarding_state_is_one_new_field_in_private_config"),
        ("onboarding_state_uses_home_instead_of_config_dir", 'relative = Path("home/.claude/.claude.json")',
         'relative = Path("home/.claude.json")', "test_onboarding_state_is_one_new_field_in_private_config"),
        ("onboarding_state_option_is_ignored", 'if args.prepare_onboarding_state:', 'if False:',
         "test_onboarding_state_precedes_cli_and_auth_only_when_requested"),
        ("terminal09_still_uses_old_authorization", 't093-terminal-09.txt', 't093-terminal-07.txt',
         "test_terminal09_is_the_only_approved_export_destination"),
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
