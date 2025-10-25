# m5_lightgbm_baseline.py
import os
import sys
import math
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

# ----------------------------
# CONFIG / SCALING KNOBS
# ----------------------------
# Try 50 → 200 → None (all items in dept)
MAX_ITEMS  = 50
# Try 1 → None (all stores in dept)
MAX_STORES = 1
# Department filter (keep one dept to control memory first)
DEPT_FILTER = "HOBBIES_1"   # set to None to keep all departments

# Choose model: "lgbm" (preferred) or "rf"
MODEL_CHOICE = "lgbm"

# Whether to run a true-future 28-day recursive forecast
RUN_FUTURE_28_FORECAST = True

# ----------------------------
# PATHS
# ----------------------------
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
calendar_path = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "calendar.csv")
sales_path    = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sales_train_validation.csv")
prices_path   = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sell_prices.csv")

# ----------------------------
# LOAD
# ----------------------------
calendar = pd.read_csv(calendar_path)
sales    = pd.read_csv(sales_path)
prices   = pd.read_csv(prices_path)

# Optional department restriction (memory control)
if DEPT_FILTER is not None:
    sales = sales[sales["dept_id"] == DEPT_FILTER]

# ----------------------------
# UNPIVOT (long format)
# ----------------------------
long = sales.melt(
    id_vars=["id","item_id","dept_id","cat_id","store_id","state_id"],
    var_name="d",
    value_name="sales"
)

# ----------------------------
# MERGE calendar & prices
# ----------------------------
df = long.merge(calendar, on="d", how="left")
df = df.merge(prices, on=["store_id","item_id","wm_yr_wk"], how="left")
df["date"] = pd.to_datetime(df["date"])

# ----------------------------
# SORT
# ----------------------------
df = df.sort_values(["item_id","date"])

# ----------------------------
# FEATURE ENGINEERING
# ----------------------------
# 1) Prices (fill + dynamics)
df["sell_price"] = df.groupby("item_id")["sell_price"].ffill().bfill()
df["sell_price"] = df["sell_price"].fillna(df["sell_price"].median())

df["price_pct_change"] = df.groupby("item_id")["sell_price"].pct_change().fillna(0)
df["price_drop_flag"]  = (df["price_pct_change"] < 0).astype(int)
df["price_roll7_mean"]  = df.groupby("item_id")["sell_price"].rolling(7).mean().reset_index(0,drop=True)
df["price_roll28_mean"] = df.groupby("item_id")["sell_price"].rolling(28).mean().reset_index(0,drop=True)
df["price_roll7_dev"]   = df["sell_price"] - df["price_roll7_mean"]

# 2) Time / calendar features
df["day_of_week"] = df["date"].dt.weekday
df["month"]       = df["date"].dt.month
df["quarter"]     = df["date"].dt.quarter
df["year"]        = df["date"].dt.year

# 3) SNAP as ints
for c in ["snap_CA","snap_TX","snap_WI"]:
    df[c] = (df[c].fillna(0)).astype(int) if c in df.columns else 0

# 4) Events (optional one-hot with small vocab to avoid bloat)
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

# 5) Demand lags & rolling means
def add_lags(frame, key, col, lags):
    for L in lags:
        frame[f"{col}_lag_{L}"] = frame.groupby(key)[col].shift(L)

def add_roll_means(frame, key, col, windows, shift=1):
    s = frame.groupby(key)[col].shift(shift)  # only past
    for W in windows:
        frame[f"{col}_rmean_{W}"] = s.rolling(W).mean().reset_index(0, drop=True)

add_lags(df,  key="item_id", col="sales", lags=[1,7,14,28,56])
add_roll_means(df, key="item_id", col="sales", windows=[7,14,28,56], shift=1)

# Encodings for IDs
df["item_code"]  = df["item_id"].astype("category").cat.codes
df["store_code"] = df["store_id"].astype("category").cat.codes
df["dept_code"]  = df["dept_id"].astype("category").cat.codes
df["cat_code"]   = df["cat_id"].astype("category").cat.codes

