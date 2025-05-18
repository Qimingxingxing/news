def sum_using_loop():
    total = 0
    for i in range(1, 101):
        total += i
    return total

def sum_using_formula():
    # Using the arithmetic sequence formula: n(a1 + an)/2
    n = 100  # number of terms
    a1 = 1   # first term
    an = 100 # last term
    return n * (a1 + an) // 2

if __name__ == "__main__":
    # Calculate using both methods
    loop_result = sum_using_loop()
    formula_result = sum_using_formula()
    
    print(f"Sum of numbers from 1 to 100 using loop: {loop_result}")
    print(f"Sum of numbers from 1 to 100 using formula: {formula_result}")

