#!/usr/bin/env python3
"""Exercise the build entry with an absent volume and an internal directory."""
import argparse
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--entry", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
fixture = args.output / "fixture"
(fixture / "src").mkdir(parents=True)
(fixture / "Cargo.toml").write_text(
    '[package]\nname = "t026_mount_contract"\nversion = "0.1.0"\nedition = "2021"\n',
    encoding="utf-8",
)
(fixture / "src/main.rs").write_text('fn main() { println!("mount contract"); }\n', encoding="utf-8")
pretend_volume = args.output / "ordinary-directory"
pretend_volume.mkdir()
records = []
for name, volume in [("absent", args.output / "absent-volume"), ("ordinary-directory", pretend_volume)]:
    env = os.environ.copy()
    env.update({
        "MUSTER_BUILD_VOLUME": str(volume.resolve()),
        "CARGO_HOME": str(args.output / name / "cargo-home"),
        "CARGO_TARGET_DIR": str(args.output / name / "target"),
        "RUSTUP_TOOLCHAIN": "1.96.1",
    })
    command = [args.entry, "build", "--offline", "--manifest-path", str(fixture / "Cargo.toml")]
    result = subprocess.run(command, env=env, text=True, capture_output=True)
    (args.output / (name + ".stdout")).write_text(result.stdout, encoding="utf-8")
    (args.output / (name + ".stderr")).write_text(result.stderr, encoding="utf-8")
    targets = [str(p) for p in args.output.rglob("target") if p.is_dir()]
    records.append({"case": name, "argv": command, "env": {k: env[k] for k in ["MUSTER_BUILD_VOLUME", "CARGO_HOME", "CARGO_TARGET_DIR", "RUSTUP_TOOLCHAIN"]},
                    "exit": result.returncode, "targets": targets,
                    "pass": result.returncode != 0 and not targets})
report = {"verdict": "PASS" if all(r["pass"] for r in records) else "NO_GO", "cases": records}
(args.output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["verdict"] == "PASS" else 1)
