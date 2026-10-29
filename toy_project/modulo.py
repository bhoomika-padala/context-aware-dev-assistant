print("this is math module file")
"""Modulo utility module.

Provides a simple function to compute the remainder of integer division.
"""

def modulo(a, b):
    """Return the remainder of a divided by b.

    Equivalent to ``a % b``. Raises ``ZeroDivisionError`` if ``b`` is zero.
    """
    return a % b
