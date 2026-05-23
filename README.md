# AmhaScript
AmhaScript is a beginner-friendly programming language that uses Amharic keywords and translates them into Python code.  
The project was developed as a group project for the Programming Languages course at Adama Science and Technology University.

---

## Project Overview

AmhaScript is designed to help Ethiopian beginners learn programming concepts using their native language. The language translates Amharic-based syntax into executable Python code using:

- Lexer
- Recursive-Descent Parser
- Abstract Syntax Tree (AST)
- Python Code Generator

The project supports variables, arithmetic operations, conditionals, loops, functions, and function calls.

---

## Features

- Amharic programming keywords
- Unicode (UTF-8) support
- Python code generation
- AST-based architecture
- Recursive-descent parsing
- Beginner-friendly syntax
- Error messages in Amharic

---

## Example

### AmhaScript Code

```amharic
ቁጥር x ሰጥ 10
ቁጥር y ሰጥ 5
ቁጥር z ሰጥ x + y
ጥራ(z)
```

### Generated Python Code

```python
x = 10
y = 5
z = x + y
print(z)
```

---

## Project Structure

```text
AmhaScript/
│
├── calculator.py
├── control.py
├── functions.py
├── mytest.py
├── variables.py
├── calculator.as
├── run_calculator.py
├── README.md
└── translator.py
```

---

## How to Run

### Using Command Line

```bash
python translator.py program.as
```

### Using Python

```python
from translator import run
run('calculator.as')
```

---

## Technologies Used

- Python
- Unicode UTF-8 Processing
- Recursive-Descent Parsing
- AST (Abstract Syntax Tree)

---

## Course Information

**Course:** Programming Languages — CSEg 4306  
**University:** Adama Science and Technology University  
**Instructor:** Ms Hiwot Habtamu

---

## Group Members

1. Hilina Ayalew — UGR/30686/15  - section 1
2. Etsubdink Gedyon — UGR/30493/15  - section 1
3. Yoseph Ayalew — UGR/31462/15  - section 1
4. Tinbite Ermiyas — UGR/31309/15  - section 1
5. Netsereab Asefa — UGR/31078/15  - section 1

---

## License

This project was developed for educational purposes only.
