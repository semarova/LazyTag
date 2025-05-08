# conftest.py — shared pytest config

import sys
from pathlib import Path

# Ensure the project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))