# ----------------------------
# FEATURE LIST
# ----------------------------
feat = [
    # demand lags
    "sales_lag_1","sales_lag_7","sales_lag_14","sales_lag_28","sales_lag_56",
    # demand roll means
    "sales_rmean_7","sales_rmean_14","sales_rmean_28","sales_rmean_56",
    # price & price dynamics
    "sell_price","price_pct_change","price_drop_flag","price_roll7_mean","price_roll28_mean","price_roll7_dev",
    # calendar
    "day_of_week","month","quarter","year",
    # SNAP
    "snap_CA","snap_TX","snap_WI",
    # encoded IDs
    "item_code","store_code","dept_code","cat_code",
]
feat += event_dummy_cols

# ----------------------------
# DROP NA ROWS (due to lags/rollings)
# ----------------------------
df = df.dropna(subset=feat+["sales"]).copy()

# ----------------------------
# SCALING (STORES / ITEMS)
# ----------------------------
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

# ----------------------------
# LAST-28-DAYS VALIDATION SPLIT
# ----------------------------
max_date = df["date"].max()
val_start = max_date - pd.Timedelta(days=27)

X_train = df.loc[df["date"] <  val_start, feat]
y_train = df.loc[df["date"] <  val_start, "sales"]
X_valid = df.loc[df["date"] >= val_start, feat]
y_valid = df.loc[df["date"] >= val_start, "sales"]

# ----------------------------
# TRAIN (LGBM → RF fallback)
# ----------------------------
model_name = None
y_pred = None

if MODEL_CHOICE.lower() == "lgbm":
    try:
        import lightgbm as lgb
        model_name = "LightGBM"
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
    except Exception as e:
        from sklearn.ensemble import RandomForestRegressor
        model_name = f"RandomForest (fallback: {e})"
        model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_valid)
else:
    from sklearn.ensemble import RandomForestRegressor
    model_name = "RandomForest"
    model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_valid)

# ----------------------------
# METRICS: RMSE
# ----------------------------
rmse = float(np.sqrt(mean_squared_error(y_valid, y_pred)))

# ----------------------------
# PRED TABLE (validation)
# ----------------------------
preds = df.loc[df["date"]>=val_start, ["item_id","store_id","date"]].copy()
preds = preds.sort_values(["item_id","store_id","date"])
preds["y_true"] = y_valid.values
preds["y_pred"] = y_pred
preds["abs_err"] = (preds["y_true"] - preds["y_pred"]).abs()

