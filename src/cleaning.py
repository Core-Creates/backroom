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
    order_columns: bool = True,
) -> pd.DataFrame:
    """
    Clean/normalize the inventory dataframe.

    Steps performed
    ---------------
    1) Standardize/rename headers to the canonical schema.
    2) Coerce numeric fields (invalid → 0).
    3) Preserve SKU formatting (string; leading zeros intact).
    4) Trim product_name.
    5) Add derived fields:
        - days_of_cover = on_hand / avg_daily_sales (0 when avg_daily_sales == 0)
        - restock_needed = (shelf_units < shelf_low_threshold) & (backroom_units > 0)
          (stored as Python bool scalars to satisfy identity checks)
    6) Optionally add 'safety_stock' column with a default value.
    7) Clip negatives to 0.
    8) (Optional) Enforce output column ordering.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe; header variants will be normalized.
    shelf_low_threshold : int, default 3
        Shelf units below this are considered low.
    add_safety_stock_if_missing : bool, default True
        If True, add 'safety_stock' if it's missing.
    default_safety_stock : float, default 2.0
        Value used when adding safety_stock.
    order_columns : bool, default True
        If True, return columns ordered as:
        REQUIRED_COLS + [derived columns present] + [other columns (sorted)]

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with canonical and derived fields.

    Examples
    --------
    >>> raw = pd.DataFrame({
    ...     "sku": ["00123", "ABC-9"],
    ...     "product_name": [" Widget A ", "Gadget B"],
    ...     "onhand": [10, 0],
    ...     "backroom": [5, 2],
    ...     "shelf": [1, 4],
    ...     "avg_dly_sales": [2.0, 1.0],
    ...     "lead_time": [3, 7],
    ... })
    >>> out = clean_inventory_df(raw, shelf_low_threshold=3)
    >>> set(REQUIRED_COLS).issubset(out.columns)
    True
    >>> float(out.loc[0, "days_of_cover"]) == 5.0
    True
    >>> out.loc[0, "restock_needed"] is True
    True
    """
    # 1) Normalize headers
    df = _standardize_columns(df)

    ok, missing = _validate_columns(df, REQUIRED_COLS)
    if not ok:
        raise ValueError(f"Missing required columns: {missing}")

    # Work on a copy
    df = df.copy()

    # 2) String cleanup (preserve SKU formatting)
    df["sku"] = df["sku"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()

    # 3) Numeric coercion (invalid → 0)
    before_nulls = {c: int(pd.to_numeric(df[c], errors="coerce").isna().sum()) for c in NUMERIC_COLS if c in df}
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 4) Derived: days_of_cover
    avg = df["avg_daily_sales"].to_numpy()
    onh = df["on_hand"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        days = np.where(avg > 0, onh / avg, 0.0)
    df["days_of_cover"] = np.maximum(days, 0)

    # 5) Derived: restock_needed (return Python bool scalars, not numpy.bool_)
    mask = (df["shelf_units"] < shelf_low_threshold) & (df["backroom_units"] > 0)
    df["restock_needed"] = pd.Series([bool(v) for v in mask.tolist()], index=df.index, dtype="object")

    # 6) safety_stock default
    if add_safety_stock_if_missing and "safety_stock" not in df.columns:
        df["safety_stock"] = float(default_safety_stock)

    # 7) Clip negatives
    for c in NUMERIC_COLS + ["days_of_cover"]:
        df[c] = df[c].clip(lower=0)

    # Logging: summary & basic stats
    low_shelf = int((df["shelf_units"] < shelf_low_threshold).sum())
    zero_avg_sales = int((df["avg_daily_sales"] <= 0).sum())
    logger.info(
        "Cleaned inventory: rows=%d | low_shelf<%d=%d | zero_avg_sales=%d | coerced_nulls=%s",
        len(df), shelf_low_threshold, low_shelf, zero_avg_sales, before_nulls
    )
    logger.debug(
        "Ranges: on_hand=[%.2f, %.2f], avg_daily_sales=[%.2f, %.2f], days_of_cover=[%.2f, %.2f]",
        float(df["on_hand"].min()), float(df["on_hand"].max()),
        float(df["avg_daily_sales"].min()), float(df["avg_daily_sales"].max()),
        float(df["days_of_cover"].min()), float(df["days_of_cover"].max()),
    )

    # 8) Column ordering (canonical → derived → others)
    if order_columns:
        derived_in_df = [c for c in ["days_of_cover", "restock_needed", "safety_stock"] if c in df.columns]
        canonical_block = [c for c in REQUIRED_COLS if c in df.columns]
        other_cols = sorted([c for c in df.columns if c not in set(canonical_block + derived_in_df)])
        ordered = canonical_block + derived_in_df + other_cols
        df = df.loc[:, ordered]

    return df


def save_cleaned_inventory(df: pd.DataFrame, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Use utf-8-sig for Excel friendliness on Windows
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"Wrote cleaned inventory → {out_path}")
    return out_path
