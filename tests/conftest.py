import sys
from pathlib import Path

# Ensure the local `src/` directory is preferred on sys.path so tests import the
# workspace copy of the package rather than any globally installed one.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