# ----------------------------
# BOTTOM-LEVEL WRMSSE
# ----------------------------
def rmsse_denominator(series: pd.Series) -> float:
    """Makridakis RMSSE denominator on in-sample: sqrt(mean((y_t - y_{t-1})^2))."""
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
    weights: avg revenue over validation window; normalized to sum 1
    """
    # Weights by average revenue in validation window
    val_mask = (full_df["date"] >= val_start_ts)
    rev = (full_df.loc[val_mask, ["item_id","store_id","date","sales","sell_price"]]
           .assign(revenue=lambda x: x["sales"]*x["sell_price"])
           .groupby(["item_id","store_id"])["revenue"].mean())
    rev = rev.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if rev.sum() == 0:
        rev = rev * 0 + 1.0
    w = rev / rev.sum()

    # Denominator per (item,store) from pre-validation
    pre_mask = (full_df["date"] < val_start_ts)
    denom = (full_df.loc[pre_mask, ["item_id","store_id","date","sales"]]
             .groupby(["item_id","store_id"])["sales"]
             .apply(rmsse_denominator))

    # MSE per series over validation window
    mse = pred_df.assign(se=lambda x: (x["y_pred"] - x["y_true"])**2) \
                 .groupby(["item_id","store_id"])["se"].mean()

    # RMSSE
    rmsse = (mse**0.5) / denom
    rmsse = rmsse.replace([np.inf, -np.inf], np.nan)

    # Align weights and compute weighted mean
    rmsse = rmsse.reindex(w.index)
    wrmsse = np.nansum(w * rmsse)
    return float(wrmsse)

# Compute WRMSSE on validation
wrmsse_val = compute_wrmsse_bottom(
    pred_df=preds[["item_id","store_id","date","y_true","y_pred"]],
    full_df=df[["item_id","store_id","date","sales","sell_price"]],
    val_start_ts=val_start
)

# ----------------------------
# SAVE VALIDATION PREDS
# ----------------------------
out_csv = os.path.join(DATA_DIR, "m5_baseline_predictions.csv")
preds.to_csv(out_csv, index=False)

print("Model:", model_name)
print("Validation start:", str(val_start.date()))
print("Validation RMSE:", round(rmse, 5))
print("Validation WRMSSE (bottom):", round(wrmsse_val, 5))
print("Train/Valid rows:", X_train.shape[0], X_valid.shape[0])
print("Items trained:", len(items))
print("Stores trained:", len(stores))
print("Saved:", out_csv)

# ----------------------------
# RECURSIVE 28-DAY FORECAST (true future)
# ----------------------------
def build_event_dummies_for_dates(dates: pd.Series, calendar_df: pd.DataFrame, template_cols: list) -> pd.DataFrame:
    """
    For future dates, map events from calendar and produce the same dummy columns
    present in training (template_cols starting with 'event_').
    """
    # Merge on 'date' (calendar has 'date' as string; ensure datetime)
    cal = calendar_df.copy()
    cal["date"] = pd.to_datetime(cal["date"])
    cols = ["date","event_name_1","event_type_1","event_name_2","event_type_2","snap_CA","snap_TX","snap_WI"]
    for c in cols:
        if c not in cal.columns:
            cal[c] = np.nan
    base = pd.DataFrame({"date": dates})
    tmp = base.merge(cal[cols], on="date", how="left")

    # Coerce SNAP to ints
    for c in ["snap_CA","snap_TX","snap_WI"]:
        tmp[c] = (tmp[c].fillna(0)).astype(int)

    # Map events to same limited vocab (OTHER fallback), then get dummies
    for c in ["event_name_1","event_type_1","event_name_2","event_type_2"]:
        if c in tmp.columns:
            tmp[c] = tmp[c].astype("category")
        else:
            tmp[c] = "NONE"
    tmp = pd.get_dummies(tmp, columns=["event_name_1","event_type_1","event_name_2","event_type_2"], prefix=["event_name_1","event_type_1","event_name_2","event_type_2"], drop_first=True)

    # Ensure all template event columns exist
    for col in template_cols:
        if col not in tmp.columns:
            tmp[col] = 0
    # Trim extras
    keep_cols = ["date","snap_CA","snap_TX","snap_WI"] + template_cols
    tmp = tmp[[c for c in keep_cols if c in tmp.columns]].copy()
    return tmp

def forecast_28_recursive(model, df_hist: pd.DataFrame, feature_cols: list, calendar_df: pd.DataFrame) -> pd.DataFrame:
    """
    df_hist: feature-engineered historical DF up to last observed date (per item_id/store_id).
             Must include columns needed to compute lags/rollings and static encodings.
    Returns: [item_id, store_id, date, y_pred] for the next 28 days.
    """
    last_date = df_hist["date"].max()
    dates = [last_date + pd.Timedelta(days=i) for i in range(1, 29)]
    # Static per item/store (codes etc.)
    static_cols = ["item_id","store_id","dept_id","cat_id","state_id","item_code","store_code","dept_code","cat_code",
                   "sell_price","price_roll7_mean","price_roll28_mean","price_roll7_dev","price_pct_change","price_drop_flag"]
    static_cols = [c for c in static_cols if c in df_hist.columns]

    # Build per-item history (only the columns we need to recompute demand lags/rollings)
    hist_small = df_hist[["item_id","store_id","date","sales"]].copy()
    by_item = {k: v.sort_values("date").copy() for k, v in hist_small.groupby(["item_id","store_id"], sort=False)}

    # Prepare calendar/event dummies for future dates (same columns as training)
    event_cols_template = [c for c in feature_cols if c.startswith("event_")]
    future_cal = build_event_dummies_for_dates(pd.Series(dates), calendar_df, event_cols_template)

    preds_out = []

    for cur_day in dates:
        # Prepare skeleton rows for each (item,store)
        # Use last known static values from df_hist
        last_static = (df_hist.sort_values("date").groupby(["item_id","store_id"]).tail(1))[["item_id","store_id"] + static_cols].drop_duplicates(["item_id","store_id"])
        step = last_static.copy()
        step["date"] = cur_day

        # Calendar/time features
        step["day_of_week"] = cur_day.weekday()
        step["month"]       = cur_day.month
        step["quarter"]     = ((cur_day.month - 1) // 3) + 1
        step["year"]        = cur_day.year

        # Map SNAP + event dummies for current day
        cal_row = future_cal[future_cal["date"] == cur_day]
        for c in ["snap_CA","snap_TX","snap_WI"]:
            if c in cal_row.columns:
                step[c] = int(cal_row[c].iloc[0]) if not cal_row.empty else 0
            else:
                step[c] = 0
        # Ensure all event dummy cols exist
        for col in event_cols_template:
            step[col] = int(cal_row[col].iloc[0]) if (not cal_row.empty and col in cal_row.columns) else 0

        # Price dynamics for future: keep last known price features (no price forecast here)
        # If you have future prices, merge them here instead.

        # Recompute demand lags/rollings using history + this new empty day
        combo_list = []
        for (iid, sid), hist in by_item.items():
            combo_list.append(hist)
        # Append today's skeleton (with sales NaN) to compute lags
        skel = step[["item_id","store_id","date"]].copy()
        skel["sales"] = np.nan
        combo = pd.concat(combo_list + [skel], axis=0, ignore_index=True).sort_values(["item_id","store_id","date"])

        # Lags & rollings
        for L in [1,7,14,28,56]:
            combo[f"sales_lag_{L}"] = combo.groupby(["item_id","store_id"])["sales"].shift(L)
        for W in [7,14,28,56]:
            combo[f"sales_rmean_{W}"] = combo.groupby(["item_id","store_id"])["sales"].shift(1).rolling(W).mean().reset_index(0,drop=True)

        cur_feats = combo[combo["date"] == cur_day][["item_id","store_id","date"] + [c for c in feature_cols if c.startswith("sales_lag_") or c.startswith("sales_rmean_")]]
        # Join back with other features
        step = step.merge(cur_feats, on=["item_id","store_id","date"], how="left")

        # Fill any remaining NaNs in features (early steps can have NaNs for long lags)
        X = step[feature_cols].fillna(0)
        yhat = model.predict(X)
        step["y_pred"] = yhat

        # Save outputs
        preds_out.append(step[["item_id","store_id","date","y_pred"]])

        # Append predictions to histories as if they were actuals (to feed next day's lags)
        to_append = step[["item_id","store_id","date","y_pred"]].rename(columns={"y_pred":"sales"})
        for (iid, sid), grp in to_append.groupby(["item_id","store_id"]):
            by_item[(iid, sid)] = pd.concat([by_item[(iid, sid)], grp], axis=0, ignore_index=True).sort_values("date")

    return pd.concat(preds_out, axis=0).sort_values(["item_id","store_id","date"]).reset_index(drop=True)

if RUN_FUTURE_28_FORECAST:
    future_preds = forecast_28_recursive(
        model=model,
        df_hist=df,                 # historical engineered DF (up to max date)
        feature_cols=feat,          # same feature list used in training
        calendar_df=calendar        # for SNAP/events
    )
    future_csv = os.path.join(DATA_DIR, "m5_future_28day_forecast.csv")
    future_preds.to_csv(future_csv, index=False)
    print("Future 28-day forecast saved:", future_csv)
