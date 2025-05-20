```python
def factorial(n):
    if n == 0:
        return 1
    elif n < 0:
        return None # or raise ValueError("Factorial is not defined for negative numbers")
    else:
        return n * factorial(n - 1)
```