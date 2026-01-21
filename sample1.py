
import math


class Calculator:
    """Basic calculator class."""
    val=0
    def add(self, a, b):
        result = a + b
        return result

    def multiply(self, a, b):
        product = a * b
        return product

    def square_root(self, x):
        temp = x
        return math.sqrt(temp)


class DataProcessor:
    def normalize(self, data):
        total = sum(data)
        normalized = [x / total for x in data]
        return normalized

    def average(self, data):
        avg = sum(data) / len(data)
        return avg


def greet(name):
    message = f"Hello, {name}"
    return message


def factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def is_prime(n):
    if n <= 1:
        return False

    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
