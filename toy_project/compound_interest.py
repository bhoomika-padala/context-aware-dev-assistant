print("this is math module file")
print("this is a part of toy_project")

def compound_interest(principal: float, rate: float, times_per_year: int, years: int) -> float:
    """Calculate compound interest.

    Args:
        principal: The initial amount of money.
        rate: Annual interest rate as a decimal (e.g., 0.05 for 5%).
        times_per_year: Number of times interest is compounded per year.
        years: Number of years the money is invested or borrowed for.

    Returns:
        The amount of money accumulated after ``years`` years, including interest.
    """
    if times_per_year <= 0:
        raise ValueError("times_per_year must be positive")
    if years < 0:
        raise ValueError("years cannot be negative")
    return principal * (1 + rate / times_per_year) ** (times_per_year * years)
