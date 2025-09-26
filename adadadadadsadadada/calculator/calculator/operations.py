from __future__ import annotations

import math
from typing import Union

Number = Union[int, float]


def add(left: Number, right: Number) -> float:
    """Return the sum of two numbers."""
    return float(left) + float(right)


def subtract(left: Number, right: Number) -> float:
    """Return the difference of two numbers (left - right)."""
    return float(left) - float(right)


def multiply(left: Number, right: Number) -> float:
    """Return the product of two numbers."""
    return float(left) * float(right)


def divide(left: Number, right: Number) -> float:
    """Return the quotient (left / right).

    Raises ZeroDivisionError if right is zero.
    """
    denominator = float(right)
    if denominator == 0.0:
        raise ZeroDivisionError("Division by zero is not allowed")
    return float(left) / denominator


def power(base: Number, exponent: Number) -> float:
    """Return base raised to the power of exponent."""
    return float(base) ** float(exponent)


def percent(value: Number, percentage: Number) -> float:
    """Return the percentage of a value (value * percentage / 100)."""
    return float(value) * (float(percentage) / 100.0)


def sqrt(value: Number) -> float:
    """Return the square root of value.

    Raises ValueError if value is negative.
    """
    numeric_value = float(value)
    if numeric_value < 0.0:
        raise ValueError("Square root of a negative number is not defined for real numbers")
    return math.sqrt(numeric_value)


def log(value: Number, base: Number = math.e) -> float:
    """Return the logarithm of value with the given base (default: e).

    Raises ValueError for invalid domain (value <= 0) or invalid base (base <= 0 or base == 1).
    """
    numeric_value = float(value)
    numeric_base = float(base)
    if numeric_value <= 0.0:
        raise ValueError("Logarithm undefined for non-positive values")
    if numeric_base <= 0.0 or numeric_base == 1.0:
        raise ValueError("Logarithm base must be positive and not equal to 1")
    return math.log(numeric_value, numeric_base)


