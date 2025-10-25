import pandas as pd
import numpy as np

def compute_reorder_plan(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # safety_stock assumed per-row; default 2 if absent
    if "safety_stock" not in out.columns:
        out["safety_stock"] = 2.0

    # days_of_cover is precomputed in cleaning; recompute if missing
    if "days_of_cover" not in out.columns:
        out["days_of_cover"] = (out["on_hand"].replace(0, 0.0001)) / (out["avg_daily_sales"].replace(0, 0.0001))

    reorder_threshold = out["lead_time_days"] + out["safety_stock"]
    deficit_days = (reorder_threshold - out["days_of_cover"]).clip(lower=0)
    out["reorder_qty"] = np.ceil(deficit_days * out["avg_daily_sales"]).astype(int)
    out["reorder_flag"] = out["reorder_qty"] > 0

    cols = ["sku","product_name","on_hand","backroom_units","shelf_units","avg_daily_sales","lead_time_days","safety_stock","days_of_cover","reorder_qty","reorder_flag"]
    return out[cols]
