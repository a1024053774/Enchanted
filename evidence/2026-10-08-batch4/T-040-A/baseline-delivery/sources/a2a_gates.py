#!/usr/bin/env python3
"""Transfer the unchanged CLI arguments to the native gate entry."""
import os
from pathlib import Path
import sys

fork = Path(__file__).resolve().parents[3] / "synara"
entry = fork / "a2a/scripts/bun"
cli = fork / "packages/a2a-gates/src/cli.ts"
os.execv(str(entry), [str(entry), str(cli), *sys.argv[1:]])
