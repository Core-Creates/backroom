from pathlib import Path
import duckdb
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backroom")

def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def get_data_paths():
    root = project_root()
    data = root / "data"
    raw = data / "raw"
    processed = data / "processed"
    shelves = data / "shelves"
    return raw, processed, shelves

def ensure_dirs():
    raw, processed, shelves = get_data_paths()
    for d in (raw, processed, shelves):
        d.mkdir(parents=True, exist_ok=True)

def write_duckdb(csv_path: str, db_path: str, table_name: str):

    conn = duckdb.connect(database=db_path)
    conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
    conn.close()
    logger.info(f"Wrote DuckDB database → {db_path} with table '{table_name}'")