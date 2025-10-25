# src/cleaning.py
from __future__ import annotations
from typing import Dict, Iterable, Optional, Tuple
import re
import pandas as pd
import numpy as np
from pathlib import Path
from .utils import logger

# -------------------------------
# Canonical schema (required)
# -------------------------------
REQUIRED_COLS = [
    "sku",
    "product_name",
    "on_hand",
    "backroom_units",
    "shelf_units",
    "avg_daily_sales",
    "lead_time_days",
]

NUMERIC_COLS = ["on_hand", "backroom_units", "shelf_units", "avg_daily_sales", "lead_time_days"]

# ------------------------------------
# Header aliasing (liberal acceptance)
# ------------------------------------
# Existing rename hints you already had (we'll merge these into SYNONYMS below)
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

# Canonical -> common variants (case/spacing doesn’t matter; we normalize)
SYNONYMS_BASE = {
    "sku": {
        "sku", "item", "item id", "item_id", "item number", "item_number",
        "product_sku", "product id", "product_id", "upc", "gtin"
    },
    "product_name": {
        "product_name", "product", "description", "item_name", "name", "title"
    },
    "on_hand": {
        "on hand", "on_hand", "onhand", "oh", "store_on_hand", "current on hand",
        "qty on hand", "on hand qty", "on_hand_qty", "qty_on_hand"
    },
    "backroom_units": {
        "backroom_units", "backroom", "back room", "boh", "backstock", "stockroom", "backroom_qty"
    },
    "shelf_units": {
        "shelf_units", "shelf", "front", "frontstock", "on_shelf", "shelf_qty"
    },
    "avg_daily_sales": {
        "avg daily sales", "ads", "average daily sales", "daily_avg", "avg_demand",
        "avg dly sales", "avg_sales_per_day"
    },
    "lead_time_days": {
        "lead time", "lead_time", "leadtime", "lt_days", "lead time (days)", "leadtime_days"
    },
}

def _normalize(text: str) -> str:
    """
    Normalize a header/alias:
    - lowercase
    - trim
    - collapse whitespace/_/- to single space
    - strip trailing parentheticals "(qty)" etc.
    """
    base = re.sub(r"[\s\-_]+", " ", str(text).strip().lower())
    base = re.sub(r"\s*\([^)]*\)$", "", base).strip()
    return base

def _build_alias_to_canonical() -> Dict[str, str]:
    """
    Build alias -> canonical map from SYNONYMS_BASE and RENAME_MAP.
    """
    alias_to_canon: Dict[str, str] = {}
    # 1) from base synonyms
    for canon, aliases in SYNONYMS_BASE.items():
        for alias in (set(aliases) | {canon}):
            alias_to_canon[_normalize(alias)] = canon
    # 2) fold in your RENAME_MAP pairs
    for alias, canon in RENAME_MAP.items():
        alias_to_canon[_normalize(alias)] = canon
    return alias_to_canon

_ALIAS_TO_CANON = _build_alias_to_canonical()

def _auto_map_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Rename columns to canonical names using liberal aliasing.
    - Prefers existing canonical names as-is.
    - If multiple aliases map to the same canonical, keeps the first encountered.
    Returns (df_renamed, rename_log) where rename_log is {original -> canonical}.
    """
    if df is None or df.empty:
        return df, {}

    original_cols = list(df.columns)
    norm_to_original: Dict[str, str] = {}
    for col in original_cols:
        norm = _normalize(col)
        # keep first occurrence of a normalized name
        norm_to_original.setdefault(norm, col)

    # Determine which originals become which canonicals
    canonical_to_original: Dict[str, str] = {}
    for norm, original in norm_to_original.items():
        # if header is already canonical (normalized) and matches a canonical name, keep it
        if norm in _ALIAS_TO_CANON:
            canon = _ALIAS_TO_CANON[norm]
            # If a canonical header already exists in df (exact string), prefer that exact column
            if canon in df.columns and canon not in canonical_to_original:
                canonical_to_original[canon] = canon
            else:
                canonical_to_original.setdefault(canon, original)

    # Build rename map: original -> canonical (skip identity)
    rename_map: Dict[str, str] = {}
    for canon, original in canonical_to_original.items():
        if original != canon:
            # Avoid renaming if canon already exists and it's not the same physical column
            if canon in df.columns and original != canon:
                # both exist; keep the true canonical, ignore the alias
                continue
            rename_map[original] = canon

    df2 = df.rename(columns=rename_map)

    if rename_map:
        logger.info(f"Renamed columns → {rename_map}")

    return df2, rename_map

def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply robust header normalization + alias mapping, then verify all REQUIRED_COLS exist.
    Raises a detailed ValueError if any are missing.
    """
    # First, lowercase/strip for safety (no destructive renames here)
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Auto-map to canonical names
    df, rename_log = _auto_map_columns(df)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        # Helpful diagnostics: what we saw (normalized) and what we mapped
        normalized_seen = [_normalize(c) for c in df.columns]
        msg = (
            "Missing required columns: "
            f"{missing}\n"
            f"Headers present (post-mapping): {list(df.columns)}\n"
            f"Normalized seen: {normalized_seen}\n"
            f"Auto-mapped: {rename_log or '{}'}\n"
            "Tip: Adjust your CSV headers or extend the alias sets in SYNONYMS_BASE/RENAME_MAP."
        )
        raise ValueError(msg)

    return df

# (Kept for compatibility with your earlier design, now a thin wrapper.)
def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return _ensure_required_columns(df)

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
    1) Standardize/rename headers to the canonical schema (robust alias mapping).
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
    """
    # 1) Normalize headers with robust auto-mapping
    df = _standardize_columns(df)

    # Secondary guard (shouldn’t trigger unless the file is truly missing fields)
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
