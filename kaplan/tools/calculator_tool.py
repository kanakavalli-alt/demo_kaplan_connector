# working
# from google.adk.tools import FunctionTool


# def calculate(operation: str, values: list[float], labels: list[str] = None) -> dict:
#     """
#     Perform financial calculations. ALWAYS use this — never compute inline.

#     Args:
#         operation: One of:
#           'sum'           → total of all values
#           'variance'      → actual − reference          [actual, reference]
#           'variance_pct'  → variance as %               [actual, reference]
#           'ratio'         → numerator / denominator     [numerator, denominator]
#           'yoy_change'    → current − prior year        [current, prior]
#           'yoy_pct'       → YoY % change                [current, prior]
#         values: Numeric inputs for the operation.
#         labels: Optional descriptive labels for each value (improves readability).

#     Returns:
#         dict with result, inputs, and a favorable flag where applicable.
#     """
#     if not values:
#         return {"error": "No values provided."}

#     labels = labels or [f"value_{i}" for i in range(len(values))]

#     if operation == "sum":
#         return {
#             "operation": "sum",
#             "result": sum(values),
#             "inputs": dict(zip(labels, values)),
#         }

#     if operation == "variance":
#         if len(values) != 2:
#             return {"error": "variance requires exactly [actual, reference]"}
#         result = values[0] - values[1]
#         return {
#             "operation":  "variance",
#             "result":     result,
#             "actual":     values[0],
#             "reference":  values[1],
#             "favorable":  result > 0,
#         }

#     if operation == "variance_pct":
#         if len(values) != 2:
#             return {"error": "variance_pct requires exactly [actual, reference]"}
#         if values[1] == 0:
#             return {"error": "Reference value cannot be zero."}
#         result = round(((values[0] - values[1]) / values[1]) * 100, 2)
#         return {
#             "operation":  "variance_pct",
#             "result":     result,
#             "actual":     values[0],
#             "reference":  values[1],
#             "favorable":  result > 0,
#         }

#     if operation == "ratio":
#         if len(values) != 2:
#             return {"error": "ratio requires exactly [numerator, denominator]"}
#         if values[1] == 0:
#             return {"error": "Denominator cannot be zero."}
#         return {
#             "operation":   "ratio",
#             "result":      round(values[0] / values[1], 4),
#             "numerator":   values[0],
#             "denominator": values[1],
#         }

#     if operation == "yoy_change":
#         if len(values) != 2:
#             return {"error": "yoy_change requires exactly [current, prior]"}
#         result = values[0] - values[1]
#         return {
#             "operation": "yoy_change",
#             "current":   values[0],
#             "prior":     values[1],
#             "change":    result,
#             "favorable": result > 0,
#         }

#     if operation == "yoy_pct":
#         if len(values) != 2:
#             return {"error": "yoy_pct requires exactly [current, prior]"}
#         if values[1] == 0:
#             return {"error": "Prior year value cannot be zero."}
#         result = round(((values[0] - values[1]) / values[1]) * 100, 2)
#         return {
#             "operation":  "yoy_pct",
#             "current":    values[0],
#             "prior":      values[1],
#             "change_pct": result,
#             "favorable":  result > 0,
#         }

#     return {
#         "error": (
#             f"Unknown operation '{operation}'. "
#             "Valid: sum, variance, variance_pct, ratio, yoy_change, yoy_pct"
#         )
#     }


# calculator_tool = FunctionTool(func=calculate)

