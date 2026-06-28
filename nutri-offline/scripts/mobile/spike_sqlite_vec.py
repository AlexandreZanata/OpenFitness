#!/usr/bin/env python3
"""sqlite-vec feasibility spike for mobile index (N-08-04)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

try:
    import pysqlite3 as sqlite3
except ImportError:  # pragma: no cover - fallback for environments without pysqlite3
    import sqlite3  # type: ignore[no-redef]

import sqlite_vec

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import LOG_DIR, MOBILE_EMBED_DIM, SPIKE_REPORT  # noqa: E402


def _connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    sqlite_vec.load(connection)
    return connection


def run_spike(
    *,
    num_vectors: int = 10_000,
    dims: int = MOBILE_EMBED_DIM,
    db_path: Path | None = None,
) -> dict:
    """Build a single-file vector DB and measure size + search latency."""
    owns_file = db_path is None
    if db_path is None:
        db_path = Path(tempfile.mktemp(suffix=".db"))

    connection = _connect(str(db_path))
    connection.execute(
        f"CREATE VIRTUAL TABLE foods USING vec0(embedding float32[{dims}])"
    )

    insert_start = time.perf_counter()
    rng = np.random.default_rng(42)
    for index in range(num_vectors):
        vector = rng.standard_normal(dims).astype(np.float32)
        connection.execute(
            "INSERT INTO foods(rowid, embedding) VALUES (?, ?)",
            (index + 1, vector),
        )
    connection.commit()
    insert_seconds = time.perf_counter() - insert_start

    query = rng.standard_normal(dims).astype(np.float32)
    search_start = time.perf_counter()
    top_k = connection.execute(
        """
        SELECT rowid, distance
        FROM foods
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT 5
        """,
        (query,),
    ).fetchall()
    search_ms = (time.perf_counter() - search_start) * 1000

    connection.close()
    vec0_size_bytes = db_path.stat().st_size

    # int8 blob estimate (target storage format for mobile budget)
    int8_path = Path(tempfile.mktemp(suffix=".db"))
    int8_conn = sqlite3.connect(str(int8_path))
    int8_conn.execute("CREATE TABLE v (id INTEGER PRIMARY KEY, emb BLOB)")
    for index in range(num_vectors):
        vector = rng.integers(-128, 127, size=dims, dtype=np.int8)
        int8_conn.execute(
            "INSERT INTO v(id, emb) VALUES (?, ?)",
            (index + 1, vector.tobytes()),
        )
    int8_conn.commit()
    int8_conn.close()
    int8_size_bytes = int8_path.stat().st_size

    if owns_file:
        db_path.unlink(missing_ok=True)
    int8_path.unlink(missing_ok=True)

    vec_version = None
    try:
        probe = _connect(":memory:")
        vec_version = probe.execute("SELECT vec_version()").fetchone()[0]
        probe.close()
    except sqlite3.Error:
        vec_version = "unknown"

    report = {
        "num_vectors": num_vectors,
        "dims": dims,
        "sqlite_backend": "pysqlite3" if "pysqlite3" in sys.modules else "sqlite3",
        "vec_version": vec_version,
        "vec0_float32_size_bytes": vec0_size_bytes,
        "vec0_float32_size_mb": round(vec0_size_bytes / (1024 * 1024), 2),
        "int8_blob_size_bytes": int8_size_bytes,
        "int8_blob_size_mb": round(int8_size_bytes / (1024 * 1024), 2),
        "insert_seconds": round(insert_seconds, 3),
        "search_ms": round(search_ms, 3),
        "top_k_sample": [{"rowid": row[0], "distance": row[1]} for row in top_k[:3]],
        "budget_vector_index_mb": 90,
        "feasible_under_budget": vec0_size_bytes <= 90 * 1024 * 1024,
        "android_jni_notes": (
            "Read-only sqlite-vec via bundled libsqlite_vec.so; "
            "pysqlite3 required on Python 3.12 for extension loading"
        ),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="sqlite-vec mobile index spike")
    parser.add_argument("--vectors", type=int, default=10_000)
    parser.add_argument("--dims", type=int, default=MOBILE_EMBED_DIM)
    parser.add_argument(
        "--output",
        type=Path,
        default=SPIKE_REPORT,
        help="JSON report path",
    )
    args = parser.parse_args()

    report = run_spike(num_vectors=args.vectors, dims=args.dims)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
