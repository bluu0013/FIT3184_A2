"""Import this first in each test module so the shared layer and inference app are importable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "aws" / "layers" / "common", ROOT / "services" / "gcp" / "inference"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
