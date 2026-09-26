#!/usr/bin/env python3
"""Entry point of the skill CLI. Normally started through scripts/wit, which prepares the environment."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from witlib.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
