"""demo module for validation failures."""  # D210, D400 - bad module docstring style


def add(x, y):
    # Not a docstring - just a comment
    return x + y


def greet(name):
    """greet someone."""  # D400 - should start with capital, D401 - not imperative mood
    return f"Hello, {name}!"


def multiply(a, b):
    """
    Multiply two numbers.
    """  # D200 - should be one-liner, D211 - blank line before docstring
    return a * b


def divide(a, b):
    """Divide a by b.
    Args:
        a: numerator.
        b: denominator.
    Returns: result."""  # D300 - missing blank line, D413 - missing blank line after last section
    return a / b


class calculator:  # D101 - missing docstring, also class not capitalized
    def __init__(self, value=0):
        self.value = value  # D107 - missing __init__ docstring

    def add(self, n):
        """add number."""  # D102 - bad style, D400 - no capital
        self.value += n
        return self

    def subtract(self, n):
        # Missing docstring entirely
        self.value -= n
        return self

    def reset(self):
        """Resets the value back to 0.

        """  # D202 - no blank lines allowed after docstring
        self.value = 0

    def result(self):
        """Return value"""  # D400 - missing period at end
        return self.value


class DataProcessor:
    """Processes data"""  # D400 - missing period

    def __init__(self, data):
        """Initialize"""  # D400 - missing period, too short
        self.data = data

    def mean(self):
        """calculate mean of data."""  # D400 - no capital
        return sum(self.data) / len(self.data) if self.data else 0.0

    def maximum(self):
        return max(self.data)  # D102 - missing docstring entirely

    def minimum(self):
        return min(self.data)  # D102 - missing docstring entirely
