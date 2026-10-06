#!/usr/bin/env python3
"""Check actual build-script environment and reject unsafe output paths."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--entry", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output = args.output.resolve()
args.output.mkdir(parents=True, exist_ok=False)
fixture = args.output / "fixture"
(fixture / "src").mkdir(parents=True)
(fixture / "Cargo.toml").write_text('[package]\nname="t026_path_contract"\nversion="0.1.0"\nedition="2021"\n', encoding="utf-8")
keys = ["CARGO_HOME", "CARGO_TARGET_DIR", "CARGO_BUILD_TARGET_DIR", "CARGO_BUILD_BUILD_DIR", "ZIG_GLOBAL_CACHE_DIR", "ZIG_LOCAL_CACHE_DIR", "TMPDIR", "npm_config_cache", "ZIG"]
(fixture / "build.rs").write_text('fn main() { let keys = ' + json.dumps(keys) + '; let text: String = keys.iter().map(|k| format!("{}={}\\n", k, std::env::var(k).unwrap())).collect(); std::fs::write(std::path::Path::new(&std::env::var("OUT_DIR").unwrap()).join("observed-env.txt"), text).unwrap(); }\n', encoding="utf-8")
(fixture / "src/main.rs").write_text('fn main() { println!("{}", std::env::args().skip(1).collect::<Vec<_>>().join("|")); }\n', encoding="utf-8")
slot = "t026-paths-" + uuid.uuid4().hex[:8]
volume = Path("/Volumes/WD-Elements")
target = volume / "dev-cache/a2a/target" / slot
env = os.environ.copy()
env.update({k: str(args.output / "poisoned-internal-cache") for k in keys})
env["MUSTER_BUILD_SLOT"] = slot
nonce = uuid.uuid4().hex
records = []


def run(label, cargo_args, selected_env):
    argv = [args.entry, *cargo_args]
    result = subprocess.run(argv, env=selected_env, text=True, capture_output=True)
    (args.output / (label + ".stdout")).write_text(result.stdout, encoding="utf-8")
    (args.output / (label + ".stderr")).write_text(result.stderr, encoding="utf-8")
    record = {"case": label, "argv": argv, "env": {k: selected_env.get(k) for k in [*keys, "MUSTER_BUILD_SLOT"]}, "exit": result.returncode}
    records.append(record)
    return result, record


result, record = run("mounted", ["run", "--offline", "--manifest-path", str(fixture / "Cargo.toml"), "--", nonce, "--config", "second-argument"], env)
observed_files = list(target.rglob("observed-env.txt")) if target.exists() else []
observed = dict(line.split("=", 1) for line in observed_files[0].read_text(encoding="utf-8").splitlines()) if len(observed_files) == 1 else {}
record["observed_env"] = observed
record["pass"] = result.returncode == 0 and result.stdout.strip() == nonce + "|--config|second-argument" and len(observed) == len(keys) and all(Path(v).resolve().is_relative_to(volume) for v in observed.values()) and not (args.output / "poisoned-internal-cache").exists() and not (fixture / "target").exists()
for label, value in [("invalid-slot", "../escape"), ("symlink-slot", slot + "-symlink")]:
    selected = env.copy()
    selected["MUSTER_BUILD_SLOT"] = value
    if label == "symlink-slot":
        internal = args.output / "symlink-destination"
        internal.mkdir()
        (target.parent / value).symlink_to(internal, target_is_directory=True)
    result, record = run(label, ["build", "--offline", "--manifest-path", str(fixture / "Cargo.toml")], selected)
    record["pass"] = result.returncode != 0 and not (args.output / "poisoned-internal-cache").exists() and not (fixture / "target").exists() and (label != "symlink-slot" or not list(internal.iterdir()))
result, record = run("target-override", ["build", "--offline", "--manifest-path", str(fixture / "Cargo.toml"), "--target-dir", str(args.output / "forbidden-target")], env)
record["pass"] = result.returncode != 0 and not (args.output / "forbidden-target").exists()
report = {"verdict": "PASS" if all(r["pass"] for r in records) else "NO_GO", "cases": records}
(args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["verdict"] == "PASS" else 1)
