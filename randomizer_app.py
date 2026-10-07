"""Convenience launcher: python randomizer/randomizer_app.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dqmj3p_randomizer.global_app import main


if __name__ == "__main__":
    main()
