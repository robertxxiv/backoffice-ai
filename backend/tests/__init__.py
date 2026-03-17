from __future__ import annotations

import atexit
import os
import tempfile
from pathlib import Path

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_FILE.name}"


@atexit.register
def cleanup_test_db() -> None:
    Path(DB_FILE.name).unlink(missing_ok=True)
