"""Evidence transport into the production CLI with a controlled thread service."""
import os
from pathlib import Path
import sys
# The acceptance runner snapshots this transport below the repository root.
root = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "acceptance/test_run_e2e.py").is_file())
os.environ["A2A_WORKBENCH"] = str(root / "workbench")
entry = Path(__file__).with_suffix('.ts')
os.execvp("node", ["node", str(entry), *sys.argv[1:]])
