#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backroom Data Cleaning Script  M5 (Printable, Single-File)
-----------------------------------------------------------
Purpose:
  Tailored cleaner for the M5 Forecasting - Accuracy dataset. Converts the wide daily
  sales matrices (d_1..d_N) into a tidy long table, joins calendar and prices, parses dates,
  checks ranges, and emits:
    1) m5_clean_long.csv  row per (store_id, item_id, date)
    2) dq_report.md  human-readable data quality report
    3) (optional) Parquet export: single file or partitioned
    4) (optional) sample CSV with first N rows

Inputs Supported (any combo):
   --m5-zip path/to/m5-forecasting-accuracy.zip  (official Kaggle bundle)
   OR explicit CSVs: --sales-csv, --calendar-csv, --prices-csv
"""

from __future__ import annotations
import argparse
import io
import os
import re
import zipfile
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

PRICE_MIN, PRICE_MAX = 0.0, 1_000_000.0
QTY_MIN, QTY_MAX = 0, 1_000_000
MISSING_SENTINELS = {"n/a", "na", "null", "none", "nan", "", "-", "?"}

ID_COLS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
CAL_KEEP = [
    "d", "date", "wm_yr_wk", "weekday", "wday", "month", "year",
    "event_name_1", "event_type_1", "event_name_2", "event_type_2",
    "snap_CA", "snap_TX", "snap_WI",
]
PRICES_KEEP = ["store_id", "item_id", "wm_yr_wk", "sell_price"]
D_COL_PREFIX = "d_"

def _read_csv_any(path_or_buf, **kw) -> pd.DataFrame:
    return pd.read_csv(path_or_buf, dtype=str, keep_default_na=False, na_values=list(MISSING_SENTINELS), **kw)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"[^A-Za-z0-9]+", "_", c.strip().lower()).strip("_") for c in df.columns]
    return df

def _strip(text: Any) -> Any:
    if pd.isna(text) or not isinstance(text, str):
        return text
    t = re.sub(r"[\u0000-\u001F\u007F]", "", text)
    return re.sub(r"\s+", " ", t).strip()

def _to_float(x: Any):
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NA
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return pd.NA

def _to_int(x: Any):
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NA
    try:
        return int(float(str(x).replace(",", "")))
    except Exception:
        return pd.NA

def _to_date_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")

@dataclass
class CleanStats:
    initial_rows_sales: int = 0
    final_rows_long: int = 0
    duplicates_removed: int = 0
    price_out_of_bounds: int = 0
    qty_out_of_bounds: int = 0
    nulls_by_col: Dict[str, int] = field(default_factory=dict)

def load_m5(
    m5_zip: Optional[str] = None,
    sales_csv: Optional[str] = None,
    calendar_csv: Optional[str] = None,
    prices_csv: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if m5_zip:
        if not os.path.exists(m5_zip):
            raise FileNotFoundError(m5_zip)
        with zipfile.ZipFile(m5_zip) as z:
            with z.open("sales_train_validation.csv") as f:
                sales = _read_csv_any(f)
            with z.open("calendar.csv") as f:
                calendar = _read_csv_any(f)
            with z.open("sell_prices.csv") as f:
                prices = _read_csv_any(f)
    else:
        if not (sales_csv and calendar_csv and prices_csv):
            raise ValueError("Provide --m5-zip OR all of --sales-csv, --calendar-csv, --prices-csv")
        sales = _read_csv_any(sales_csv)
        calendar = _read_csv_any(calendar_csv)
        prices = _read_csv_any(prices_csv)
    return _normalize_columns(sales), _normalize_columns(calendar), _normalize_columns(prices)

def sales_wide_to_long(sales_wide: pd.DataFrame) -> pd.DataFrame:
    day_cols = [c for c in sales_wide.columns if c.startswith(D_COL_PREFIX)]
    id_cols = [c for c in ID_COLS if c in sales_wide.columns]
    long_df = sales_wide.melt(id_vars=id_cols, value_vars=day_cols, var_name="d", value_name="sold_qty")
    for c in id_cols + ["d"]:
        long_df[c] = long_df[c].map(_strip).astype("string")
    long_df["sold_qty"] = long_df["sold_qty"].map(_to_int).astype("Int64")
    return long_df

def join_calendar_prices(long_df: pd.DataFrame, calendar: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    calendar = calendar[[c for c in CAL_KEEP if c in calendar.columns]].copy()
    for c in ["date", "weekday", "event_name_1", "event_type_1", "event_name_2", "event_type_2"]:
        if c in calendar.columns:
            calendar[c] = calendar[c].map(_strip).astype("string")
    if "date" in calendar.columns:
        calendar["date"] = _to_date_series(calendar["date"])

    prices = prices[[c for c in PRICES_KEEP if c in prices.columns]].copy()
    for c in ["store_id", "item_id", "wm_yr_wk"]:
        if c in prices.columns:
            prices[c] = prices[c].map(_strip).astype("string")
    if "sell_price" in prices.columns:
        prices["sell_price"] = prices["sell_price"].map(_to_float).astype("Float64")

    if "d" not in calendar.columns:
        cal_map = calendar.reset_index().rename(columns={"index": "d_index"})
        cal_map["d"] = cal_map["d_index"].add(1).map(lambda x: f"d_{x}").astype("string")
        cal_map.drop(columns=["d_index"], inplace=True)
    else:
        cal_map = calendar

    out = long_df.merge(cal_map, on="d", how="left", validate="m:1")

    price_keys = [k for k in ["store_id", "item_id", "wm_yr_wk"] if k in out.columns and k in prices.columns]
    if len(price_keys) == 3:
        out = out.merge(prices, on=price_keys, how="left", validate="m:1")
    return out

def reasonableness_checks(df: pd.DataFrame):
    issues = {"qty_out_of_bounds": 0, "price_out_of_bounds": 0}
    if "sold_qty" in df.columns:
        bad = ~df["sold_qty"].isna() & ((df["sold_qty"] < QTY_MIN) | (df["sold_qty"] > QTY_MAX))
        issues["qty_out_of_bounds"] = int(bad.sum())
        df.loc[bad, "sold_qty"] = pd.NA
    if "sell_price" in df.columns:
        badp = ~df["sell_price"].isna() & ((df["sell_price"] < PRICE_MIN) | (df["sell_price"] > PRICE_MAX))
        issues["price_out_of_bounds"] = int(badp.sum())
        df.loc[badp, "sell_price"] = pd.NA
    if {"sold_qty", "sell_price"}.issubset(df.columns):
        df["revenue"] = (df["sold_qty"].astype("Float64") * df["sell_price"].astype("Float64")).astype("Float64")
    return df, issues

def build_report(stats: CleanStats, nulls_by_col: Dict[str, int], notes: str) -> str:
    s = io.StringIO()
    print("# Data Quality Summary\n", file=s)
    print(f"- Initial M5 sales rows (wide): {stats.initial_rows_sales}", file=s)
    print(f"- Final rows (long): {stats.final_rows_long}", file=s)
    print(f"- Duplicates removed: {stats.duplicates_removed}", file=s)
    if stats.qty_out_of_bounds:
        print(f"- Qty out-of-bounds set to null: {stats.qty_out_of_bounds}", file=s)
    if stats.price_out_of_bounds:
        print(f"- Price out-of-bounds set to null: {stats.price_out_of_bounds}", file=s)
    print("\n## Nulls by Column", file=s)
    for c, n in sorted(nulls_by_col.items()):
        print(f"- {c}: {n}", file=s)
    print("\n## Processing Notes", file=s)
    print(notes, file=s)
    return s.getvalue()

# ---- Parquet helpers (single-file or partitioned) ----
def write_duckdb(out_csv: str, db_path: str, table_name: str = "m5_clean_long") -> None:
    """
    Create (or open) a DuckDB database and load the cleaned CSV into a table.
    Overwrites the table if it already exists.
    """
    try:
        import duckdb
    except ImportError as e:
        raise RuntimeError(
            "DuckDB export requested but duckdb is not installed. "
            "Install with: pip install duckdb"
        ) from e

    con = duckdb.connect(db_path)
    # Create or replace the table using DuckDB's zero-copy CSV reader
    con.execute(f"DROP TABLE IF EXISTS {duckdb.escape_identifier(table_name)};")
    con.execute(f"""
        CREATE TABLE {duckdb.escape_identifier(table_name)} AS
        SELECT * FROM read_csv_auto('{out_csv}', SAMPLE_SIZE=-1);
    """)
    # Optional: add a few handy indexes (comment out if not needed)
    for col in ["state_id", "store_id", "item_id", "date", "wm_yr_wk"]:
        try:
            con.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON {duckdb.escape_identifier(table_name)}({duckdb.escape_identifier(col)});")
        except Exception:
            pass
    con.close()
    print(f"DuckDB written: {db_path} (table={table_name})")

def write_parquet_with_fallback(
    out_csv: str,
    parquet_path: str,
    partition_by: Optional[List[str]] = None
) -> None:
    """
    Try pandas.to_parquet first (pyarrow/fastparquet). If unavailable, fallback to DuckDB.
    If `partition_by` is provided, `parquet_path` is treated as a directory output.
    """
    # Attempt pandas first (single-file only if no partitioning)
    if partition_by in (None, [], ()):
        try:
            import pyarrow  # noqa: F401
            import pandas as pd
            df = pd.read_csv(out_csv, low_memory=False)
            df.to_parquet(parquet_path, index=False)
            print(f"Parquet saved (pandas): {parquet_path}")
            return
        except Exception as e:
            print(f"pandas.to_parquet not used ({e}); falling back to DuckDB...")
    else:
        print("Partitioned export requested; using DuckDB backend.")

    # DuckDB fallback (handles both single-file and partitioned)
    try:
        import duckdb
    except ImportError:
        raise RuntimeError(
            "Parquet export requested but neither pyarrow/fastparquet nor duckdb is available. "
            "Install one of: pip install pyarrow OR pip install duckdb"
        )
    con = duckdb.connect()
    if partition_by:
        # directory output
        os.makedirs(parquet_path, exist_ok=True)
        cols = ", ".join(partition_by)
        con.execute(f"""
        COPY (
          SELECT *
          FROM read_csv_auto('{out_csv}', SAMPLE_SIZE=-1)
        ) TO '{parquet_path.replace("'", "''")}'
        (FORMAT PARQUET, PARTITION_BY ({cols}));
        """)
        print(f"Partitioned Parquet written to {parquet_path} (by {', '.join(partition_by)})")
    else:
        con.execute(f"""
        COPY (
          SELECT *
          FROM read_csv_auto('{out_csv}', SAMPLE_SIZE=-1)
        ) TO '{parquet_path.replace("'", "''")}'
        (FORMAT PARQUET);
        """)
        print(f"Parquet saved (duckdb): {parquet_path}")

def write_sample_csv(out_csv: str, sample_path: str, n_rows: int) -> None:
    try:
        import duckdb
        con = duckdb.connect()
        con.execute(f"""
        COPY (
          SELECT *
          FROM read_csv_auto('{out_csv}', SAMPLE_SIZE=-1)
          LIMIT {int(n_rows)}
        ) TO '{sample_path.replace("'", "''")}' (HEADER, DELIMITER ',');
        """)
        print(f"Sample CSV written: {sample_path}")
    except Exception as e:
        # Pandas streaming fallback
        import pandas as pd  # type: ignore
        import itertools
        chunksize = min(max(10_000, n_rows), 250_000)
        it = pd.read_csv(out_csv, chunksize=chunksize)
        out = pd.concat(list(itertools.islice(it, max(1, n_rows // chunksize + (1 if n_rows % chunksize else 0)))))
        out.iloc[:n_rows].to_csv(sample_path, index=False)
        print(f"Sample CSV written (pandas fallback): {sample_path}")

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Clean the M5 Forecasting dataset into a tidy long table.")
    ap.add_argument("--m5-zip", dest="m5_zip", help="Path to m5-forecasting-accuracy.zip")
    ap.add_argument("--sales-csv", dest="sales_csv", help="Path to sales_train_validation.csv")
    ap.add_argument("--calendar-csv", dest="calendar_csv", help="Path to calendar.csv")
    ap.add_argument("--prices-csv", dest="prices_csv", help="Path to sell_prices.csv")
    ap.add_argument("--out-dir", dest="out_dir", required=True, help="Directory to write outputs")

    # New post-processing flags
    ap.add_argument("--to-parquet", action="store_true", help="Also write a Parquet version of the cleaned CSV")
    ap.add_argument("--parquet-path", default=None, help="Path for Parquet output (file or directory if partitioned)")
    ap.add_argument("--partition-by", default="", help="Comma-separated columns for partitioned Parquet (e.g. state_id,store_id)")
    ap.add_argument("--sample-csv", type=int, default=0, help="Write a sample CSV with the first N rows")
    
    # DuckDB export flags
    ap.add_argument("--to-duckdb", action="store_true",
                    help="Also write a DuckDB database with the cleaned table preloaded")
    ap.add_argument("--duckdb-path", default=None,
                    help="Path to the .duckdb database file (default: <out_dir>/m5.duckdb)")
    ap.add_argument("--duckdb-table", default="m5_clean_long",
                    help="Table name to create/replace in DuckDB (default: m5_clean_long)")
    
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    sales_wide, calendar, prices = load_m5(
        m5_zip=args.m5_zip,
        sales_csv=args.sales_csv,
        calendar_csv=args.calendar_csv,
        prices_csv=args.prices_csv,
    )

    stats = CleanStats(initial_rows_sales=len(sales_wide))
    notes = io.StringIO()
    print(f"Loaded sales shape: {sales_wide.shape}", file=notes)
    print(f"Loaded calendar shape: {calendar.shape}", file=notes)
    print(f"Loaded prices shape: {prices.shape}", file=notes)

    long_df = sales_wide_to_long(sales_wide)
    merged = join_calendar_prices(long_df, calendar, prices)

    before = len(merged)
    subset = [c for c in ["store_id", "item_id", "date"] if c in merged.columns]
    if subset:
        merged = merged.drop_duplicates(subset=subset + ["d"], keep="last")
    stats.duplicates_removed = before - len(merged)

    merged, issues = reasonableness_checks(merged)
    stats.qty_out_of_bounds = issues.get("qty_out_of_bounds", 0)
    stats.price_out_of_bounds = issues.get("price_out_of_bounds", 0)

    prefer = [
        "state_id","store_id","dept_id","cat_id","item_id",
        "id","d","date","wm_yr_wk","weekday","month","year",
        "event_name_1","event_type_1","event_name_2","event_type_2",
        "snap_CA","snap_TX","snap_WI",
        "sold_qty","sell_price","revenue",
    ]
    cols = [c for c in prefer if c in merged.columns] + [c for c in merged.columns if c not in prefer]
    merged = merged[cols]

    nulls = {c: int(merged[c].isna().sum()) for c in merged.columns}
    stats.final_rows_long = len(merged)

    out_csv = os.path.join(args.out_dir, "m5_clean_long.csv")
    out_report = os.path.join(args.out_dir, "dq_report.md")

    merged.to_csv(out_csv, index=False)
    report_text = build_report(stats, nulls, notes.getvalue())
    with open(out_report, "w", encoding="utf-8") as f:
        f.write(report_text)

    print("Cleaning complete.")
    print(f"Wide sales rows: {stats.initial_rows_sales}")
    print(f"Final long rows: {stats.final_rows_long}")
    print(f"Duplicates removed: {stats.duplicates_removed}")
    print(f"Report: {out_report}")
    print(f"Clean CSV: {out_csv}")

    # ---- Post-processing ----
    # Parquet export
    if args.to_parquet:
        parquet_path = args.parquet_path
        if not parquet_path:
            # default: single-file parquet next to CSV; if partitioning, write to a folder
            parquet_path = os.path.join(args.out_dir, "m5_clean_long.parquet") if not args.partition_by \
                           else os.path.join(args.out_dir, "m5_parquet")
        partition_cols = [c.strip() for c in args.partition_by.split(",") if c.strip()]
        write_parquet_with_fallback(out_csv, parquet_path, partition_cols if partition_cols else None)

    # Sample CSV
    if args.sample_csv and args.sample_csv > 0:
        sample_path = os.path.join(args.out_dir, f"sample_{args.sample_csv}.csv")
        write_sample_csv(out_csv, sample_path, args.sample_csv)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
