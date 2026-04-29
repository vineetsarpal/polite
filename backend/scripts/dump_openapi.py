"""
Emit the OpenAPI schema as JSON to stdout.

Used by .github/workflows/pr-checks.yml's openapi-drift job. Does NOT
boot uvicorn — just imports `app` and calls `app.openapi()`.

SQLAlchemy engines are created at import time but connections are lazy,
so this runs without a live database as long as DATABASE_URL is *parseable*.
The CI job sets dummy values that satisfy URL parsing without connecting.
"""

from __future__ import annotations

import json
import os
import sys

# Project root on path so `from src...` resolves when run as `uv run python scripts/dump_openapi.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app  # noqa: E402


def main() -> None:
    print(json.dumps(app.openapi(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
