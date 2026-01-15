# Implementation Documentation - Simple RDBMS in Python

## Goal
Design and implement a simple relational database management system (RDBMS) in Python, supporting basic generic SQL commands, persistence, indexing, and a demonstration web app.

## Architecture Overview

### 1. Core Engine (`/simple_db/core`)
- **Database**: Manages a collection of tables. Handles starting/stopping and persistent loading.
- **Table**: Manages rows and metadata (schema).
    - Stores rows as a list of dictionaries.
    - Manages `indexes` (dictionary mapping value -> row index).
    - Implements CRUD logic (`insert`, `select`, `update`, `delete`).
- **Column**: Metadata class (name, type, constraints like PK/Unique).

### 2. Query Processor (`/simple_db/sql`)
- **Executor**: Takes SQL strings, passes them to the Parser, and executes methods on the `Database` instance.
- **Parser**: A Regex-based parser to convert SQL strings into structured `Query` dictionaries.
- **Supported Commands**:
    - `CREATE TABLE table_name (col1 type [PK], col2 type)`
    - `INSERT INTO table_name (col1, col2) VALUES (val1, val2)`
    - `SELECT * FROM table [WHERE col=val] [JOIN other_table ON ...]`
    - `UPDATE table SET col=val WHERE ...`
    - `DELETE FROM table WHERE ...`

### 3. Interface (`/simple_db`)
- **REPL (`cli.py`)**: An interactive command-line loop to accept SQL and display results.
- **Web App (`webapp_server.py`)**: A simple `http.server` implementation that processes POST requests to perform database operations, demonstrating the usage of the RDBMS in a real application.

## Data Structures & Persistence
- **Row**: Represented as a standard Python `dict`.
- **Index**: A hash map (`dict`) where `{ value: row_index }`. This provides O(1) lookups for Unique constraints and Primary Keys.
- **Storage**: Data is persisted as JSON files in a `db_data/` directory. Each table matches a single JSON file containing its schema and rows.

## Data Types Supported
- `int` (Integer)
- `str` (String)
- `float` (Float)
- `bool` (Boolean)

## Implementation Details

### Core Logic
The `Table` class enforces schema constraints on insertion.
- **Primary Key**: Checks internal index to ensure uniqueness.
- **Unique**: Checks internal index to ensure uniqueness.
- **Not Null**: Enforced by default unless specified otherwise.

### SQL Parsing
The parsing logic uses Python's `re` module to identify command patterns. It extracts table names, columns, and values.
- **Where Clause**: Currently supports basic equality checks (e.g., `id=1`).
- **Joins**: Implemented as a Nested Loop Join. It iterates through the left table and finds matching rows in the right table based on the join condition.

## Verification
Two test suites verify the correctness of the system:
1. `test_core.py`: Direct unit tests against the Python classes (`Database`, `Table`).
2. `test_sql.py`: Integration tests passing raw SQL strings to the `SQLExecutor`.
