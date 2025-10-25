# src/cleaning.py
from __future__ import annotations
from typing import Dict, Iterable, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
from .utils import logger

# Canonical schema
REQUIRED_COLS = [
    "sku",
    "product_name",
    "on_hand",
    "backroom_units",
    "shelf_units",
    "avg_daily_sales",
    "lead_time_days",
]

# Common header variants → canonical names
RENAME_MAP: Dict[str, str] = {
    "onhand": "on_hand",
    "on_hand_qty": "on_hand",
    "qty_on_hand": "on_hand",
    "avg_dly_sales": "avg_daily_sales",
    "avg_sales_per_day": "avg_daily_sales",
    "lead_time": "lead_time_days",
    "leadtime_days": "lead_time_days",
    "backroom": "backroom_units",
    "backroom_qty": "backroom_units",
    "shelf": "shelf_units",
    "shelf_qty": "shelf_units",
}

NUMERIC_COLS = ["on_hand", "backroom_units", "shelf_units", "avg_daily_sales", "lead_time_days"]

def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    # Apply known renames if present
    present = {k: v for k, v in RENAME_MAP.items() if k in df.columns and v not in df.columns}
    if present:
        df = df.rename(columns=present)
        logger.info(f"Renamed columns → {present}")
    return df

def _validate_columns(df: pd.DataFrame, required: Iterable[str]) -> Tuple[bool, list]:
    missing = [c for c in required if c not in df.columns]
    return (len(missing) == 0, missing)

def clean_inventory_df(
    df: pd.DataFrame,
    *,
    shelf_low_threshold: int = 3,
    add_safety_stock_if_missing: bool = True,
    default_safety_stock: float = 2.0,
) -> pd.DataFrame:
    """
    Clean/normalize the inventory dataframe.

    - Standardizes/renames headers.
    - Enforces numeric dtypes on key columns.
    - Preserves SKU formatting (string, keep leading zeros).
    - Adds derived fields:
        - days_of_cover = on_hand / avg_daily_sales (0 when avg_daily_sales==0)
        - restock_needed = (shelf_units < shelf_low_threshold) & (backroom_units > 0)
    - Optionally adds 'safety_stock' if missing.

    Parameters
    ----------
    shelf_low_threshold : int
        Shelf units below this are considered low.
    add_safety_stock_if_missing : bool
        If True and column is missing, add 'safety_stock' with default.
    default_safety_stock : float
        Value to use when adding safety_stock.
    """
    df = _standardize_columns(df)

    ok, missing = _validate_columns(df, REQUIRED_COLS)
    if not ok:
        raise ValueError(f"Missing required columns: {missing}")

    # Types & cleaning
    df = df.copy()

    # String cleanups
    df["sku"] = df["sku"].astype(str).str.strip()               # keep leading zeros
    df["product_name"] = df["product_name"].astype(str).str.strip()

    # Numeric conversions (coerce bad values to 0)
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Derived fields
    # days_of_cover = on_hand / avg_daily_sales (handle 0 safely)
    avg = df["avg_daily_sales"].to_numpy()
    onh = df["on_hand"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        days = np.where(avg > 0, onh / avg, 0.0)
    df["days_of_cover"] = np.maximum(days, 0)

    # Restock signal — produce Python bools (not numpy.bool_)    
    df["restock_needed"] = (
    ((df["shelf_units"] < shelf_low_threshold) & (df["backroom_units"] > 0))
    .astype(object)
    .map(bool)
)


    # Optional safety_stock default (used later in forecasting)
    if add_safety_stock_if_missing and "safety_stock" not in df.columns:
        df["safety_stock"] = float(default_safety_stock)

    # Basic sanity limits
    for c in NUMERIC_COLS + ["days_of_cover"]:
        df[c] = df[c].clip(lower=0)

    # Helpful logging
    low_shelf = int((df["shelf_units"] < shelf_low_threshold).sum())
    zero_sellers = int((df["avg_daily_sales"] <= 0).sum())
    logger.info(
        f"Cleaned inventory: rows={len(df)} | low_shelf<{shelf_low_threshold}={low_shelf} | zero_avg_sales={zero_sellers}"
    )

    return df

def save_cleaned_inventory(df: pd.DataFrame, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Use utf-8-sig for Excel friendliness on Windows
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"Wrote cleaned inventory → {out_path}")
    return out_path
