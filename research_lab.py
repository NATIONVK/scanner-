"""Statistical tools for educational crash-multiplier research.

No function predicts future rounds or generates betting advice.
Only Python's standard library is used.
"""
from __future__ import annotations

import hashlib
import math
import random
import statistics
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


def pearson_correlation(left: List[float], right: List[float]):
    """Pearson correlation, implemented for Python 3.9 compatibility."""
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left, mean_right = statistics.mean(left), statistics.mean(right)
    centered_left = [x - mean_left for x in left]
    centered_right = [y - mean_right for y in right]
    sum_left = sum(x * x for x in centered_left)
    sum_right = sum(y * y for y in centered_right)
    if sum_left == 0 or sum_right == 0:
        return None
    return sum(x * y for x, y in zip(centered_left, centered_right)) / math.sqrt(sum_left * sum_right)


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
        threshold_results[label] = {
            "hits": hits,
            "trials": n,
            "empirical_rate": hits / n,
            "wilson_95_ci": wilson_interval(hits, n),
            "longest_consecutive_run": longest_run(outcomes),
        }

    lag1 = pearson_correlation(data[:-1], data[1:]) if n >= 3 else None

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
        value = factor / max(1e-12, 1.0 - u)
        values.append(max(1.0, round(value, 2)))
    return values


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_sha256_reveal(revealed_seed: str, committed_hash: str) -> bool:
    """Check SHA256(revealed_seed) only; not a platform's full protocol."""
    expected = committed_hash.strip().lower()
    if len(expected) != 64:
        return False
    try:
        int(expected, 16)
    except ValueError:
        return False
    return sha256_hex(revealed_seed) == expected
