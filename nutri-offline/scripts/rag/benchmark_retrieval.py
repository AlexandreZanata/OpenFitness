#!/usr/bin/env python3
"""G-RET retrieval benchmark — Phase 11 (N-11-11)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(RAG_DIR))

from _paths import LOG_DIR
from index_catalog import index_snapshot, load_index_metadata
from rag_pipeline import RagPipeline

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
DEFAULT_GATE = FIXTURES / "retrieval_gate_sample.jsonl"
DEFAULT_FULL = FIXTURES / "retrieval_corpus_full.jsonl"

MIN_HIT_SCORE = 0.08

BUCKET_TARGETS = {
    "taco": {"recall_at": 1, "min_pct": 98.0},
    "off": {"recall_at": 5, "min_pct": 90.0},
    "fdc_branded": {"recall_at": 5, "min_pct": 85.0},
    "generic_pt": {"recall_at": 1, "min_pct": 99.0, "source_top1": True},
    "negative": {"max_false_positive_pct": 5.0},
}


@dataclass
class QueryResult:
    query_id: str
    bucket: str
    query: str
    passed: bool
    detail: str
    top_ids: list[str]
    top_sources: list[str]
    latency_ms: float


def load_queries(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def evaluate_query(rag: RagPipeline, row: dict, *, top_k: int = 5) -> QueryResult:
    started = time.perf_counter()
    bucket = row["bucket"]
    query = row["query"]

    if bucket == "negative":
        hits = rag.search_for_lookup(query, top_k=top_k)
        elapsed = (time.perf_counter() - started) * 1000
        false_positive = bool(hits) and hits[0].score >= MIN_HIT_SCORE
        return QueryResult(
            query_id=row["id"],
            bucket=bucket,
            query=query,
            passed=not false_positive,
            detail="no hit" if not hits else f"top_score={hits[0].score:.3f}",
            top_ids=[h.id for h in hits[:top_k]],
            top_sources=[h.source for h in hits[:top_k]],
            latency_ms=round(elapsed, 2),
        )

    hits = rag.search_for_lookup(
        query,
        top_k=top_k,
        prefer_branded=bucket in {"off", "fdc_branded"},
    )
    elapsed = (time.perf_counter() - started) * 1000
    top_ids = [h.id for h in hits[:top_k]]
    top_sources = [h.source for h in hits[:top_k]]

    expected_id = row.get("expected_id")
    expect_source = row.get("expect_top1_source") or row.get("expected_source")

    if expected_id:
        target_k = BUCKET_TARGETS.get(bucket, {}).get("recall_at", 5)
        slice_ids = top_ids[:target_k]
        passed = expected_id in slice_ids
        detail = f"expected {expected_id} in top-{target_k}"
    elif expect_source:
        passed = bool(top_sources) and top_sources[0] == expect_source
        detail = f"expected top-1 source={expect_source}, got={top_sources[:1]}"
    else:
        passed = bool(hits)
        detail = "any hit"

    return QueryResult(
        query_id=row["id"],
        bucket=bucket,
        query=query,
        passed=passed,
        detail=detail,
        top_ids=top_ids,
        top_sources=top_sources,
        latency_ms=elapsed,
    )


def bucket_metrics(results: list[QueryResult]) -> dict[str, dict]:
    grouped: dict[str, list[QueryResult]] = defaultdict(list)
    for result in results:
        grouped[result.bucket].append(result)

    metrics: dict[str, dict] = {}
    for bucket, rows in grouped.items():
        passed = sum(1 for row in rows if row.passed)
        total = len(rows)
        pct = round(passed / total * 100.0, 2) if total else 100.0
        target = BUCKET_TARGETS.get(bucket, {})
        if bucket == "negative":
            false_pct = round((total - passed) / total * 100.0, 2) if total else 0.0
            ok = false_pct <= float(target.get("max_false_positive_pct", 5.0))
            metrics[bucket] = {
                "total": total,
                "false_positive_pct": false_pct,
                "target_max_pct": target.get("max_false_positive_pct", 5.0),
                "pass": ok,
            }
        else:
            min_pct = float(target.get("min_pct", 80.0))
            metrics[bucket] = {
                "total": total,
                "passed": passed,
                "recall_pct": pct,
                "target_min_pct": min_pct,
                "pass": pct >= min_pct,
            }
    return metrics


def gate_pass(metrics: dict[str, dict], *, index_scope: str) -> bool:
    required = ["taco", "off", "generic_pt", "negative"]
    if index_scope == "all":
        required.append("fdc_branded")
    for bucket in required:
        if bucket not in metrics:
            return False
        if not metrics[bucket].get("pass", False):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieval benchmark G-RET")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--full", action="store_true", help="Use full corpus fixture")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--gate", action="store_true", help="Exit non-zero if targets missed")
    args = parser.parse_args()

    fixture = DEFAULT_FULL if args.full else args.fixture
    if not fixture.is_file():
        print(f"ERROR: fixture missing {fixture} — run generate_retrieval_corpus.py", file=sys.stderr)
        return 1

    meta = load_index_metadata()
    scope = str(meta.get("scope", "v1"))
    queries = load_queries(fixture)
    rag = RagPipeline.get()

    results = [evaluate_query(rag, row, top_k=args.top_k) for row in queries]
    metrics = bucket_metrics(results)
    latencies = [r.latency_ms for r in results]
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    passed = gate_pass(metrics, index_scope=scope)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "timestamp": timestamp,
        "fixture": str(fixture),
        "query_count": len(queries),
        "index_scope": scope,
        "index_records": (index_snapshot().record_count if index_snapshot() else 0),
        "latency_ms_p50": round(p50, 2),
        "latency_ms_p95": round(p95, 2),
        "bucket_metrics": metrics,
        "pass": passed,
        "failures": [asdict(r) for r in results if not r.passed][:50],
    }

    out = args.report or LOG_DIR / f"retrieval-benchmark-{timestamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for bucket, data in sorted(metrics.items()):
            if bucket == "negative":
                print(f"{bucket}: false_positive={data['false_positive_pct']}% (max {data['target_max_pct']}%)")
            else:
                print(f"{bucket}: recall={data['recall_pct']}% (target ≥{data['target_min_pct']}%)")
        print(f"p50={p50:.1f}ms p95={p95:.1f}ms scope={scope}")
        print(f"Report: {out}")
        print(f"{'PASS' if passed else 'FAIL'}: G-RET retrieval benchmark")

    if args.gate and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
