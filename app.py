import os
from pathlib import Path
import streamlit as st
import pandas as pd
from src.utils import ensure_dirs, get_data_paths, logger
from src.cleaning import clean_inventory_df, save_cleaned_inventory
from src.forecast import compute_reorder_plan
from src.detect import detect_shelf_gaps

st.set_page_config(page_title="Backroom — Inventory Intelligence", layout="wide")
st.title("Backroom — Inventory Intelligence")

ensure_dirs()
DATA_RAW, DATA_PROCESSED, SHELVES = get_data_paths()

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Overview", "Upload & Clean", "Forecast", "Shelf Gaps (Vision)"])

if page == "Overview":
    st.subheader("Processed Inventory Snapshot")
    processed_fp = DATA_PROCESSED / "inventory_clean.csv"
    if processed_fp.exists():
        df = pd.read_csv(processed_fp)
        st.metric("Unique SKUs", df["sku"].nunique())
        st.metric("Total On-Hand", int(df["on_hand"].sum()))
        st.metric("Avg Daily Sales (mean)", round(df["avg_daily_sales"].mean(), 2))
        st.dataframe(df.head(100), use_container_width=True)
    else:
        st.info("No processed inventory found yet. Go to 'Upload & Clean' to ingest data.")

elif page == "Upload & Clean":
    st.subheader("Upload Inventory CSV")
    st.markdown("Upload a CSV with columns like: `sku, product_name, on_hand, backroom_units, shelf_units, avg_daily_sales, lead_time_days`")
    uploaded = st.file_uploader("inventory.csv", type=["csv"])
    if uploaded is not None:
        raw_fp = DATA_RAW / "inventory.csv"
        raw_fp.write_bytes(uploaded.read())
        st.success(f"Saved raw file → {raw_fp}")
        df = pd.read_csv(raw_fp)
        cleaned = clean_inventory_df(df)
        out_fp = save_cleaned_inventory(cleaned, DATA_PROCESSED / "inventory_clean.csv")
        st.success(f"Cleaned & saved → {out_fp}")
        st.dataframe(cleaned.head(100), use_container_width=True)

elif page == "Forecast":
    st.subheader("Reorder Planning")
    processed_fp = DATA_PROCESSED / "inventory_clean.csv"
    if not processed_fp.exists():
        st.warning("No processed data yet. Upload & clean first.")
    else:
        df = pd.read_csv(processed_fp)
        plan = compute_reorder_plan(df)
        st.dataframe(plan, use_container_width=True)
        csv = plan.to_csv(index=False).encode("utf-8")
        st.download_button("Download Reorder Plan CSV", data=csv, file_name="reorder_plan.csv")

elif page == "Shelf Gaps (Vision)":
    st.subheader("Shelf Gap Detection (Demo Stub)")
    st.markdown("Upload shelf images to detect likely gaps (demo uses a lightweight heuristic).")
    imgs = st.file_uploader("Shelf images", type=["jpg","jpeg","png"], accept_multiple_files=True)
    if imgs:
        results = []
        for f in imgs:
            # Save to shelves/ and run stub detector
            out = (SHELVES / f.name)
            out.write_bytes(f.read())
            gaps = detect_shelf_gaps(out)
            results.append({"image": f.name, "gap_score": gaps.get("gap_score", 0.0), "notes": gaps.get("notes", "")})
        st.dataframe(pd.DataFrame(results), use_container_width=True)
