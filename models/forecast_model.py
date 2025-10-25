#!/usr/bin/env python3
import os
import sys
import math
import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

# ----------------------------
# Utilities
# ----------------------------
def info(msg):  print(f"[INFO] {msg}")
def warn(msg):  print(f"[WARN] {msg}")
def err(msg):   print(f"[ERR ] {msg}", file=sys.stderr)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path

def as_int_or_all(v):
    if isinstance(v, str) and v.lower() in ("all", "none"):
        return None
    return int(v)

# ----------------------------
# WRMSSE (bottom level) helper
# ----------------------------
def rmsse_denominator(series: pd.Series) -> float:
    s = series.dropna().astype(float).values
    if len(s) < 2:
        return np.nan
    diffs = np.diff(s)
    m = np.mean(diffs**2)
    return np.sqrt(m) if m > 0 else np.nan

def compute_wrmsse_bottom(pred_df: pd.DataFrame, full_df: pd.DataFrame, val_start_ts: pd.Timestamp) -> float:
    """
    pred_df: [item_id, store_id, date, y_true, y_pred]
    full_df: long DF with ['item_id','store_id','date','sales','sell_price']
    val_start_ts: first day of validation window
    Weights: avg revenue over validation window; normalized to sum=1
    """
    val_mask = (full_df["date"] >= val_start_ts)
    rev = (full_df.loc[val_mask, ["item_id","store_id","date","sales","sell_price"]]
           .assign(revenue=lambda x: x["sales"]*x["sell_price"])
           .groupby(["item_id","store_id"])["revenue"].mean())
    rev = rev.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if rev.sum() == 0:
        rev = rev * 0 + 1.0
    w = rev / rev.sum()

    pre_mask = (full_df["date"] < val_start_ts)
    denom = (full_df.loc[pre_mask, ["item_id","store_id","date","sales"]]
             .groupby(["item_id","store_id"])["sales"]
             .apply(rmsse_denominator))

    mse = pred_df.assign(se=lambda x: (x["y_pred"] - x["y_true"])**2) \
                 .groupby(["item_id","store_id"])["se"].mean()

    rmsse = (mse**0.5) / denom
    rmsse = rmsse.replace([np.inf, -np.inf], np.nan)

    rmsse = rmsse.reindex(w.index)
    wrmsse = np.nansum(w * rmsse)
    return float(wrmsse)

# ----------------------------
# Event dummies for future dates
# ----------------------------
def build_event_dummies_for_dates(dates: pd.Series, calendar_df: pd.DataFrame, template_cols: list) -> pd.DataFrame:
    cal = calendar_df.copy()
    cal["date"] = pd.to_datetime(cal["date"])
    cols = ["date","event_name_1","event_type_1","event_name_2","event_type_2","snap_CA","snap_TX","snap_WI"]
    for c in cols:
        if c not in cal.columns:
            cal[c] = np.nan
    base = pd.DataFrame({"date": dates})
    tmp = base.merge(cal[cols], on="date", how="left")

    for c in ["snap_CA","snap_TX","snap_WI"]:
        tmp[c] = (tmp[c].fillna(0)).astype(int)

    for c in ["event_name_1","event_type_1","event_name_2","event_type_2"]:
        if c not in tmp.columns:
            tmp[c] = "NONE"
        tmp[c] = tmp[c].astype("category")

    tmp = pd.get_dummies(
        tmp,
        columns=["event_name_1","event_type_1","event_name_2","event_type_2"],
        prefix=["event_name_1","event_type_1","event_name_2","event_type_2"],
        drop_first=True
    )

    for col in template_cols:
        if col not in tmp.columns:
            tmp[col] = 0

    keep_cols = ["date","snap_CA","snap_TX","snap_WI"] + template_cols
    tmp = tmp[[c for c in keep_cols if c in tmp.columns]].copy()
    return tmp

