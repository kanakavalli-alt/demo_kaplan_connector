from google.adk.tools import FunctionTool


def calculate(operation: str, values: list[float], labels: list[str] = None) -> dict:
    """
    Perform financial calculations. ALWAYS use this — never compute inline.

    Args:
        operation: One of:
          'sum'           → total of all values
          'variance'      → actual − reference          [actual, reference]
          'variance_pct'  → variance as %               [actual, reference]
          'ratio'         → numerator / denominator     [numerator, denominator]
          'yoy_change'    → current − prior year        [current, prior]
          'yoy_pct'       → YoY % change                [current, prior]
        values: Numeric inputs for the operation.
        labels: Optional descriptive labels for each value (improves readability).

    Returns:
        dict with result, inputs, and a favorable flag where applicable.
    """
    if not values:
        return {"error": "No values provided."}

    labels = labels or [f"value_{i}" for i in range(len(values))]

    if operation == "sum":
        return {
            "operation": "sum",
            "result": sum(values),
            "inputs": dict(zip(labels, values)),
        }

    if operation == "variance":
        if len(values) != 2:
            return {"error": "variance requires exactly [actual, reference]"}
        result = values[0] - values[1]
        return {
            "operation":  "variance",
            "result":     result,
            "actual":     values[0],
            "reference":  values[1],
            "favorable":  result > 0,
        }

    if operation == "variance_pct":
        if len(values) != 2:
            return {"error": "variance_pct requires exactly [actual, reference]"}
        if values[1] == 0:
            return {"error": "Reference value cannot be zero."}
        result = round(((values[0] - values[1]) / values[1]) * 100, 2)
        return {
            "operation":  "variance_pct",
            "result":     result,
            "actual":     values[0],
            "reference":  values[1],
            "favorable":  result > 0,
        }

    if operation == "ratio":
        if len(values) != 2:
            return {"error": "ratio requires exactly [numerator, denominator]"}
        if values[1] == 0:
            return {"error": "Denominator cannot be zero."}
        return {
            "operation":   "ratio",
            "result":      round(values[0] / values[1], 4),
            "numerator":   values[0],
            "denominator": values[1],
        }

    if operation == "yoy_change":
        if len(values) != 2:
            return {"error": "yoy_change requires exactly [current, prior]"}
        result = values[0] - values[1]
        return {
            "operation": "yoy_change",
            "current":   values[0],
            "prior":     values[1],
            "change":    result,
            "favorable": result > 0,
        }

    if operation == "yoy_pct":
        if len(values) != 2:
            return {"error": "yoy_pct requires exactly [current, prior]"}
        if values[1] == 0:
            return {"error": "Prior year value cannot be zero."}
        result = round(((values[0] - values[1]) / values[1]) * 100, 2)
        return {
            "operation":  "yoy_pct",
            "current":    values[0],
            "prior":      values[1],
            "change_pct": result,
            "favorable":  result > 0,
        }

    return {
        "error": (
            f"Unknown operation '{operation}'. "
            "Valid: sum, variance, variance_pct, ratio, yoy_change, yoy_pct"
        )
    }


calculator_tool = FunctionTool(func=calculate)