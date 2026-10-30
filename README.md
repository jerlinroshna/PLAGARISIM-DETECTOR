# CodeGuard AST: SIH-Aligned Source Code Plagiarism Detector Across Historical Submissions

A complete, full-stack web application designed for academic code plagiarism screening. The system compares student submissions against historical source code submitted across previous academic years using multi-language text similarity and Abstract Syntax Tree (AST) structural analysis.

---

## 1. Key Features

- **Multi-Language AST Structural Analysis**:
  - **Python (`.py`)**: Built-in Python `ast` parser with variable/identifier anonymization and AST sequence alignment.
  - **C (`.c`) & C++ (`.cpp`)**: Structural AST and grammar tokenizer with preprocessor directive stripping and canonical identifier mapping.
  - **Java (`.java`)**: `javalang` AST compilation unit and tokenizer analysis with identifier abstraction.
  - **JavaScript (`.js`)**: `esprima` AST parser with syntax tree traversal and symbol normalization.
- **Identifier Normalization**:
  - Renaming variables (e.g., `total = a + b` vs `result = x + y`) yields **100% AST structural similarity**.
- **Historical Code Repository**:
  - Archives previous academic year code submissions organized by academic year (e.g., `2022-2023`, `2023-2024`, `2024-2025`), course subject, assignment, and language.
- **Side-by-Side Synchronized Diff Inspection**:
  - Two parallel code viewing panes with synchronized scrolling and highlighted matching blocks.
- **Automated Score Breakdown**:
  - Text Similarity % (token winnowing & line sequence matching).
  - AST Structural Similarity % (syntactic structure alignment & feature vector similarity).
  - Combined Score: **40% Text + 60% AST Structure** (configurable in `config.py`).
  - Classifications: `High Similarity` ($\ge 70\%$), `Medium Similarity` ($30\% - 69\%$), `Low Similarity` ($< 30\%$).
- **Role-Based Access Control (RBAC)**:
  - **Students**: Can submit code, view only their own submissions and permitted feedback without leaking unrestricted historical repository code or other students' private solutions.
  - **Faculty**: Manage assignments, upload historical records, inspect comparisons, record review notes (`Pending Review`, `Reviewed`, `Further Investigation Required`, `No Concern Identified`), and export CSV reports.
- **Strict Execution Safety**:
  - Uploaded code is **never executed**. It is treated strictly as static data for parsing and comparison.

---

## 2. Pre-seeded Demo Accounts

The database automatically initializes **60 Student demo accounts** and **20 Faculty demo accounts** without duplication:

| Role | Username Range | Display Name | Demo Password | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | `STU001` &ndash; `STU060` | Student 001 &ndash; Student 060 | `Student@123` | Student portal testing |
| **Faculty** | `FAC001` &ndash; `FAC020` | Faculty 001 &ndash; Faculty 020 | `Faculty@123` | Instructor review & management |

A development CSV reference is generated at `data/demo_accounts.csv` and can also be downloaded directly from the Faculty **Demo Accounts** page.

---

## 3. Technology Stack

- **Backend**: Python 3.10+ / Flask 3.x
- **Database**: SQLite 3 (with foreign key enforcement and indexed queries)
- **Code Analyzers**:
  - Python: `ast`
  - Java: `javalang`
  - JavaScript: `esprima`
  - C / C++: Structural Lexer and AST Mapper (`pycparser` compatible)
- **Frontend**: Clean College Portal Design System (HTML5, Responsive CSS, Vanilla JavaScript)
- **Testing**: Python `unittest` suite (16 comprehensive tests)

---

## 4. Installation & Local Setup in VS Code

### Step 1: Open Project in VS Code
Open this folder in VS Code or navigate to it in your terminal:
```powershell
cd "c:\Users\jerli\OneDrive\ドキュメント\New folder"
```

### Step 2: Install Dependencies
Install all required libraries:
```powershell
pip install -r requirements.txt
```

