import math
import pytest

from calculator import operations as op


def test_add():
    assert op.add(2, 3) == 5.0
    assert op.add(-1, 1.5) == 0.5


def test_subtract():
    assert op.subtract(5, 2) == 3.0


def test_multiply():
    assert op.multiply(2, 4) == 8.0


def test_divide():
    assert op.divide(8, 2) == 4.0
    with pytest.raises(ZeroDivisionError):
        op.divide(1, 0)


def test_power():
    assert op.power(2, 3) == 8.0


def test_percent():
    assert op.percent(200, 10) == 20.0


def test_sqrt():
    assert op.sqrt(9) == 3.0
    with pytest.raises(ValueError):
        op.sqrt(-1)


def test_log():
    assert math.isclose(op.log(math.e), 1.0)
    assert math.isclose(op.log(8, 2), 3.0)
    with pytest.raises(ValueError):
        op.log(0)
    with pytest.raises(ValueError):
        op.log(10, 1)


