# src/tools.py
from pathlib import Path
import pandas as pd
from .forecast import compute_reorder_plan

def tool_load_inventory(data_processed: Path) -> str:
    fp = data_processed / "inventory_clean.csv"
    if not fp.exists():
        return "No processed inventory found. Please upload/clean data first."
    df = pd.read_csv(fp)
    summary = {
        "unique_sku": int(df["sku"].nunique()),
        "total_on_hand": int(df.get("on_hand", pd.Series(dtype=float)).sum()),
        "avg_daily_sales_mean": float(round(df.get("avg_daily_sales", pd.Series(dtype=float)).mean() or 0.0, 3)),
    }
    return f"Inventory summary: {summary}"

def tool_lookup_sku(sku: str, data_processed: Path) -> str:
    fp = data_processed / "inventory_clean.csv"
    if not fp.exists():
        return "No processed inventory found. Please upload/clean data first."
    df = pd.read_csv(fp)
    row = df.loc[df["sku"].astype(str).str.lower() == str(sku).lower()]
    if row.empty:
        row = df[df["sku"].astype(str).str.contains(str(sku), case=False, na=False)].head(1)
    if row.empty:
        return f"SKU {sku}: not found in processed inventory."
    r = row.iloc[0]
    on_hand = int(r.get("on_hand", 0))
    backroom = int(r.get("backroom_units", 0))
    shelf = int(r.get("shelf_units", 0))
    lead = float(r.get("lead_time_days", 0))
    ads  = float(r.get("avg_daily_sales", 0))
    parts = [f"SKU {r['sku']}: on_hand={on_hand}", f"shelf={shelf}", f"backroom={backroom}"]
    if ads > 0:
        parts.append(f"days_cover≈{round(on_hand / ads, 2)}")
    if lead:
        parts.append(f"lead_time_days={lead}")
    return ", ".join(parts)

def tool_reorder_plan(top_n: int, data_processed: Path) -> str:
    fp = data_processed / "inventory_clean.csv"
    if not fp.exists():
        return "No processed inventory found. Please upload/clean data first."
    df = pd.read_csv(fp)
    plan = compute_reorder_plan(df).sort_values("reorder_qty", ascending=False).head(top_n)
    return plan.to_csv(index=False)
