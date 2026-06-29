"""SQLite + sqlite-vec connection helpers for mobile index."""

from __future__ import annotations

from pathlib import Path

try:
    import pysqlite3 as sqlite3
except ImportError:  # pragma: no cover
    import sqlite3  # type: ignore[no-redef]

import sqlite_vec


def connect(db_path: str, *, readonly: bool = False) -> sqlite3.Connection:
    if db_path == ":memory:":
        connection = sqlite3.connect(":memory:")
    else:
        path = Path(db_path).resolve()
        if not readonly:
            path.parent.mkdir(parents=True, exist_ok=True)
        if readonly:
            uri = f"file:{path}?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
        else:
            connection = sqlite3.connect(str(path))
    sqlite_vec.load(connection)
    connection.execute("PRAGMA journal_mode=WAL")
    return connection
