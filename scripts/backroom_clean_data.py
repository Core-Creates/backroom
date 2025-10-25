#!/usr/bin/env python3
"""
Backroom Data Cleaning Script — M5 (Printable, Single-File)
-----------------------------------------------------------
Purpose:
  Tailored cleaner for the M5 Forecasting - Accuracy dataset. Converts the wide daily
  sales matrices (d_1..d_N) into a tidy long table, joins calendar and prices, parses dates,
  checks ranges, and emits:

  1) m5_clean_long.csv — row per (store_id, item_id, date)
  2) dq_report.md — human-readable data quality report

Inputs Supported (any combo):
  • --m5-zip path/to/m5-forecasting-accuracy.zip  (official Kaggle bundle)
  • OR explicit CSVs: --sales-csv, --calendar-csv, --prices-csv
"""

from __future__ import annotations
import argparse
import io
import os
import re
import sys
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd

# --------------------------
# CONFIG (tuned for M5)
# --------------------------
PRICE_MIN, PRICE_MAX = 0.0, 1_000_000.0
QTY_MIN, QTY_MAX = 0, 1_000_000
MISSING_SENTINELS = {"n/a", "na", "null", "none", "nan", "", "-", "?"}

# Columns present in M5
ID_COLS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
CAL_KEEP = [
    "d", "date", "wm_yr_wk", "weekday", "wday", "month", "year",
    "event_name_1", "event_type_1", "event_name_2", "event_type_2",
    "snap_CA", "snap_TX", "snap_WI",
]
PRICES_KEEP = ["store_id", "item_id", "wm_yr_wk", "sell_price"]

D_COL_PREFIX = "d_"

# --------------------------
# Helpers
# --------------------------
def _read_csv_any(path_or_buf, **kw) -> pd.DataFrame:
    return pd.read_csv(
        path_or_buf,
        dtype=str,
        keep_default_na=False,
        na_values=list(MISSING_SENTINELS),
        **kw,
    )

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"[^A-Za-z0-9]+", "_", c.strip().lower()).strip("_") for c in df.columns]
    return df

def _strip(text: Any) -> Any:
    if pd.isna(text) or not isinstance(text, str):
        return text
    t = re.sub(r"[\u0000-\u001F\u007F]", "", text)
    return re.sub(r"\s+", " ", t).strip()

def _to_float(x: Any) -> Optional[float]:
    if pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS:
        return pd.NA
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return pd.NA

def _to_int(x: Any) -> Optional[int]:
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

