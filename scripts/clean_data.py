#!/usr/bin/env python3
"""
Backroom Data Cleaning Script (Printable, Single-File)
-----------------------------------------------------
Purpose:
  Clean and standardize backroom inventory/export CSVs (SKUs, product names, quantities,
  prices, locations, dates), and emit a cleaned CSV plus a human-readable data quality report.

Usage:
  python backroom_clean.py --in raw_inventory.csv --out cleaned_inventory.csv \
      --report dq_report.md --primary-columns sku,location_id --date-columns received_at,expires_at

Notes:
  - Only uses pandas (pip install pandas python-dateutil).
  - Safe defaults; customize the CONFIG section as needed.
  - The script is intentionally verbose and well-commented for easy printing and SOP inclusion.
"""

from __future__ import annotations
import argparse
import io
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd
from dateutil import parser as dateparser

# --------------------------
# CONFIG: edit to your needs
# --------------------------
DEFAULT_PRIMARY_COLUMNS = ["sku", "location_id"]  # used for de-duplication and key checks
DEFAULT_DATE_COLUMNS = ["received_at", "expires_at", "last_counted_at"]
DEFAULT_INT_COLUMNS = ["qty_on_hand", "reorder_point"]
DEFAULT_FLOAT_COLUMNS = ["unit_cost", "unit_price"]
DEFAULT_STR_COLUMNS = ["sku", "product_name", "uom", "location_id", "bin", "category"]

# SKU normalization: keep alnum, convert to upper, remove spaces/dashes/underscores
SKU_NORMALIZE_REGEX = re.compile(r"[^A-Za-z0-9]")

# Acceptable UOM remaps (example)
UOM_NORMALIZATION = {
    "ea": "EA",
    "each": "EA",
    "pcs": "EA",
    "piece": "EA",
    "kg": "KG",
    "g": "G",
    "lb": "LB",
    "lbs": "LB",
    "oz": "OZ",
}

# Missing value sentinels commonly seen in exports
MISSING_SENTINELS = {"n/a", "na", "null", "none", "nan", "", "-", "?"}

# Hard bounds to flag unlikely values (adjust to your site)
QTY_MIN, QTY_MAX = 0, 1_000_000
PRICE_MIN, PRICE_MAX = 0.0, 1_000_000.0

# -----------------------------------
# Utility helpers
# -----------------------------------

def normalize_column_names(cols: List[str]) -> List[str]:
    out = []
    for c in cols:
        c2 = re.sub(r"[^A-Za-z0-9]+", "_", c.strip().lower()).strip("_")
        out.append(c2)
    return out