# ----------------------------
# Recursive 28-day forecast
# ----------------------------
def forecast_28_recursive(model, df_hist: pd.DataFrame, feature_cols: list, calendar_df: pd.DataFrame) -> pd.DataFrame:
    last_date = df_hist["date"].max()
    dates = [last_date + pd.Timedelta(days=i) for i in range(1, 29)]

    static_cols = ["item_id","store_id","dept_id","cat_id","state_id",
                   "item_code","store_code","dept_code","cat_code",
                   "sell_price","price_roll7_mean","price_roll28_mean","price_roll7_dev",
                   "price_pct_change","price_drop_flag"]
    static_cols = [c for c in static_cols if c in df_hist.columns]

    hist_small = df_hist[["item_id","store_id","date","sales"]].copy()
    by_item = {k: v.sort_values("date").copy() for k, v in hist_small.groupby(["item_id","store_id"], sort=False)}

    event_cols_template = [c for c in feature_cols if c.startswith("event_")]
    future_cal = build_event_dummies_for_dates(pd.Series(dates), calendar_df, event_cols_template)

    preds_out = []

    for cur_day in dates:
        last_static = (df_hist.sort_values("date")
                       .groupby(["item_id","store_id"])
                       .tail(1))[["item_id","store_id"] + static_cols].drop_duplicates(["item_id","store_id"])
        step = last_static.copy()
        step["date"] = cur_day

        # Calendar/time
        step["day_of_week"] = cur_day.weekday()
        step["month"]       = cur_day.month
        step["quarter"]     = ((cur_day.month - 1) // 3) + 1
        step["year"]        = cur_day.year

        # SNAP + event dummies
        cal_row = future_cal[future_cal["date"] == cur_day]
        for c in ["snap_CA","snap_TX","snap_WI"]:
            step[c] = int(cal_row[c].iloc[0]) if (c in cal_row.columns and not cal_row.empty) else 0
        for col in event_cols_template:
            step[col] = int(cal_row[col].iloc[0]) if (not cal_row.empty and col in cal_row.columns) else 0

        # Build combo to compute lags/rollings at cur_day
        combo_list = [hist for hist in by_item.values()]
        skel = step[["item_id","store_id","date"]].copy()
        skel["sales"] = np.nan
        combo = pd.concat(combo_list + [skel], axis=0, ignore_index=True).sort_values(["item_id","store_id","date"])

        # Lags & rollings
        for L in [1,7,14,28,56]:
            combo[f"sales_lag_{L}"] = combo.groupby(["item_id","store_id"])["sales"].shift(L)
        for W in [7,14,28,56]:
            combo[f"sales_rmean_{W}"] = combo.groupby(["item_id","store_id"])["sales"].shift(1).rolling(W).mean().reset_index(0,drop=True)

        cur_feats = combo[combo["date"] == cur_day][["item_id","store_id","date"] + [c for c in feature_cols if c.startswith("sales_lag_") or c.startswith("sales_rmean_")]]
        step = step.merge(cur_feats, on=["item_id","store_id","date"], how="left")

        X = step[feature_cols].fillna(0)
        yhat = model.predict(X)
        step["y_pred"] = yhat

        preds_out.append(step[["item_id","store_id","date","y_pred"]])

        # Append forecast as sales to histories for next iteration
        to_append = step[["item_id","store_id","date","y_pred"]].rename(columns={"y_pred":"sales"})
        for (iid, sid), grp in to_append.groupby(["item_id","store_id"]):
            by_item[(iid, sid)] = pd.concat([by_item[(iid, sid)], grp], axis=0, ignore_index=True).sort_values("date")

    return pd.concat(preds_out, axis=0).sort_values(["item_id","store_id","date"]).reset_index(drop=True)

# ----------------------------
# Main
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="M5-style demand forecasting (subset scalable) with WRMSSE and recursive 28-day inference.")
    parser.add_argument("--data_dir", default=os.path.dirname(os.path.abspath(__file__)), help="Project root (contains m5_forecasting_accuracy/).")
    parser.add_argument("--dept", default="HOBBIES_1", help="Department filter (e.g., HOBBIES_1). Use 'ALL' for no filter.")
    parser.add_argument("--stores", default="1", help="How many stores to include (int) or 'all'.")
    parser.add_argument("--items", default="50", help="How many items to include (int) or 'all'.")
    parser.add_argument("--model", default="lightgbm", choices=["lightgbm","catboost","rf"], help="Model to train.")
    parser.add_argument("--future", action="store_true", help="Run recursive 28-day forecasting beyond last date.")
    parser.add_argument("--outdir", default=None, help="Output directory for CSVs (default = script folder).")
    args = parser.parse_args()

    DATA_DIR = args.data_dir
    outdir = ensure_dir(args.outdir if args.outdir else DATA_DIR)

    cal_path = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "calendar.csv")
    sal_path = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sales_train_validation.csv")
    prc_path = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sell_prices.csv")

    info("Loading data…")
    calendar = pd.read_csv(cal_path)
    sales    = pd.read_csv(sal_path)
    prices   = pd.read_csv(prc_path)

    dept = None if args.dept.upper() == "ALL" else args.dept
    if dept is not None:
        sales = sales[sales["dept_id"] == dept]

    # Unpivot
    long = sales.melt(
        id_vars=["id","item_id","dept_id","cat_id","store_id","state_id"],
        var_name="d",
        value_name="sales"
    )

    # Merge
    df = long.merge(calendar, on="d", how="left")
    df = df.merge(prices, on=["store_id","item_id","wm_yr_wk"], how="left")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["item_id","date"])

    # Price features
    df["sell_price"] = df.groupby("item_id")["sell_price"].ffill().bfill()
    df["sell_price"] = df["sell_price"].fillna(df["sell_price"].median())
    df["price_pct_change"] = df.groupby("item_id")["sell_price"].pct_change().fillna(0)
    df["price_drop_flag"]  = (df["price_pct_change"] < 0).astype(int)
    df["price_roll7_mean"]  = df.groupby("item_id")["sell_price"].rolling(7).mean().reset_index(0,drop=True)
    df["price_roll28_mean"] = df.groupby("item_id")["sell_price"].rolling(28).mean().reset_index(0,drop=True)
    df["price_roll7_dev"]   = df["sell_price"] - df["price_roll7_mean"]

    # Calendar/time
    df["day_of_week"] = df["date"].dt.weekday
    df["month"]       = df["date"].dt.month
    df["quarter"]     = df["date"].dt.quarter
    df["year"]        = df["date"].dt.year

    # SNAP
    for c in ["snap_CA","snap_TX","snap_WI"]:
        df[c] = (df[c].fillna(0)).astype(int) if c in df.columns else 0

    # Events (top-10 per column)
    event_cols_raw = ["event_name_1","event_type_1","event_name_2","event_type_2"]
    for c in event_cols_raw:
        if c in df.columns:
            df[c] = df[c].astype("category")
            top = df[c].value_counts().head(10).index
            df[c] = df[c].where(df[c].isin(top), other="OTHER").astype("category")
        else:
            df[c] = "NONE"

    df = pd.get_dummies(df, columns=event_cols_raw, prefix=event_cols_raw, drop_first=True)
    event_dummy_cols = [c for c in df.columns if c.startswith("event_")]

    # Demand lags/rollings
    def add_lags(frame, key, col, lags):
        for L in lags:
            frame[f"{col}_lag_{L}"] = frame.groupby(key)[col].shift(L)

    def add_roll_means(frame, key, col, windows, shift=1):
        s = frame.groupby(key)[col].shift(shift)
        for W in windows:
            frame[f"{col}_rmean_{W}"] = s.rolling(W).mean().reset_index(0, drop=True)

    add_lags(df,  key="item_id", col="sales", lags=[1,7,14,28,56])
    add_roll_means(df, key="item_id", col="sales", windows=[7,14,28,56], shift=1)

    # Encoded IDs
    df["item_code"]  = df["item_id"].astype("category").cat.codes
    df["store_code"] = df["store_id"].astype("category").cat.codes
    df["dept_code"]  = df["dept_id"].astype("category").cat.codes
    df["cat_code"]   = df["cat_id"].astype("category").cat.codes

    # Feature list
    feat = [
        "sales_lag_1","sales_lag_7","sales_lag_14","sales_lag_28","sales_lag_56",
        "sales_rmean_7","sales_rmean_14","sales_rmean_28","sales_rmean_56",
        "sell_price","price_pct_change","price_drop_flag","price_roll7_mean","price_roll28_mean","price_roll7_dev",
        "day_of_week","month","quarter","year",
        "snap_CA","snap_TX","snap_WI",
        "item_code","store_code","dept_code","cat_code",
    ] + event_dummy_cols

    # Drop rows with NA features/target
    df = df.dropna(subset=feat + ["sales"]).copy()

    # Scale stores/items
    stores_arg = args.stores
    items_arg  = args.items

    MAX_STORES = as_int_or_all(stores_arg)
    MAX_ITEMS  = as_int_or_all(items_arg)

    if MAX_STORES:
        stores = df["store_id"].unique()[:MAX_STORES]
        df = df[df["store_id"].isin(stores)]
    else:
        stores = df["store_id"].unique()

    if MAX_ITEMS:
        items = df["item_id"].unique()[:MAX_ITEMS]
        df = df[df["item_id"].isin(items)]
    else:
        items = df["item_id"].unique()

    info(f"Using dept: {dept if dept else 'ALL'} | stores: {len(stores)} | items: {len(items)}")
    info(f"Train rows (post-filter): {len(df)}")

    # Validation split (last 28 days)
    max_date = df["date"].max()
    val_start = max_date - pd.Timedelta(days=27)

    X_train = df.loc[df["date"] <  val_start, feat]
    y_train = df.loc[df["date"] <  val_start, "sales"]
    X_valid = df.loc[df["date"] >= val_start, feat]
    y_valid = df.loc[df["date"] >= val_start, "sales"]

    # Model training
    model_name = args.model.lower()
    y_pred = None

    if model_name == "lightgbm":
        try:
            import lightgbm as lgb
            info("Training LightGBM…")
            dtr = lgb.Dataset(X_train, label=y_train)
            dvl = lgb.Dataset(X_valid, label=y_valid, reference=dtr)
            params = {
                "objective":"regression","metric":"rmse","learning_rate":0.05,
                "num_leaves":64,"feature_fraction":0.8,"bagging_fraction":0.8,
                "bagging_freq":1,"max_depth":-1,"verbosity":-1
            }
            model = lgb.train(
                params, dtr, num_boost_round=600,
                valid_sets=[dtr,dvl], valid_names=["train","valid"],
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)]
            )
            y_pred = model.predict(X_valid, num_iteration=model.best_iteration)
            used_model = "LightGBM"
        except Exception as e:
            warn(f"LightGBM failed ({e}); falling back to RandomForest.")
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_valid)
            used_model = "RandomForest (fallback)"
    elif model_name == "catboost":
        try:
            from catboost import CatBoostRegressor
            info("Training CatBoost…")
            model = CatBoostRegressor(
                loss_function="RMSE",
                learning_rate=0.05,
                depth=8,
                iterations=1500,
                random_seed=42,
                verbose=False,
                l2_leaf_reg=3.0
            )
            model.fit(X_train, y_train, eval_set=(X_valid, y_valid), use_best_model=True)
            y_pred = model.predict(X_valid)
            used_model = "CatBoost"
        except Exception as e:
            warn(f"CatBoost failed ({e}); falling back to RandomForest.")
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_valid)
            used_model = "RandomForest (fallback)"
    else:
        from sklearn.ensemble import RandomForestRegressor
        info("Training RandomForest…")
        model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_valid)
        used_model = "RandomForest"

    # Metrics
    rmse = float(np.sqrt(mean_squared_error(y_valid, y_pred)))

    preds = df.loc[df["date"]>=val_start, ["item_id","store_id","date"]].copy()
    preds = preds.sort_values(["item_id","store_id","date"])
    preds["y_true"] = y_valid.values
    preds["y_pred"] = y_pred
    preds["abs_err"] = (preds["y_true"] - preds["y_pred"]).abs()

    wrmsse_val = compute_wrmsse_bottom(
        pred_df=preds[["item_id","store_id","date","y_true","y_pred"]],
        full_df=df[["item_id","store_id","date","sales","sell_price"]],
        val_start_ts=val_start
    )

    out_csv = os.path.join(outdir, "m5_baseline_predictions.csv")
    preds.to_csv(out_csv, index=False)

    info(f"Model: {used_model}")
    info(f"Validation start: {str(val_start.date())}")
    info(f"Validation RMSE: {round(rmse, 5)}")
    info(f"Validation WRMSSE (bottom): {round(wrmsse_val, 5)}")
    info(f"Train/Valid rows: {X_train.shape[0]} / {X_valid.shape[0]}")
    info(f"Items trained: {len(items)} | Stores: {len(stores)}")
    info(f"Saved validation predictions → {out_csv}")

    # True future 28-day forecast
    if args.future:
        info("Running 28-day recursive forecast (true future)…")
        future_preds = forecast_28_recursive(
            model=model,
            df_hist=df,                 # engineered historical DF
            feature_cols=feat,          # same feature set
            calendar_df=calendar        # for SNAP/events
        )
        future_csv = os.path.join(outdir, "m5_future_28day_forecast.csv")
        future_preds.to_csv(future_csv, index=False)
        info(f"Saved future forecast → {future_csv}")

if __name__ == "__main__":
    main()