# --------------------------
# Core M5 cleaning
# --------------------------
def load_m5(
    m5_zip: Optional[str] = None,
    sales_csv: Optional[str] = None,
    calendar_csv: Optional[str] = None,
    prices_csv: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (sales_wide, calendar, prices) as dataframes."""
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
    # Identify day columns d_1..d_N
    day_cols = [c for c in sales_wide.columns if c.startswith(D_COL_PREFIX)]
    id_cols = [c for c in ID_COLS if c in sales_wide.columns]

    long_df = sales_wide.melt(
        id_vars=id_cols, value_vars=day_cols,
        var_name="d", value_name="sold_qty"
    )

    # Coerce types & clean strings
    for c in id_cols + ["d"]:
        long_df[c] = long_df[c].map(_strip).astype("string")
    long_df["sold_qty"] = long_df["sold_qty"].map(_to_int).astype("Int64")

    return long_df

def join_calendar_prices(long_df: pd.DataFrame, calendar: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    # Keep essential columns and coerce
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

    # Ensure calendar has 'd'
    if "d" not in calendar.columns:
        cal_map = calendar.reset_index().rename(columns={"index": "d_index"})
        cal_map["d"] = cal_map["d_index"].add(1).map(lambda x: f"d_{x}").astype("string")
        cal_map.drop(columns=["d_index"], inplace=True)
    else:
        cal_map = calendar

    # Join long_df with calendar on 'd'
    out = long_df.merge(cal_map, on="d", how="left", validate="m:1")

    # Join prices on (store_id, item_id, wm_yr_wk)
    price_keys = [k for k in ["store_id", "item_id", "wm_yr_wk"] if k in out.columns and k in prices.columns]
    if len(price_keys) == 3:
        out = out.merge(prices, on=price_keys, how="left", validate="m:1")

    return out

def reasonableness_checks(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    issues = {"qty_out_of_bounds": 0, "price_out_of_bounds": 0}

    if "sold_qty" in df.columns:
        bad = ~df["sold_qty"].isna() & ((df["sold_qty"] < QTY_MIN) | (df["sold_qty"] > QTY_MAX))
        issues["qty_out_of_bounds"] = int(bad.sum())
        df.loc[bad, "sold_qty"] = pd.NA

    if "sell_price" in df.columns:
        badp = ~df["sell_price"].isna() & ((df["sell_price"] < PRICE_MIN) | (df["sell_price"] > PRICE_MAX))
        issues["price_out_of_bounds"] = int(badp.sum())
        df.loc[badp, "sell_price"] = pd.NA

    # Revenue
    if {"sold_qty", "sell_price"}.issubset(df.columns):
        df["revenue"] = (
            df["sold_qty"].astype("Float64") * df["sell_price"].astype("Float64")
        ).astype("Float64")

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

# --------------------------
# CLI
# --------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Clean the M5 Forecasting dataset into a tidy long table.")
    ap.add_argument("--m5-zip", dest="m5_zip", help="Path to m5-forecasting-accuracy.zip")
    ap.add_argument("--sales-csv", dest="sales_csv", help="Path to sales_train_validation.csv")
    ap.add_argument("--calendar-csv", dest="calendar_csv", help="Path to calendar.csv")
    ap.add_argument("--prices-csv", dest="prices_csv", help="Path to sell_prices.csv")
    ap.add_argument("--out-dir", dest="out_dir", required=True, help="Directory to write outputs")

    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    # Load raw files
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

    # Wide -> Long
    long_df = sales_wide_to_long(sales_wide)

    # Join calendar & prices
    merged = join_calendar_prices(long_df, calendar, prices)

    # Drop obvious dups on (store_id, item_id, date) if present
    before = len(merged)
    subset = [c for c in ["store_id", "item_id", "date"] if c in merged.columns]
    if subset:
        merged = merged.drop_duplicates(subset=subset + ["d"], keep="last")
    stats.duplicates_removed = before - len(merged)

    # Reasonableness + revenue
    merged, issues = reasonableness_checks(merged)
    stats.qty_out_of_bounds = issues.get("qty_out_of_bounds", 0)
    stats.price_out_of_bounds = issues.get("price_out_of_bounds", 0)

    # Final typing and column order
    prefer = [
        "state_id", "store_id", "dept_id", "cat_id", "item_id",
        "id", "d", "date", "wm_yr_wk", "weekday", "month", "year",
        "event_name_1", "event_type_1", "event_name_2", "event_type_2",
        "snap_CA", "snap_TX", "snap_WI",
        "sold_qty", "sell_price", "revenue",
    ]
    cols = [c for c in prefer if c in merged.columns] + [c for c in merged.columns if c not in prefer]
    merged = merged[cols]

    # Null counts
    nulls = {c: int(merged[c].isna().sum()) for c in merged.columns}
    stats.final_rows_long = len(merged)

    # Outputs
    out_csv = os.path.join(args.out_dir, "m5_clean_long.csv")
    out_report = os.path.join(args.out_dir, "dq_report.md")

    merged.to_csv(out_csv, index=False)
    report_text = build_report(stats, nulls, notes.getvalue())
    with open(out_report, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Console summary
    print("Cleaning complete.\n")
    print(f"Wide sales rows: {stats.initial_rows_sales}")
    print(f"Final long rows: {stats.final_rows_long}")
    print(f"Duplicates removed: {stats.duplicates_removed}")
    print(f"Report: {out_report}")
    print(f"Clean CSV: {out_csv}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
