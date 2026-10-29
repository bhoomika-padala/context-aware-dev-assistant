print("this is math module file")
print("this is a part of toy_project")

def factorial(n):
    """Return the factorial of a non‑negative integer n.

    The function returns 1 for n == 0. For negative inputs or non‑integers,
    it raises a ``ValueError``.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non‑negative integer")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
