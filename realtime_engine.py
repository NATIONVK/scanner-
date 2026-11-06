"""Real-time descriptive and diagnostic research for observed crash multipliers.

This module deliberately does not forecast an individual next-round outcome.
All outputs are historical diagnostics or clearly labelled empirical baselines.
Uses only the Python standard library.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Any, Iterable

from research_lab import clean_multipliers, pearson_correlation, wilson_interval


def runs_test(values: Iterable[Any], threshold: float = 2.0) -> dict:
    """Wald-Wolfowitz runs test around a fixed threshold (normal approximation)."""
    data = clean_multipliers(values)
    flags = [x >= threshold for x in data]
    n1, n2 = sum(flags), len(flags) - sum(flags)
    runs = 1 + sum(flags[i] != flags[i - 1] for i in range(1, len(flags))) if flags else 0
    if n1 == 0 or n2 == 0 or len(flags) < 10:
        return {"available": False, "reason": "Need at least 10 observations and both sides of the threshold.", "runs": runs}
    n = n1 + n2
    expected = 1 + (2 * n1 * n2 / n)
    variance = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n * n * (n - 1))
    if variance <= 0:
        return {"available": False, "reason": "Insufficient variation.", "runs": runs}
    z = (runs - expected) / math.sqrt(variance)
    return {"available": True, "threshold": threshold, "runs": runs, "expected_runs": expected,
            "z_score": z, "interpretation": "Possible non-random ordering signal; not proof and not a forecast."}


def autocorrelation(values: Iterable[Any], max_lag: int = 5) -> dict:
    data = clean_multipliers(values)
    result = {}
    for lag in range(1, max(1, min(max_lag, len(data) - 2)) + 1):
        corr = pearson_correlation(data[:-lag], data[lag:])
        result[str(lag)] = corr
    return {"sample_size": len(data), "lags": result,
            "note": "Exploratory sample correlations; unstable for small samples."}


def rolling_summary(values: Iterable[Any], window: int = 50) -> dict:
    data = clean_multipliers(values)
    if window < 2:
        raise ValueError("window must be at least 2")
    recent = data[-window:]
    if not recent:
        return {"window": window, "count": 0, "mean": None, "median": None, "sd": None}
    return {"window": window, "count": len(recent), "mean": statistics.mean(recent),
            "median": statistics.median(recent),
            "sd": statistics.stdev(recent) if len(recent) > 1 else 0.0,
            "last_value": recent[-1]}


def empirical_baseline(values: Iterable[Any], minimum_sample: int = 100) -> dict:
    """Historical quantile reference band; explicitly not a next-round prediction."""
    data = sorted(clean_multipliers(values))
    if len(data) < minimum_sample:
        return {"available": False, "sample_size": len(data),
                "message": f"Need at least {minimum_sample} valid observations for a reference band."}
    def quantile(p: float) -> float:
        position = (len(data) - 1) * p
        lo, hi = math.floor(position), math.ceil(position)
        return data[lo] if lo == hi else data[lo] + (data[hi] - data[lo]) * (position - lo)
    return {"available": True, "sample_size": len(data),
            "historical_10th_percentile": quantile(.10),
            "historical_median": quantile(.50),
            "historical_90th_percentile": quantile(.90),
            "label": "Historical reference only — not a forecast or confidence interval for the next round."}


def analyze_live(values: Iterable[Any], window: int = 50) -> dict:
    data = clean_multipliers(values)
    if not data:
        return {"sample_size": 0, "status": "waiting_for_valid_data"}
    recent = rolling_summary(data, window)
    thresholds = {}
    for t in (1.5, 2.0, 5.0, 10.0):
        hits = sum(x >= t for x in data)
        thresholds[str(t)] = {"hits": hits, "rate": hits / len(data),
                              "wilson_95_ci": wilson_interval(hits, len(data))}
    return {"sample_size": len(data), "rolling": recent, "thresholds": thresholds,
            "runs_test": runs_test(data), "autocorrelation": autocorrelation(data),
            "historical_baseline": empirical_baseline(data),
            "warning": "No individual next-round outcome can be reliably inferred from these historical observations."}


class RoundStore:
    """SQLite history store. Duplicate event IDs are ignored for OCR frame deduplication."""
    def __init__(self, path: str | Path = "aviator_history.sqlite3"):
        self.path = str(path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                captured_at REAL NOT NULL,
                multiplier REAL NOT NULL CHECK(multiplier >= 1.0),
                source TEXT NOT NULL DEFAULT 'screen_ocr',
                confidence REAL
            )""")

    def _connect(self):
        return sqlite3.connect(self.path)

    def add(self, multiplier: Any, event_id: str | None = None,
            captured_at: float | None = None, source: str = "screen_ocr",
            confidence: float | None = None) -> bool:
        data = clean_multipliers([multiplier])
        if not data:
            raise ValueError("Multiplier must be finite and >= 1.0")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        try:
            with self._connect() as db:
                db.execute("INSERT INTO rounds(event_id,captured_at,multiplier,source,confidence) VALUES(?,?,?,?,?)",
                           (event_id, captured_at or time.time(), data[0], source, confidence))
            return True
        except sqlite3.IntegrityError:
            return False

    def values(self, limit: int = 5000) -> list[float]:
        with self._connect() as db:
            rows = db.execute("SELECT multiplier FROM rounds ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [row[0] for row in reversed(rows)]

    def export_rows(self) -> list[dict]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM rounds ORDER BY id").fetchall()
        return [dict(row) for row in rows]
