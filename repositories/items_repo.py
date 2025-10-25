# repositories/items_repo.py
"""
DuckDB repository equivalent of the Node.js itemsRepo.js:

Original (Node):
----------------
function insertItem(id, label) { ... }
function listItems() { ... }
function upsertItem(id, label) { ... }

Python:
-------
Provides both a class-based repo (ItemsRepo) and simple functional helpers
that accept an existing duckdb connection.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import duckdb


def _default_db_path() -> str:
    """
    Resolve the DuckDB path from env or default to ./db/duckdb.duckdb
    """
    return os.getenv("DUCKDB_PATH") or os.path.join(".", "db", "duckdb.duckdb")


def get_connection(db_path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """
    Create a new DuckDB connection.
    """
    path = db_path or _default_db_path()
    # Ensure parent directory exists to avoid connect errors when creating a new DB
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return duckdb.connect(path, read_only=False)


# ----- Functional API (accept an existing connection) -------------------------

def insert_item(con: duckdb.DuckDBPyConnection, item_id: int, label: str) -> None:
    """
    Insert a single item row.
    Mirrors: con.run("INSERT INTO items VALUES (?, ?)", [id, label], ...)
    """
    con.execute("INSERT INTO items VALUES (?, ?)", [item_id, label])


def list_items(con: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    """
    List items ordered by id.
    Mirrors: con.all("SELECT id, label FROM items ORDER BY id", ...)
    Returns a list of dicts: [{"id": ..., "label": ...}, ...]
    """
    # DuckDB returns a Relation; fetchall() yields tuples; use columns() for names
    rel = con.execute("SELECT id, label FROM items ORDER BY id")
    rows = rel.fetchall()
    cols = [d[0] for d in rel.description]  # ("id",), ("label",)
    return [dict(zip(cols, row)) for row in rows]


def upsert_item(con: duckdb.DuckDBPyConnection, item_id: int, label: str) -> None:
    """
    Simple upsert using DELETE + INSERT to mirror the Node version.
    """
    # Use a small transaction to keep DELETE+INSERT atomic
    try:
        con.execute("BEGIN")
        con.execute("DELETE FROM items WHERE id = ?", [item_id])
        con.execute("INSERT INTO items VALUES (?, ?)", [item_id, label])
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise


# ----- Class-based repo (manages its own connection) -------------------------

class ItemsRepo:
    """
    Convenience wrapper managing its own connection.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or _default_db_path()
        self.con = get_connection(self.db_path)

    def insert_item(self, item_id: int, label: str) -> None:
        insert_item(self.con, item_id, label)

    def list_items(self) -> List[Dict[str, Any]]:
        return list_items(self.con)

    def upsert_item(self, item_id: int, label: str) -> None:
        upsert_item(self.con, item_id, label)

    def close(self) -> None:
        try:
            self.con.close()
        finally:
            pass


if __name__ == "__main__":
    # Tiny demo: ensure table exists, seed/print
    con = get_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY,
            label TEXT
        )
    """)
    # Demo operations
    upsert_item(con, 1, "slime")
    insert_item(con, 2, "velvet")
    print(list_items(con))
    con.close()
