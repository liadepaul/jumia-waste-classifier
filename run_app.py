"""Small launcher kept for local development convenience."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
        check=True,
    )


if __name__ == "__main__":
    main()
