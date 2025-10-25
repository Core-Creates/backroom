# db/duckdb_helper.py
"""
Centralized DuckDB connection helper for the Backroom app (Python version).

- Resolves DB path from DUCKDB_PATH or defaults to ./mydb.duckdb (project root).
- Ensures the parent directory exists.
- Creates a module-level connection.
- Applies simple PRAGMA tuning.
- Initializes the schema (table 'items') if it doesn't exist.

Exports:
- db_path: str
- con: duckdb.DuckDBPyConnection
- get_connection() -> duckdb.DuckDBPyConnection
"""
import os
import duckdb
from typing import Optional

def _resolve_db_path() -> str:
    env = os.getenv("DUCKDB_PATH")
    if env:
        return env
    return os.path.abspath(os.path.join(os.getcwd(), "mydb.duckdb"))

db_path: str = _resolve_db_path()
os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

con: Optional[duckdb.DuckDBPyConnection] = duckdb.connect(db_path, read_only=False)
con.execute("PRAGMA threads=4")

con.execute("""
CREATE TABLE IF NOT EXISTS items(
    id INTEGER,
    label TEXT
)
""")

def get_connection() -> duckdb.DuckDBPyConnection:
    global con
    try:
        con.execute("SELECT 1")
    except Exception:
        con = duckdb.connect(db_path, read_only=False)
        con.execute("PRAGMA threads=4")
        con.execute("""
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER,
            label TEXT
        )
        """)
    return con
