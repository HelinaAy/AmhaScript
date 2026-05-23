# AmhaScript Calculator
# ደምር = add, ቀነስ = subtract, አባዛ = multiply, ክፈል = divide

ስራ ደምር(a, b):
    መልስ a + b

ስራ ቀነስ(a, b):
    መልስ a - b

ስራ አባዛ(a, b):
    መልስ a * b

ስራ ክፈል(a, b):
    ከሆነ b == 0:
        ጥራ(0)
        መልስ 0
    ካልሆነ:
        መልስ a / b

# --- Test the calculator ---
ቁጥር num1 ሰጥ 20
ቁጥር num2 ሰጥ 4

ቁጥር addition ሰጥ ደምር(num1, num2)
ቁጥር subtraction ሰጥ ቀነስ(num1, num2)
ቁጥር multiply ሰጥ አባዛ(num1, num2)
ቁጥር division ሰጥ ክፈል(num1, num2)

ጥራ(addition)
ጥራ(subtraction)
ጥራ(multiply)
ጥራ(division)
