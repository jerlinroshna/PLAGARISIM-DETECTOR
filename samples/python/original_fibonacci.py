def fibonacci(n):
    if n <= 0:
        return []
    sequence = [0, 1]
    while len(sequence) < n:
        next_val = sequence[-1] + sequence[-2]
        sequence.append(next_val)
    return sequence[:n]

if __name__ == "__main__":
    result = fibonacci(10)
    print("Fibonacci sequence:", result)
