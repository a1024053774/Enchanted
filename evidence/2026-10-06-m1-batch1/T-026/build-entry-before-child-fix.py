#!/usr/bin/env python3
"""Run Cargo with the repository's external-volume build environment."""
import os
from pathlib import Path
import re
import subprocess
import sys


def fail(message):
    print(f"muster build: {message}", file=sys.stderr)
    raise SystemExit(2)


volume = Path(os.environ.get("MUSTER_BUILD_VOLUME", "/Volumes/WD-Elements")).resolve()
if not volume.is_mount():
    fail(f"external volume is not mounted: {volume}")
if volume.stat().st_dev == Path(__file__).resolve().stat().st_dev:
    fail(f"build volume is on the repository's internal filesystem: {volume}")

slot = os.environ.get("MUSTER_BUILD_SLOT", "default")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", slot):
    fail("MUSTER_BUILD_SLOT must be a single directory name beginning with a letter or digit")

args = sys.argv[1:] or ["build"]
for arg in args:
    if arg in ("--target-dir", "--artifact-dir", "--config") or arg.startswith(
        ("--target-dir=", "--artifact-dir=", "--config=")
    ):
        fail(f"{arg} overrides the managed build paths; use MUSTER_BUILD_SLOT instead")

cache = volume / "dev-cache/a2a"
paths = {
    "CARGO_HOME": cache / "cargo-home",
    "CARGO_TARGET_DIR": cache / "target" / slot,
    "CARGO_BUILD_TARGET_DIR": cache / "target" / slot,
    "CARGO_BUILD_BUILD_DIR": cache / "target" / slot,
    "ZIG_GLOBAL_CACHE_DIR": cache / "zig-cache/global",
    "ZIG_LOCAL_CACHE_DIR": cache / "zig-cache/local" / slot,
    "TMPDIR": cache / "tmp" / slot,
    "npm_config_cache": cache / "npm-cache",
}
zig = cache / "toolchains/zig-aarch64-macos-0.16.0/zig"
for path in [*paths.values(), zig]:
    if not path.resolve().is_relative_to(volume):
        fail(f"build path escapes the external volume: {path}")
if not zig.is_file():
    fail(f"Zig 0.16.0 is required at {zig}; see README.md for installation")

env = os.environ.copy()
env.update({name: str(path) for name, path in paths.items()})
env.update({"ZIG": str(zig), "RUSTUP_TOOLCHAIN": "1.96.1"})
version = subprocess.run([str(zig), "version"], env=env, text=True, capture_output=True, check=True)
if version.stdout.strip() != "0.16.0":
    fail(f"expected Zig 0.16.0, got {version.stdout.strip()}")
for path in set(paths.values()):
    path.mkdir(parents=True, exist_ok=True)

print(f"muster build: CARGO_TARGET_DIR={env['CARGO_TARGET_DIR']}", file=sys.stderr, flush=True)
os.execvpe("cargo", ["cargo", *args], env)