### Step 3: Initialize Database (Automatic or Manual)
The database initializes automatically when running the application. To initialize or verify manually:
```powershell
python -c "import database; database.init_db(); print('Database ready!')"
```

### Step 4: Start the Flask Application
Run the local server using `run.py` or `app.py`:
```powershell
python run.py
```
The application will launch on:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

For complete system architecture, folder layout details, and pipeline flow, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Pre-configured sample files for all languages are provided in [samples/](samples/) for testing.

---

## 5. Running the Test Suite

Run all automated unit and integration tests:
```powershell
python -m unittest discover tests
```

### Test Coverage Highlights:
- `tests/test_auth.py`: Verifies seeding of 60 student and 20 faculty accounts, password hashing, idempotent restarts, and RBAC authorization boundaries.
- `tests/test_analyzers.py`: Verifies AST identifier normalization across Python, C/C++, Java, and JavaScript (`total = a + b` vs `result = x + y`), loop structures, token winnowing, and syntax error resilience.
- `tests/test_workflow.py`: End-to-end integration test of student submission, historical match lookup, side-by-side reporting, faculty reviews, student isolation (403 Forbidden), and CSV export.

---

## 6. Supported Programming Languages

| Language | Extension | Analyzer Engine | Identifier Normalization | Tested Status |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `.py` | Python `ast` | Anonymizes variables/functions to `VAR_0`, `VAR_1` while preserving builtins | **Fully Supported & Tested** |
| **C** | `.c` | Structural Lexer + AST Mapper | Strips `#include`/directives; maps variables, control flow, functions | **Fully Supported & Tested** |
| **C++** | `.cpp`, `.cc` | Structural Lexer + AST Mapper | Normalizes namespace symbols, types, loops, statements | **Fully Supported & Tested** |
| **Java** | `.java` | `javalang` AST & Tokenizer | Normalizes classes, methods, parameters, and expressions | **Fully Supported & Tested** |
| **JavaScript** | `.js` | `esprima` AST Parser | Anonymizes identifiers, literals, and AST control statements | **Fully Supported & Tested** |

---

## 7. Known Limitations & Best Practices

1. **Static Analysis Only**:
   - The system analyzes code syntactically and structurally as data. It does not execute dynamic test suites or bytecode execution.
2. **Missing Historical Records**:
   - If an assignment has no corresponding historical submissions in the requested language, the system cleanly displays:
     `"No comparable historical submissions found."`
3. **Cross-Language Plagiarism**:
   - Cross-language comparison (e.g., comparing Python directly with Java) is marked as experimental and disabled by default to prevent false positives between divergent language constructs.
4. **Syntax Errors in Submitted Code**:
   - If a student submits code with syntax errors that prevent AST parsing, the system logs the parse limitation, falls back to tokenized text similarity, and alerts the instructor without crashing.

---

## 8. Git Collaboration & Continuous Push Policy

> **Mandatory Policy**: **Always push all changes to Git immediately.**  
> Whenever any file is added, edited, or fixed, commit and push your changes to GitHub right away. Always pull latest before starting (`git pull origin main`), and always push after every work session (`git push origin main`) to ensure all collaborators are in sync without merge conflicts.

### Standard Git Sync Protocol:
```powershell
# 1. Pull latest remote changes first
git pull origin main

# 2. Check current modified files
git status

# 3. Stage all modified and new files
git add .

# 4. Commit with a clear, descriptive message
git commit -m "feat/fix: describe your changes here"

# 5. Always push immediately to the remote branch
git push origin main
```

### Git Rules for All Team Members & Agents:
1. **Never leave uncommitted work**: Commit and push at the end of each feature or bug fix.
2. **Pull before starting**: Always fetch and pull `origin main` before starting new edits to prevent merge collisions.
3. **Resolve conflicts cleanly**: If any conflict occurs, test thoroughly and commit the resolution before pushing.
4. **Run test suite before push**: Ensure tests pass via `python -m unittest tests.test_auth tests.test_workflow tests.test_grok_integration`.

