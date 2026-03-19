from __future__ import annotations

import atexit
import os
import tempfile
from pathlib import Path

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_FILE.name}"
os.environ["AUTH_SECRET_KEY"] = "test-auth-secret"
os.environ["INITIAL_ADMIN_EMAIL"] = "admin@example.com"
os.environ["INITIAL_ADMIN_PASSWORD"] = "admin-password"


@atexit.register
def cleanup_test_db() -> None:
    Path(DB_FILE.name).unlink(missing_ok=True)


def auth_headers(client) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": os.environ["INITIAL_ADMIN_EMAIL"], "password": os.environ["INITIAL_ADMIN_PASSWORD"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