def strip_bad_unicode(text: Any) -> Any:
    if pd.isna(text):
        return text
    if not isinstance(text, str):
        return text
    # Remove control chars and normalize whitespace
    cleaned = re.sub(r"[\u0000-\u001F\u007F]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_sku(s: Any) -> Any:
    if pd.isna(s):
        return s
    s = str(s).strip()
    s = s.upper()
    s = SKU_NORMALIZE_REGEX.sub("", s)  # drop non-alnum
    return s


def normalize_uom(u: Any) -> Any:
    if pd.isna(u):
        return u
    k = str(u).strip().lower()
    return UOM_NORMALIZATION.get(k, str(u).strip().upper())


def coerce_int(x: Any) -> Optional[int]:
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NA
    try:
        # allow floats-as-strings like "12.0"
        return int(float(str(x).replace(",", "")))
    except Exception:
        return pd.NA


def coerce_float(x: Any) -> Optional[float]:
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NA
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return pd.NA


def parse_date(x: Any) -> Optional[pd.Timestamp]:
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NaT
    try:
        return pd.to_datetime(dateparser.parse(str(x), dayfirst=False, yearfirst=False))
    except Exception:
        return pd.NaT


@dataclass
class CleanStats:
    initial_rows: int = 0
    final_rows: int = 0
    duplicates_dropped: int = 0
    rows_with_missing_keys: int = 0
    out_of_bounds_qty: int = 0
    out_of_bounds_price: int = 0
    nulls_by_col: Dict[str, int] = field(default_factory=dict)


# -----------------------------------
# Core cleaning routine
# -----------------------------------

def clean_df(
    df: pd.DataFrame,
    primary_cols: List[str],
    date_cols: List[str],
    int_cols: List[str],
    float_cols: List[str],
    str_cols: List[str],
) -> tuple[pd.DataFrame, CleanStats, str]:
    stats = CleanStats(initial_rows=len(df))
    notes = io.StringIO()

    # 1) Standardize columns
    df = df.copy()
    df.columns = normalize_column_names(list(df.columns))
    print(f"Columns normalized: {df.columns.tolist()}", file=notes)

    # 2) Trim strings / remove control chars
    for c in df.columns:
        df[c] = df[c].map(strip_bad_unicode)
    print("Applied unicode/control-char stripping and whitespace normalization to all columns.", file=notes)

    # 3) Type coercions
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype("string")
    for c in int_cols:
        if c in df.columns:
            df[c] = df[c].map(coerce_int).astype("Int64")
    for c in float_cols:
        if c in df.columns:
            df[c] = df[c].map(coerce_float).astype("Float64")
    for c in date_cols:
        if c in df.columns:
            df[c] = df[c].map(parse_date).astype("datetime64[ns]")

    # 4) Domain-specific normalizations
    if "sku" in df.columns:
        df["sku"] = df["sku"].map(normalize_sku)
    if "uom" in df.columns:
        df["uom"] = df["uom"].map(normalize_uom)

    # 5) Key presence and duplicates
    missing_key_mask = pd.Series(False, index=df.index)
    for c in primary_cols:
        if c in df.columns:
            missing_key_mask |= df[c].isna() | (df[c].astype(str).str.len() == 0)
        else:
            print(f"WARNING: primary column '{c}' not present in input.", file=notes)
    stats.rows_with_missing_keys = int(missing_key_mask.sum())
    df = df.loc[~missing_key_mask].copy()

    before = len(df)
    subset = [c for c in primary_cols if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    stats.duplicates_dropped = before - len(df)

    # 6) Reasonableness checks
    if "qty_on_hand" in df.columns:
        bad_qty = ~df["qty_on_hand"].isna() & ((df["qty_on_hand"] < QTY_MIN) | (df["qty_on_hand"] > QTY_MAX))
        stats.out_of_bounds_qty = int(bad_qty.sum())
        df.loc[bad_qty, "qty_on_hand"] = pd.NA
    price_col = None
    for cand in ("unit_cost", "unit_price", "price"):
        if cand in df.columns:
            price_col = cand
            break
    if price_col:
        bad_price = ~df[price_col].isna() & ((df[price_col] < PRICE_MIN) | (df[price_col] > PRICE_MAX))
        stats.out_of_bounds_price = int(bad_price.sum())
        df.loc[bad_price, price_col] = pd.NA

    # 7) Final null counts
    stats.nulls_by_col = {c: int(df[c].isna().sum()) for c in df.columns}

    stats.final_rows = len(df)

    # Build a human-readable summary block
    summary = io.StringIO()
    print("# Data Quality Summary\n", file=summary)
    print(f"- Initial rows: {stats.initial_rows}", file=summary)
    print(f"- Dropped due to missing primary keys: {stats.rows_with_missing_keys}", file=summary)
    print(f"- Duplicates removed: {stats.duplicates_dropped}", file=summary)
    print(f"- Final rows: {stats.final_rows}", file=summary)
    if stats.out_of_bounds_qty:
        print(f"- Qty out-of-bounds set to null: {stats.out_of_bounds_qty}", file=summary)
    if stats.out_of_bounds_price:
        print(f"- Price out-of-bounds set to null: {stats.out_of_bounds_price}", file=summary)

    print("\n## Nulls by Column", file=summary)
    for c, n in stats.nulls_by_col.items():
        print(f"- {c}: {n}", file=summary)

    print("\n## Processing Notes", file=summary)
    print(notes.getvalue(), file=summary)

    return df, stats, summary.getvalue()


# -----------------------------------
# CLI
# -----------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Clean backroom inventory CSV and emit report.")
    p.add_argument("--in", dest="in_path", required=True, help="Input CSV path")
    p.add_argument("--out", dest="out_path", required=True, help="Output cleaned CSV path")
    p.add_argument("--report", dest="report_path", default="dq_report.md", help="Output report (.md)")
    p.add_argument("--primary-columns", dest="primary_cols", default=",".join(DEFAULT_PRIMARY_COLUMNS),
                   help="Comma-separated primary key columns for de-duplication")
    p.add_argument("--date-columns", dest="date_cols", default=",".join(DEFAULT_DATE_COLUMNS),
                   help="Comma-separated date columns to parse")
    p.add_argument("--int-columns", dest="int_cols", default=",".join(DEFAULT_INT_COLUMNS),
                   help="Comma-separated integer columns to coerce")
    p.add_argument("--float-columns", dest="float_cols", default=",".join(DEFAULT_FLOAT_COLUMNS),
                   help="Comma-separated float/price columns to coerce")
    p.add_argument("--str-columns", dest="str_cols", default=",".join(DEFAULT_STR_COLUMNS),
                   help="Comma-separated string columns to standardize")

    args = p.parse_args(argv)

    # Read
    try:
        df = pd.read_csv(args.in_path, dtype=str, keep_default_na=False, na_values=list(MISSING_SENTINELS))
    except Exception as e:
        sys.stderr.write(f"Failed to read CSV: {e}\n")
        return 2

    # Clean
    df_clean, stats, report_md = clean_df(
        df,
        primary_cols=[c.strip() for c in args.primary_cols.split(",") if c.strip()],
        date_cols=[c.strip() for c in args.date_cols.split(",") if c.strip()],
        int_cols=[c.strip() for c in args.int_cols.split(",") if c.strip()],
        float_cols=[c.strip() for c in args.float_cols.split(",") if c.strip()],
        str_cols=[c.strip() for c in args.str_cols.split(",") if c.strip()],
    )

    # Write outputs
    try:
        df_clean.to_csv(args.out_path, index=False)
    except Exception as e:
        sys.stderr.write(f"Failed to write cleaned CSV: {e}\n")
        return 3

    try:
        with open(args.report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
    except Exception as e:
        sys.stderr.write(f"Failed to write report: {e}\n")
        return 4

    # Console summary for quick reference
    print("Cleaning complete.\n")
    print(f"Input rows: {stats.initial_rows}")
    print(f"Dropped (missing keys): {stats.rows_with_missing_keys}")
    print(f"Duplicates removed: {stats.duplicates_dropped}")
    print(f"Final rows: {stats.final_rows}")
    print(f"Report saved to: {args.report_path}")
    print(f"Cleaned CSV saved to: {args.out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
