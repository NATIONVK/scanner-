"""Statistical tools for educational crash-multiplier research.

No function predicts future rounds or generates betting advice.
Only Python's standard library is used.
"""
from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections import Counter
from typing import Iterable, Dict, List, Any


def clean_multipliers(values: Iterable[Any]) -> List[float]:
    cleaned = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and number >= 1.0:
            cleaned.append(number)
    return cleaned


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054):
    """95% Wilson score interval by default."""
    if trials <= 0:
        return None
    p = successes / trials
    denom = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials) / denom
    return [max(0.0, center - margin), min(1.0, center + margin)]


def longest_run(flags: List[bool]) -> int:
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def analyze(values: Iterable[Any], thresholds=(1.5, 2, 5, 10)) -> Dict[str, Any]:
    data = clean_multipliers(values)
    if not data:
        raise ValueError("No valid multiplier values found (values must be finite and >= 1.0).")

    n = len(data)
    sorted_data = sorted(data)
    mean = statistics.mean(data)
    median = statistics.median(data)
    variance = statistics.variance(data) if n > 1 else 0.0
    flags = {str(float(t)): [x >= t for x in data] for t in thresholds}

    threshold_results = {}
    for label, outcomes in flags.items():
        hits = sum(outcomes)
        interval = wilson_interval(hits, n)
        threshold_results[label] = {
            "hits": hits,
            "trials": n,
            "empirical_rate": hits / n,
            "wilson_95_ci": interval,
            "longest_consecutive_run": longest_run(outcomes),
        }

    # Exploratory lag-1 Pearson correlation. Undefined for constant series.
    lag1 = None
    if n >= 3:
        left, right = data[:-1], data[1:]
        if statistics.pvariance(left) > 0 and statistics.pvariance(right) > 0:
            lag1 = statistics.correlation(left, right)

    return {
        "sample_size": n,
        "mean": mean,
        "median": median,
        "minimum": min(data),
        "maximum": max(data),
        "population_sd": math.sqrt(statistics.pvariance(data)),
        "sample_sd": math.sqrt(variance),
        "quantiles": {
            "q25": statistics.quantiles(sorted_data, n=4, method="inclusive")[0] if n >= 2 else sorted_data[0],
            "q50": median,
            "q75": statistics.quantiles(sorted_data, n=4, method="inclusive")[2] if n >= 2 else sorted_data[0],
            "q90": statistics.quantiles(sorted_data, n=10, method="inclusive")[8] if n >= 2 else sorted_data[0],
        },
        "thresholds": threshold_results,
        "lag1_correlation_exploratory": lag1,
        "warning": "Historical statistics do not predict or guarantee the next round.",
    }


def generate_synthetic(rounds: int = 1000, seed: int = 42, house_edge: float = 0.03):
    """Illustrative inverse-tail model; NOT the verified algorithm of any platform."""
    if rounds < 1 or rounds > 1_000_000:
        raise ValueError("rounds must be between 1 and 1,000,000")
    if not 0 <= house_edge < 1:
        raise ValueError("house_edge must be in [0, 1)")
    rng = random.Random(seed)
    factor = 1.0 - house_edge
    values = []
    for _ in range(rounds):
        u = rng.random()
        # Illustrative continuous tail model with a minimum multiplier of 1.
        value = factor / max(1e-12, 1.0 - u)
        values.append(max(1.0, round(value, 2)))
    return values


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_sha256_reveal(revealed_seed: str, committed_hash: str) -> bool:
    """Check whether SHA256(revealed_seed) matches a supplied commitment."""
    expected = committed_hash.strip().lower()
    if len(expected) != 64:
        return False
    try:
        int(expected, 16)
    except ValueError:
        return False
    return sha256_hex(revealed_seed) == expected