# tools/calculator_tool.py
"""
Dynamic financial calculator for the Kaplan FP&A Analytics Agent.

DESIGN PHILOSOPHY — "operations are data, not code"
═══════════════════════════════════════════════════════════════════════════════
The calculator is a DISPATCHER.

  • Every operation is a self-contained handler function.
  • The dispatch table (_OPERATIONS) maps operation name → handler.
  • Adding a new operation = adding one function + one dict entry.
    No if/elif chains to maintain. No risk of breaking existing operations.

  • favorable_direction comes FROM the RAG tool result (which reads it from BQ).
    The calculator never decides what "favorable" means — BQ does.

  • Every result carries:
      human_summary → pre-formatted string agents can quote directly
      favorable      → True/False/None (None = neutral, no label)
      labels         → input labels preserved in output for traceability

FUTURE-PROOF GUARANTEES:
  • New operation       → add one handler function + one _OPERATIONS entry.
                          Zero changes to existing operations.
  • New favorable logic → change BQ favorable_direction column.
                          Zero code changes.
  • New input format    → add validation inside the handler only.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations
import logging
from typing import Any, Callable

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared utilities
# ─────────────────────────────────────────────────────────────────────────────

def _favorable(result: float, direction: str) -> bool | None:
    """
    Determine favorability.
    direction values (from BQ favorable_direction column):
      "higher"  → positive result = Favorable  (revenue, starts, census…)
      "lower"   → negative result = Favorable  (drop rate, cost, attrition…)
      "neutral" → None                          (mix %, ratios, CAGR…)
    """
    d = (direction or "higher").lower().strip()
    if d == "neutral":
        return None
    return (result > 0) if d == "higher" else (result < 0)


def _fmt(v: float) -> str:
    """Human-readable number formatting."""
    return f"{v:,.4f}" if abs(v) < 1_000 else f"{v:,.2f}"


def _lbl(labels: list[str], i: int, default: str) -> str:
    return labels[i] if i < len(labels) else default


def _err(msg: str) -> dict:
    return {"error": msg, "found": False}


# ─────────────────────────────────────────────────────────────────────────────
# Operation handlers
# Each handler signature: (values, labels, favorable_direction) → dict
# ─────────────────────────────────────────────────────────────────────────────

def _op_sum(values, labels, fd) -> dict:
    total = sum(values)
    fav   = _favorable(total, fd)
    return {
        "operation": "sum",
        "result":    total,
        "inputs":    dict(zip(labels, values)),
        "favorable": fav,
        "human_summary": (
            f"Total = {_fmt(total)}"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_variance(values, labels, fd) -> dict:
    if len(values) != 2:
        return _err("variance requires exactly [actual, reference]")
    result = values[0] - values[1]
    fav    = _favorable(result, fd)
    al, rl = _lbl(labels, 0, "actual"), _lbl(labels, 1, "reference")
    return {
        "operation":       "variance",
        "result":          result,
        "actual":          values[0], "actual_label":    al,
        "reference":       values[1], "reference_label": rl,
        "favorable":       fav,
        "human_summary": (
            f"{al} vs {rl}: {_fmt(values[0])} − {_fmt(values[1])} = {_fmt(result)}"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_variance_pct(values, labels, fd) -> dict:
    if len(values) != 2:
        return _err("variance_pct requires exactly [actual, reference]")
    if values[1] == 0:
        return _err("Reference value cannot be zero.")
    result = round(((values[0] - values[1]) / values[1]) * 100, 2)
    fav    = _favorable(result, fd)
    al, rl = _lbl(labels, 0, "actual"), _lbl(labels, 1, "reference")
    return {
        "operation":       "variance_pct",
        "result":          result,
        "actual":          values[0], "actual_label":    al,
        "reference":       values[1], "reference_label": rl,
        "favorable":       fav,
        "human_summary": (
            f"{al} vs {rl}: {result:+.2f}%"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_ratio(values, labels, fd) -> dict:
    if len(values) != 2:
        return _err("ratio requires exactly [numerator, denominator]")
    if values[1] == 0:
        return _err("Denominator cannot be zero.")
    result = round(values[0] / values[1], 4)
    nl, dl = _lbl(labels, 0, "numerator"), _lbl(labels, 1, "denominator")
    return {
        "operation":         "ratio",
        "result":            result,
        "numerator":         values[0], "numerator_label":   nl,
        "denominator":       values[1], "denominator_label": dl,
        "human_summary":     f"{nl} / {dl} = {_fmt(result)}",
    }


def _op_yoy_change(values, labels, fd) -> dict:
    if len(values) != 2:
        return _err("yoy_change requires exactly [current, prior]")
    change = values[0] - values[1]
    fav    = _favorable(change, fd)
    cl, pl = _lbl(labels, 0, "current"), _lbl(labels, 1, "prior")
    return {
        "operation":   "yoy_change",
        "current":     values[0], "current_label": cl,
        "prior":       values[1], "prior_label":   pl,
        "change":      change,
        "favorable":   fav,
        "human_summary": (
            f"YoY change ({cl} vs {pl}): {_fmt(change):+}"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_yoy_pct(values, labels, fd) -> dict:
    if len(values) != 2:
        return _err("yoy_pct requires exactly [current, prior]")
    if values[1] == 0:
        return _err("Prior year value cannot be zero.")
    pct  = round(((values[0] - values[1]) / values[1]) * 100, 2)
    fav  = _favorable(pct, fd)
    cl, pl = _lbl(labels, 0, "current"), _lbl(labels, 1, "prior")
    return {
        "operation":   "yoy_pct",
        "current":     values[0], "current_label": cl,
        "prior":       values[1], "prior_label":   pl,
        "change_pct":  pct,
        "favorable":   fav,
        "human_summary": (
            f"YoY% ({cl} vs {pl}): {pct:+.2f}%"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_mix_pct(values, labels, fd) -> dict:
    """Each value as % of total — for channel mix share."""
    if len(values) < 2:
        return _err("mix_pct requires at least 2 values.")
    total = sum(values)
    if total == 0:
        return _err("Total of all values is zero — cannot compute mix.")
    shares = {_lbl(labels, i, f"item_{i}"): round(v / total * 100, 2)
              for i, v in enumerate(values)}
    return {
        "operation":     "mix_pct",
        "total":         total,
        "shares":        shares,
        "human_summary": "Mix: " + ", ".join(f"{k}={v:.1f}%" for k, v in shares.items()),
    }


def _op_weighted_average(values, labels, fd) -> dict:
    """Weighted mean — [v1, w1, v2, w2, …] alternating pairs."""
    n = len(values)
    if n < 2 or n % 2 != 0:
        return _err(
            "weighted_average requires paired [value, weight] inputs. "
            "values=[v1, w1, v2, w2, …]. Total count must be even."
        )
    pairs        = [(values[i], values[i + 1]) for i in range(0, n, 2)]
    total_weight = sum(w for _, w in pairs)
    if total_weight == 0:
        return _err("Sum of weights is zero.")
    wavg         = round(sum(v * w for v, w in pairs) / total_weight, 4)
    pair_labels  = [_lbl(labels, i, f"item_{i//2}") for i in range(0, n, 2)]
    return {
        "operation":    "weighted_average",
        "result":       wavg,
        "total_weight": total_weight,
        "components":   {pair_labels[i]: {"value": pairs[i][0], "weight": pairs[i][1]}
                         for i in range(len(pairs))},
        "human_summary": f"Weighted average = {_fmt(wavg)}",
    }


def _op_growth_rate(values, labels, fd) -> dict:
    """
    Simple growth or CAGR.
      2 values: [start, end]           → simple growth %
      3 values: [start, end, n_periods] → CAGR
    """
    n = len(values)
    if n < 2:
        return _err("growth_rate requires [start, end] or [start, end, n_periods].")
    start, end = values[0], values[1]
    if start == 0:
        return _err("Start value cannot be zero.")
    sl, el = _lbl(labels, 0, "start"), _lbl(labels, 1, "end")
    if n >= 3:
        periods = values[2]
        if periods <= 0:
            return _err("n_periods must be > 0 for CAGR.")
        rate = round(((end / start) ** (1 / periods) - 1) * 100, 2)
        fav  = _favorable(rate, fd)
        return {
            "operation":  "growth_rate", "type": "CAGR",
            "start":      start, "end": end, "n_periods": periods,
            "result":     rate,  "favorable": fav,
            "human_summary": (
                f"CAGR over {int(periods)} periods: {rate:+.2f}%"
                + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
            ),
        }
    rate = round(((end - start) / abs(start)) * 100, 2)
    fav  = _favorable(rate, fd)
    return {
        "operation":  "growth_rate", "type": "simple",
        "start":      start, "end": end,
        "result":     rate,  "favorable": fav,
        "human_summary": (
            f"Growth ({sl} → {el}): {rate:+.2f}%"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_yoy_multi(values, labels, fd) -> dict:
    """
    YoY % for N period pairs — for trend queries spanning multiple quarters.
    values=[curr1, prior1, curr2, prior2, …]
    labels=[period1_label, period2_label, …]
    """
    n = len(values)
    if n < 2 or n % 2 != 0:
        return _err(
            "yoy_multi requires paired [current, prior] values. "
            "values=[curr1, prior1, curr2, prior2, …]"
        )
    results = []
    for i in range(n // 2):
        curr, prior = values[i * 2], values[i * 2 + 1]
        lbl = _lbl(labels, i, f"period_{i+1}")
        if prior == 0:
            results.append({"label": lbl, "current": curr, "prior": prior,
                            "yoy_pct": None, "favorable": None,
                            "summary": f"{lbl}: prior=0, cannot compute YoY%"})
            continue
        pct = round(((curr - prior) / prior) * 100, 2)
        fav = _favorable(pct, fd)
        results.append({
            "label":    lbl, "current": curr, "prior": prior,
            "yoy_pct":  pct, "favorable": fav,
            "summary":  (
                f"{lbl}: {_fmt(curr)} vs {_fmt(prior)} → {pct:+.2f}%"
                + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
            ),
        })
    return {
        "operation":     "yoy_multi",
        "results":       results,
        "human_summary": " | ".join(r["summary"] for r in results),
    }


def _op_delta_mix(values, labels, fd) -> dict:
    """
    Period-over-period mix shift per category (percentage-point).
    values=[curr_share1, prior_share1, curr_share2, prior_share2, …]
    labels=[category1, category2, …]
    """
    n = len(values)
    if n < 2 or n % 2 != 0:
        return _err(
            "delta_mix requires paired [current_share, prior_share] values (%). "
            "values=[curr1, prior1, curr2, prior2, …]"
        )
    results = []
    for i in range(n // 2):
        curr, prior = values[i * 2], values[i * 2 + 1]
        lbl   = _lbl(labels, i, f"category_{i+1}")
        shift = round(curr - prior, 2)
        results.append({
            "category":   lbl,
            "current_pct": curr, "prior_pct": prior,
            "shift_pp":   shift,
            "summary":    f"{lbl}: {prior:.1f}% → {curr:.1f}% ({shift:+.1f} pp)",
        })
    return {
        "operation":     "delta_mix",
        "results":       results,
        "human_summary": " | ".join(r["summary"] for r in results),
    }


def _op_percent_of_total(values, labels, fd) -> dict:
    """
    One value as % of another — for military mix, B2B share, etc.
    values=[part, total]
    """
    if len(values) != 2:
        return _err("percent_of_total requires exactly [part, total]")
    if values[1] == 0:
        return _err("Total cannot be zero.")
    result = round(values[0] / values[1] * 100, 2)
    pl, tl = _lbl(labels, 0, "part"), _lbl(labels, 1, "total")
    fav    = _favorable(result, fd)
    return {
        "operation":     "percent_of_total",
        "result":        result,
        "part":          values[0], "part_label":  pl,
        "total":         values[1], "total_label": tl,
        "favorable":     fav,
        "human_summary": (
            f"{pl} as % of {tl} = {result:.2f}%"
            + (f" ({'Favorable' if fav else 'Unfavorable'})" if fav is not None else "")
        ),
    }


def _op_index(values, labels, fd) -> dict:
    """
    Index current value against a baseline (baseline = 100).
    values=[current, baseline]
    Useful for comparing trends across metrics with different scales.
    """
    if len(values) != 2:
        return _err("index requires exactly [current, baseline]")
    if values[1] == 0:
        return _err("Baseline cannot be zero.")
    result = round(values[0] / values[1] * 100, 2)
    cl, bl = _lbl(labels, 0, "current"), _lbl(labels, 1, "baseline")
    return {
        "operation":     "index",
        "result":        result,
        "current":       values[0], "current_label":  cl,
        "baseline":      values[1], "baseline_label": bl,
        "human_summary": f"{cl} indexed to {bl} (=100): {result:.1f}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch table — the ONLY place you need to touch to add a new operation.
# Map: operation_name → handler function
# ─────────────────────────────────────────────────────────────────────────────

_OPERATIONS: dict[str, Callable] = {
    "sum":              _op_sum,
    "variance":         _op_variance,
    "variance_pct":     _op_variance_pct,
    "ratio":            _op_ratio,
    "yoy_change":       _op_yoy_change,
    "yoy_pct":          _op_yoy_pct,
    "mix_pct":          _op_mix_pct,
    "weighted_average": _op_weighted_average,
    "growth_rate":      _op_growth_rate,
    "yoy_multi":        _op_yoy_multi,
    "delta_mix":        _op_delta_mix,
    "percent_of_total": _op_percent_of_total,
    "index":            _op_index,
}


# ─────────────────────────────────────────────────────────────────────────────
# Public tool function
# ─────────────────────────────────────────────────────────────────────────────

def calculate(
    operation: str,
    values: list[float],
    labels: list[str] | None = None,
    favorable_direction: str = "higher",
) -> dict:
    """
    Perform financial calculations. ALWAYS use this — never compute inline.

    Args:
        operation: Calculation type. Available operations:

          sum              [v1, v2, …]           Total of all values
          variance         [actual, ref]          actual − reference
          variance_pct     [actual, ref]          variance as %
          ratio            [numerator, denom]     n / d
          yoy_change       [current, prior]       current − prior
          yoy_pct          [current, prior]       YoY % change
          mix_pct          [v1, v2, …]            each as % of sum
          weighted_average [v1,w1, v2,w2, …]      SUM(vi*wi)/SUM(wi)
          growth_rate      [start, end]            simple growth %
                           [start, end, n_periods] CAGR
          yoy_multi        [c1,p1, c2,p2, …]      YoY% for N pairs
          delta_mix        [cs1,ps1, cs2,ps2, …]  mix shift per category
          percent_of_total [part, total]           part as % of total
          index            [current, baseline]     indexed to baseline=100

        values:
            Numeric inputs. Order is significant — see each operation above.

        labels:
            Descriptive labels for each value. Strongly recommended.
            Passed through to all output fields for full traceability.
            Example: ["Q1_2025_revenue", "Q1_2024_revenue"]

        favorable_direction:
            Comes from RAG tool result (favorable_direction field).
            "higher"  → increase = Favorable  (revenue, starts, census…)
            "lower"   → decrease = Favorable  (drop rate, cost, attrition…)
            "neutral" → no Favorable/Unfavorable label
            DO NOT hardcode this — always pass the value from the RAG result.

    Returns:
        dict with result, inputs, favorable flag, and human_summary.
        human_summary is a pre-formatted string agents can quote directly.
    """
    if not values:
        return _err("No values provided.")

    n      = len(values)
    labels = list(labels or [f"value_{i}" for i in range(n)])

    op_key = (operation or "").lower().strip()
    handler = _OPERATIONS.get(op_key)

    if handler is None:
        valid = ", ".join(sorted(_OPERATIONS.keys()))
        return _err(
            f"Unknown operation '{operation}'. "
            f"Valid operations: {valid}"
        )

    try:
        return handler(values, labels, favorable_direction)
    except Exception as exc:
        logger.error("calculator_tool error [%s]: %s", operation, exc, exc_info=True)
        return _err(f"Calculation failed for operation '{operation}': {exc}")


calculator_tool = FunctionTool(func=calculate)