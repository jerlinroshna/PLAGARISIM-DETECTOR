# CodeGuard AST: System Architecture & Design

## 1. Overview
**CodeGuard AST** is an academic source code plagiarism screening platform designed to detect code plagiarism across current and historical academic years. Unlike traditional text-only diff engines, CodeGuard combines:
1. **N-gram Token Winnowing & Text Sequence Alignment** (40% weight by default).
2. **Abstract Syntax Tree (AST) Structural Comparison** (60% weight by default).

This multi-tiered analysis reliably detects plagiarism even when students rename variables, modify comments, reformat indentation, or reorder variable definitions.

---

## 2. Directory Structure

```
├── .env.example             # Template for environment configuration
├── .gitignore               # Excludes SQLite databases, caches, user uploads, IDE files
├── README.md                # Main project summary and quickstart guide
├── requirements.txt         # Production and runtime Python dependencies
├── run.py                   # Standard application runner script
├── app.py                   # Flask Application Factory and error handlers
├── auth.py                  # Authentication routines, session management, and RBAC
├── config.py                # Centralized application and analysis parameters
├── database.py              # SQLite schema, connection lifecycle, queries, and seeding
│
├── analyzers/               # Multi-language AST & text analysis engines
│   ├── __init__.py
│   ├── base.py              # Abstract base analyzer interface
│   ├── comparator.py        # Composite comparator combining Text + AST scores
│   ├── text_analyzer.py     # Winnowing, tokenization, and line matching
│   ├── ast_c_cpp.py         # C/C++ lexer, preprocessor stripping, AST mapper
│   ├── ast_java.py          # Java AST parser (javalang) with identifier abstraction
│   ├── ast_javascript.py    # JavaScript AST parser (esprima) with symbol mapping
│   └── ast_python.py        # Python AST parser (built-in ast) with node normalization
│
├── routes/                  # Modular Flask Blueprints (Presentation & Controller)
│   ├── __init__.py
│   ├── auth_routes.py       # Login, logout, session management
│   ├── student_routes.py    # Submissions, report viewing, isolation checks
│   └── faculty_routes.py    # Assignments, reviews, historical archives, CSV export
│
├── static/                  # Client-side static assets
│   ├── css/
│   │   └── style.css        # Responsive styling and diff highlighting
│   └── js/
│       └── main.js          # Synchronized side-by-side scrolling and UI controls
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html            # Core layout with navigation and alerts
│   ├── auth/                # Login templates
│   ├── faculty/             # Faculty dashboard, assignments, reviews, comparisons
│   └── student/             # Student dashboard, submission portal, reports
│
├── data/                    # Data persistence layer
│   ├── demo_accounts.csv    # Exported credentials for test accounts
│   ├── plagiarism_detector.db # SQLite database
│   └── seed_historical/    # Initial seed sources
│
├── uploads/                 # Runtime storage for user submissions (Git-ignored)
│   ├── historical/          # Archives of previous academic years
│   └── submissions/         # Live student submissions
│
├── samples/                 # Sample code suites for manual testing & benchmarking
│   ├── c/                   # Original and renamed C programs
│   ├── java/                # Original and renamed Java classes
│   ├── javascript/          # Original and renamed JavaScript scripts
│   └── python/              # Original and renamed Python modules
│
├── tests/                   # Automated unittest suite
│   ├── test_analyzers.py    # AST normalization & similarity tests
│   ├── test_auth.py         # Authentication & RBAC boundary checks
│   └── test_workflow.py     # End-to-end integration workflow tests
│
├── docs/                    # Architecture and documentation
│   └── ARCHITECTURE.md      # This document
│
└── misc/                    # Preserved non-code workspace files
```

---

## 3. Plagiarism Detection Pipeline

1. **Upload & Verification**:
   - File is sanitized, validated against `ALLOWED_EXTENSIONS`, and stored statically (never executed).
2. **Text Comparison**:
   - Comments and whitespace are stripped.
   - Code is normalized into rolling n-gram hash footprints (winnowing).
3. **AST Parsing & Normalization**:
   - The file is parsed into an Abstract Syntax Tree based on the detected language.
   - All variable names, parameters, and function identifiers are mapped into canonical tokens (`VAR_0`, `VAR_1`, `FUNC_0`).
   - Structural nodes (`For`, `While`, `If`, `BinaryOp`) are extracted into an AST sequence string.
4. **Scoring**:
   - `Combined Score = (0.40 * Text Score) + (0.60 * AST Score)`
   - Classification:
     - **$\ge 70\%$**: High Similarity
     - **$30\% - 69\%$**: Medium Similarity
     - **$< 30\%$**: Low Similarity

---

## 4. Security & Isolation Controls

- **Zero-Code Execution**: Uploaded files are strictly treated as text for lexical and syntactic parsing.
- **Role-Based Access Control (RBAC)**:
  - Students cannot view other students' private code or full historical archives.
  - Faculty can configure assignments, view side-by-side AST comparisons, and export audit trails.
- **CSRF & Session Security**: Flask sessions use signed cookies with strong secret keys.
