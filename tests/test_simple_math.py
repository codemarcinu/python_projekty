import pytest
from modules.simple_math import add, subtract, multiply

def test_add_positive_numbers():
    """Testuje dodawanie dwóch dodatnich liczb."""
    assert add(2, 3) == 5
    assert add(10, 20) == 30

def test_add_negative_numbers():
    """Testuje dodawanie liczb ujemnych."""
    assert add(-2, -3) == -5

def test_subtract_positive_numbers():
    """Testuje odejmowanie dwóch dodatnich liczb."""
    assert subtract(5, 2) == 3
    assert subtract(20, 10) == 10

def test_subtract_with_negative_result():
    """Testuje odejmowanie, którego wynikiem jest liczba ujemna."""
    assert subtract(2, 5) == -3

def test_multiply_positive_numbers():
    """Testuje mnożenie dwóch dodatnich liczb całkowitych."""
    assert multiply(2, 3) == 6
    assert multiply(10, 20) == 200

def test_multiply_with_zero():
    """Testuje mnożenie przez zero."""
    assert multiply(5, 0) == 0
    assert multiply(0, 5) == 0

def test_multiply_negative_numbers():
    """Testuje mnożenie liczb ujemnych."""
    assert multiply(-2, 3) == -6
    assert multiply(2, -3) == -6
    assert multiply(-2, -3) == 6 