import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
ROOT = PIPELINE.parent
sys.path.insert(0, str(PIPELINE))
