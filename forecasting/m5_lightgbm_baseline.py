# m5_lightgbm_baseline.py
import os
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
calendar_path = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "calendar.csv")
sales_path    = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sales_train_validation.csv")
prices_path   = os.path.join(DATA_DIR, "m5_forecasting_accuracy", "sell_prices.csv")

# --- Load
calendar = pd.read_csv(calendar_path)
sales    = pd.read_csv(sales_path)
prices   = pd.read_csv(prices_path)

# --- Subset for speed (same as our session)
sales = sales[(sales["store_id"]=="CA_1") & (sales["dept_id"]=="HOBBIES_1")]

# --- Unpivot
long = sales.melt(
    id_vars=["id","item_id","dept_id","cat_id","store_id","state_id"],
    var_name="d",
    value_name="sales"
)

# --- Merge calendar & prices
df = long.merge(calendar, on="d", how="left")
df = df.merge(prices, on=["store_id","item_id","wm_yr_wk"], how="left")
df["date"] = pd.to_datetime(df["date"])

# --- Sort + features
df = df.sort_values(["item_id","date"])
df["lag_7"]   = df.groupby("item_id")["sales"].shift(7)
df["lag_28"]  = df.groupby("item_id")["sales"].shift(28)
df["rmean_7"] = df.groupby("item_id")["sales"].shift(7).rolling(7).mean().reset_index(0, drop=True)
df["rmean_28"]= df.groupby("item_id")["sales"].shift(28).rolling(28).mean().reset_index(0, drop=True)

for c in ["snap_CA","snap_TX","snap_WI"]:
    if c in df.columns: df[c] = df[c].fillna(0).astype(int)
    else: df[c] = 0

df["sell_price"] = df.groupby("item_id")["sell_price"].ffill().bfill()
df["sell_price"] = df["sell_price"].fillna(df["sell_price"].median())

df["day_of_week"] = df["date"].dt.weekday
df["month"]       = df["date"].dt.month
df["quarter"]     = df["date"].dt.quarter
df["year"]        = df["date"].dt.year
df["item_code"]   = df["item_id"].astype("category").cat.codes

feat = ["lag_7","lag_28","rmean_7","rmean_28","sell_price",
        "day_of_week","month","quarter","year",
        "snap_CA","snap_TX","snap_WI","item_code"]

df = df.dropna(subset=feat+["sales"]).copy()

# After df = df.dropna(...).copy()
# SCALE KNOB(s):
MAX_ITEMS = 50   # try 50 → 200 → None (all in dept)
MAX_STORES = 1   # later: set to None to include all stores in this dept

stores = df["store_id"].unique()[:MAX_STORES] if MAX_STORES else df["store_id"].unique()
df = df[df["store_id"].isin(stores)]

if MAX_ITEMS:
    items = df["item_id"].unique()[:MAX_ITEMS]
    df = df[df["item_id"].isin(items)]

# Reduce to 50 items for speed
items = df["item_id"].unique()[:50]
df = df[df["item_id"].isin(items)].copy()

# --- Last-28-days validation split
max_date = df["date"].max()
val_start = max_date - pd.Timedelta(days=27)

X_train = df.loc[df["date"] <  val_start, feat]
y_train = df.loc[df["date"] <  val_start, "sales"]
X_valid = df.loc[df["date"] >= val_start, feat]
y_valid = df.loc[df["date"] >= val_start, "sales"]

# --- Train (LightGBM with callback early stopping; RF fallback)
y_pred = None
model_name = "LightGBM"
try:
    import lightgbm as lgb
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

rmse = float(np.sqrt(mean_squared_error(y_valid, y_pred)))
preds = df.loc[df["date"]>=val_start, ["item_id","date"]].copy()
preds["y_true"] = y_valid.values
preds["y_pred"] = y_pred
preds["abs_err"] = (preds["y_true"] - preds["y_pred"]).abs()
out_csv = os.path.join(DATA_DIR, "m5_baseline_predictions.csv")
preds.to_csv(out_csv, index=False)

print("Model:", model_name)
print("Validation start:", str(val_start.date()))
print("Validation RMSE:", round(rmse, 4))
print("Train/Valid rows:", X_train.shape[0], X_valid.shape[0])
print("Items trained:", len(items))
print("Saved:", out_csv)
