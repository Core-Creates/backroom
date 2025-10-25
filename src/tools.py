# src/tools.py
from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd

from .forecast import compute_reorder_plan
from .detect import detect_shelf_gaps  # <-- needed for tool_detect_gap

__all__ = [
    "tool_load_inventory",
    "tool_lookup_sku",
    "tool_reorder_plan",
    "tool_detect_gap",
]

# ---------- internal helpers ----------

def _csv_path(data_processed: Path) -> Path:
    return data_processed / "inventory_clean.csv"

def _load_df(data_processed: Path) -> Optional[pd.DataFrame]:
    fp = _csv_path(data_processed)
    if not fp.exists():
        return None
    try:
        return pd.read_csv(fp)
    except Exception:
        return None

# ---------- tools ----------

def tool_load_inventory(data_processed: Path) -> str:
    """
    Summarize the current processed inventory dataset.
    """
    df = _load_df(data_processed)
    if df is None:
        return "No processed inventory found. Please upload/clean data first."

    # Column safety
    if "sku" not in df.columns:
        return "Inventory summary unavailable: missing 'sku' column."
    on_hand_series = df.get("on_hand", pd.Series(dtype=float))
    ads_series = df.get("avg_daily_sales", pd.Series(dtype=float))

    summary = {
        "unique_sku": int(df["sku"].nunique()),
        "total_on_hand": int(on_hand_series.sum()),
        "avg_daily_sales_mean": float(round(ads_series.mean() or 0.0, 3)),
    }
    return f"Inventory summary: {summary}"

def tool_lookup_sku(sku: str, data_processed: Path) -> str:
    """
    Return a terse availability line for a given SKU from processed data.
    """
    df = _load_df(data_processed)
    if df is None:
        return "No processed inventory found. Please upload/clean data first."

    if "sku" not in df.columns:
        return "SKU lookup unavailable: missing 'sku' column."

    # Exact match first
    row = df.loc[df["sku"].astype(str).str.lower() == str(sku).lower()]
    if row.empty:
        # Fallback: contains match
        row = df[df["sku"].astype(str).str.contains(str(sku), case=False, na=False)].head(1)
    if row.empty:
        return f"SKU {sku}: not found in processed inventory."

    r = row.iloc[0]
    on_hand = int(r.get("on_hand", 0))
    backroom = int(r.get("backroom_units", 0))
    shelf = int(r.get("shelf_units", 0))
    lead = float(r.get("lead_time_days", 0))
    ads = float(r.get("avg_daily_sales", 0))
    days_cover = round(on_hand / ads, 2) if ads > 0 else None

    parts = [f"SKU {r['sku']}: on_hand={on_hand}", f"shelf={shelf}", f"backroom={backroom}"]
    if days_cover is not None:
        parts.append(f"days_cover≈{days_cover}")
    if lead:
        parts.append(f"lead_time_days={lead}")
    return ", ".join(parts)

def tool_reorder_plan(top_n: int, data_processed: Path) -> str:
    """
    Compute reorder plan and return top N rows as CSV snippet.
    """
    df = _load_df(data_processed)
    if df is None:
        return "No processed inventory found. Please upload/clean data first."

    try:
        plan = compute_reorder_plan(df)
    except Exception as e:
        return f"Failed to compute reorder plan: {e}"

    if "reorder_qty" not in plan.columns:
        return "Reorder plan missing 'reorder_qty' column."
    plan = plan.sort_values("reorder_qty", ascending=False).head(top_n)
    return plan.to_csv(index=False)

def tool_detect_gap(image_path: str) -> str:
    """
    Run simple shelf-gap heuristic on an uploaded image path.
    """
    p = Path(image_path)
    if not p.exists():
        return f"Image not found: {image_path}"
    try:
        res = detect_shelf_gaps(p)
    except Exception as e:
        return f"Gap detection failed: {e}"
    return f"gap_score={res.get('gap_score')}, notes={res.get('notes')}"


# ---------- end of file ----------
