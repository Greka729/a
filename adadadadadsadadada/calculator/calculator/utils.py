from __future__ import annotations

import math


def format_result(value: float, max_digits: int = 12) -> str:
    """Format numeric result to a readable string.

    - Show integers without .0 if close to an integer
    - Limit precision to avoid long floats
    - Use scientific notation for very large/small numbers
    """
    if math.isfinite(value):
        if abs(value - round(value)) < 1e-12:
            return str(int(round(value)))
        text = f"{value:.{max_digits}g}"
        # Ensure decimal point for numbers like 1e-05 is fine
        return text
    if math.isnan(value):
        return "NaN"
    return "Infinity" if value > 0 else "-Infinity"


