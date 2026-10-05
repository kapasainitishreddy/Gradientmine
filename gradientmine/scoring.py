"""Predeclared, bounded candidate comparison. Statistical intervals are approximate, not proofs."""

from __future__ import annotations
import numpy as np
from .crypto import digest


def assess(labels, baseline, candidate, min_delta: float = 0.01, max_candidates: int = 8) -> dict:
    arrays = [np.asarray(value) for value in (labels, baseline, candidate)]
    y, before, after = arrays
    if (
        any(a.ndim != 1 or not np.issubdtype(a.dtype, np.number) or not np.isfinite(a).all() for a in arrays)
        or not len(y) >= 2
        or len(before) != len(y)
        or len(after) != len(y)
    ):
        raise ValueError("Expected paired finite predictions of equal length >= 2")
    if not 0 <= min_delta <= 1 or type(max_candidates) is not int or not 1 <= max_candidates <= 8:
        raise ValueError("Invalid eligibility parameters")
    correctness_before = before == y
    correctness_after = after == y
    paired = correctness_after.astype(int) - correctness_before.astype(int)
    n = len(y)
    probabilities = [float((paired == 1).mean()), float((paired == -1).mean()), float((paired == 0).mean())]
    # Equivalent to resampling paired {-1,0,1} outcomes, without a large index matrix.
    resamples = np.random.default_rng(7301).multinomial(n, probabilities, size=20000)
    deltas = (resamples[:, 0] - resamples[:, 1]) / n
    alpha = 0.05 / max_candidates
    lower = float(np.quantile(deltas, alpha, method="linear"))
    delta = float(paired.mean())
    eligible = bool(delta + 1e-12 >= min_delta and lower > 0)
    return {
        "baseline_accuracy": float(correctness_before.mean()),
        "candidate_accuracy": float(correctness_after.mean()),
        "delta": delta,
        "minimum_delta": min_delta,
        "bootstrap_lower_bound": lower,
        "per_candidate_alpha": alpha,
        "maximum_candidates": max_candidates,
        "n": n,
        "bootstrap_resamples": 20000,
        "bootstrap_seed": 7301,
        "eligible": eligible,
        "reason": (
            "Threshold and positive adjusted lower bound met"
            if eligible
            else "Required improvement or adjusted lower bound not met"
        ),
        "candidate_predictions_sha256": digest(after.astype(int).tolist()),
        "baseline_predictions_sha256": digest(before.astype(int).tolist()),
        "statistical_limit": "Approximate one-sided paired bootstrap under IID assumptions; no anti-leakage or work proof.",
    }


def select_winner(rows: list[dict]) -> dict | None:
    eligible = [row for row in rows if row.get("eligible") is True]
    if not eligible:
        return None
    return sorted(eligible, key=lambda row: (-row["candidate_accuracy"], row["artifact_sha256"]))[0]
