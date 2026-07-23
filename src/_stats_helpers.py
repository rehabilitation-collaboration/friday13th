"""Shared statistics helpers for the friday13th pipeline.

Phase 2C-C4 D1+D4 fix (pre-flagged in 2C-C3 P3-e as the 3-copy DRY trigger,
escalated by 07 to a 3-form drift on Z_CRIT_95 alone). This module
centralizes:

  - Z_CRIT_95: the 97.5th percentile of the standard normal (95% two-sided
    critical value). Previously `1.96` in 03, `Z_CRIT_95 = 1.96` in 04/05,
    and `Z95 = 1.959963984540054` in 07 — 3 forms diverging in the 5th-6th
    decimal, immaterial numerically but a manuscript-facing consistency risk.
    Standardized to the scipy-exact value 1.959963984540054 so all four
    scripts feeding the manuscript produce byte-identical CI bounds.
  - _safe_float / _safe_exp: null-safe conversions that return None on
    NaN/inf/non-numeric input. Ensures `json.dumps(allow_nan=False)` cannot
    fail after long compute (2C-C1 P1-4 pattern).

Intentionally minimal — no dependencies beyond math + numpy/scipy standard.
"""
from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Statistical constants
# ---------------------------------------------------------------------------
# scipy.stats.norm.ppf(0.975) with full float64 precision; hardcoded to avoid
# a scipy import at load time in scripts that don't otherwise need it.
Z_CRIT_95: float = 1.959963984540054


# ---------------------------------------------------------------------------
# Null-safe conversions
# ---------------------------------------------------------------------------
def safe_float(x: Any) -> float | None:
    """Convert x to a Python float; return None if NaN/inf/non-numeric.

    Use this on every numeric field that will be dumped through
    `json.dumps(..., allow_nan=False)` — the allow_nan guard raises
    ValueError at serialization time on NaN, which is far too late in a
    long-running fit pipeline. Filter at construction, not at write.
    """
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def safe_exp(x: Any) -> float | None:
    """Return exp(x) as a Python float, or None on overflow / non-numeric.

    Prevents `math.exp(large_beta)` from raising OverflowError inside a
    result-building path — the caller should treat None as "not computable"
    (typically flagged in the surrounding result dict as non-convergence).
    """
    v = safe_float(x)
    if v is None:
        return None
    try:
        r = math.exp(v)
    except OverflowError:
        return None
    if not math.isfinite(r):
        return None
    return r
