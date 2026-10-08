"""Evidence transport into the production CLI with a controlled thread service."""
import os
from pathlib import Path
import sys
fork = Path('/Users/luckye/Documents/Code/synara')
entry = Path(__file__).with_suffix('.ts')
os.execv(str(fork / 'a2a/scripts/bun'), [str(fork / 'a2a/scripts/bun'), str(entry), *sys.argv[1:]])
