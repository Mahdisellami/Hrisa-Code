def add(a, b):
    try:
        a = int(a)
        b = int(b)
        return a + b
    except ValueError:
        return "Error: Both inputs must be integers."

def subtract(a, b):
    try:
        a = int(a)
        b = int(b)
        return a - b
    except ValueError:
        return "Error: Both inputs must be integers."

def multiply(a, b):
    try:
        a = int(a)
        b = int(b)
        return a * b
    except ValueError:
        return "Error: Both inputs must be integers."

def divide(a, b):
    try:
        a = int(a)
        b = int(b)
        if b == 0:
            return "Error: Division by zero is not allowed."
        return a / b
    except ValueError:
        return "Error: Both inputs must be integers."