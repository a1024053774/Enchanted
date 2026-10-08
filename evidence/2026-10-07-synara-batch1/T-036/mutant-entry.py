"""Transfer unchanged arguments to the explicitly selected isolated mutant."""
import os
from pathlib import Path
import sys

fork = Path(__file__).resolve().parents[3].parent / "synara"
entry = fork / "a2a/scripts/bun"
os.execv(str(entry), [str(entry), os.environ["A2A_MUTANT_ENTRY"], *sys.argv[1:]])
