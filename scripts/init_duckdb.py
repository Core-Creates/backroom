# scripts/init_duckdb.py
"""
Seed the DuckDB database once with a single row.

Usage:
  python scripts/init_duckdb.py --db path/to/database.duckdb

If --db is not provided, it uses DUCKDB_PATH or ./db/duckdb.duckdb
"""

import argparse
import os
import sys
import duckdb

DUPLICATE_HINTS = ("Duplicate", "constraint", "UNIQUE", "PRIMARY KEY")
MISSING_TABLE_HINTS = ("does not exist", "No matching table", "Catalog Error")

def resolve_db_path(arg_path: str | None) -> str:
    if arg_path:
        return arg_path
    env = os.getenv("DUCKDB_PATH")
    if env:
        return env
    return os.path.join(".", "db", "duckdb.duckdb")

def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the DuckDB with a starter row in items.")
    parser.add_argument("--db", help="Path to DuckDB file (e.g., ./db/duckdb.duckdb)")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    con = None
    try:
        con = duckdb.connect(db_path, read_only=False)
        con.execute("INSERT INTO items VALUES (1, 'slime')")
        print("Inserted seed row into items.")
        return 0
    except Exception as e:
        msg = str(e)
        if any(hint in msg for hint in DUPLICATE_HINTS):
            print("Row already exists; skipping insert.")
            return 0
        if any(hint in msg for hint in MISSING_TABLE_HINTS):
            print("Table 'items' not found. Create it first, e.g.:")
            print("  CREATE TABLE items(id INTEGER PRIMARY KEY, label TEXT);")
            return 1
        print("Insert failed:", e)
        return 1
    finally:
        if con is not None:
            con.close()
        print("Closed connection. DB at", db_path)

if __name__ == "__main__":
    raise SystemExit(main())
