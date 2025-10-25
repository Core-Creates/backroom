from __future__ import annotations
import pandas as pd
from pathlib import Path
from .utils import logger

REQUIRED_COLS = ["sku","product_name","on_hand","backroom_units","shelf_units","avg_daily_sales","lead_time_days"]

def clean_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    # Standardize columns
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    # Rename common variants
    rename_map = {
        "onhand": "on_hand",
        "avg_dly_sales": "avg_daily_sales",
        "lead_time": "lead_time_days",
        "backroom": "backroom_units",
        "shelf": "shelf_units",
    }
    df = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})

    # Ensure required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Types & cleaning
    num_cols = ["on_hand","backroom_units","shelf_units","avg_daily_sales","lead_time_days"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Strip text
    df["sku"] = df["sku"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()

    # Derived fields
    df["days_of_cover"] = (df["on_hand"].replace(0, 0.0001)) / (df["avg_daily_sales"].replace(0, 0.0001))
    df["restock_needed"] = (df["shelf_units"] < 3) & (df["backroom_units"] > 0)

    # Basic sanity limits
    for c in num_cols + ["days_of_cover"]:
        df[c] = df[c].clip(lower=0)

    return df

def save_cleaned_inventory(df: pd.DataFrame, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info(f"Wrote cleaned inventory → {out_path}")
    return out_path
