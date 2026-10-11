#!/usr/bin/env python3
"""Transfer the unchanged CLI arguments to the native gate entry."""
import os
from pathlib import Path
import sys

cli = Path(__file__).resolve().parents[2] / "workbench/src/gates/cli.ts"
os.execvp("node", ["node", str(cli), *sys.argv[1:]])
