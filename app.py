"""
Backroom — Inventory Intelligence + Chatbot (Streamlit + LangGraph + DuckDB)
----------------------------------------------------------------------------
Single-file Streamlit app that provides:
1) Inventory workflow (overview → upload/clean → reorder forecast → shelf-gaps demo)
2) A guarded chatbot powered by LangGraph that ONLY answers about:
   - Inventory (stock, availability, quantities),
   - Timelines (schedules, deadlines, ETAs, roadmaps), and
   - Future predictions (forecasts, projections, outlooks, trends).
3) NEW: Persistent storage using DuckDB (optional but recommended).

Run locally
----------
# 1) Install deps
pip install -U streamlit langgraph openai typing_extensions pydantic pandas numpy duckdb pillow

# 2) Your project utilities (expected in ./src)
#    src/utils.py     -> ensure_dirs, get_data_paths, logger
#    src/cleaning.py  -> clean_inventory_df, save_cleaned_inventory
#    src/forecast.py  -> compute_reorder_plan
#    src/detect.py    -> detect_shelf_gaps
#    src/tools.py     -> tool_load_inventory, tool_lookup_sku, tool_reorder_plan, tool_detect_gap

# 3) Environment
export OPENAI_API_KEY="sk-..."              # or setx on Windows
# Optional for OpenAI-compatible endpoints:
# export OPENAI_BASE_URL="https://your.endpoint/v1"
# Optional model override:
# export OPENAI_MODEL="gpt-4o-mini"
# export MODEL_TEMPERATURE="0.4"
# Optional DuckDB path (defaults to ./data/backroom.duckdb)
# export DUCKDB_PATH="./data/backroom.duckdb"

# 4) Launch
streamlit run app.py
"""

from __future__ import annotations

# --- Standard libs ---
import os
import re
import logging
from pathlib import Path
from typing import Annotated, TypedDict, List

# --- Third party ---
import streamlit as st
import pandas as pd
from openai import OpenAI
import numpy as np

# --- LangGraph ---
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# --- Project utils (user-provided) ---
from src.utils import ensure_dirs, get_data_paths, logger
from src.cleaning import clean_inventory_df, save_cleaned_inventory
from src.forecast import compute_reorder_plan
from src.detect import detect_shelf_gaps

# ------ Project tools (reused in agent) ------
from src.tools import (
    tool_load_inventory,
    tool_lookup_sku,
    tool_reorder_plan,
    tool_detect_gap,   # <-- added
)

# =============================
# Streamlit App Configuration
# =============================
st.set_page_config(page_title="Backroom — Inventory Intelligence", layout="wide")
st.title("Backroom — Inventory Intelligence")

# Prepare data directories and known paths
ensure_dirs()
DATA_RAW, DATA_PROCESSED, SHELVES = get_data_paths()

# =============================
# DuckDB helper (uses Python module, not JS)
# =============================
# Use centralized Python helper (db/duckdb_helper.py) instead of any JS files.
try:
    from db.duckdb_helper import get_connection, db_path as _DB_PATH
    _DUCKDB_AVAILABLE = True
except Exception as e:
    get_connection = None  # type: ignore
    _DB_PATH = None
    _DUCKDB_AVAILABLE = False
    logging.warning("DuckDB helper unavailable: %s", e)

class DB:
    """Tiny helper around the shared DuckDB connection from db.duckdb_helper."""
    con = None
    enabled = False
    db_path = None

    @classmethod
    def init(cls):
        if not _DUCKDB_AVAILABLE:
            cls.con = None
            cls.enabled = False
            cls.db_path = None
            return

        try:
            cls.con = get_connection()
            cls.db_path = _DB_PATH
            cls.enabled = True
            # Ensure required tables exist (inventory, shelf_gaps, chat_logs).
            cls.con.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    sku TEXT,
                    product_name TEXT,
                    on_hand DOUBLE,
                    backroom_units DOUBLE,
                    shelf_units DOUBLE,
                    avg_daily_sales DOUBLE,
                    lead_time_days DOUBLE
                );
            """)
            cls.con.execute("""
                CREATE TABLE IF NOT EXISTS shelf_gaps (
                    image TEXT,
                    gap_score DOUBLE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT current_timestamp
                );
            """)
            cls.con.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT current_timestamp
                );
            """)
        except Exception as e:
            logging.exception("DuckDB initialization failed: %s", e)
            cls.con = None
            cls.enabled = False
            cls.db_path = None

    @classmethod
    def upsert_inventory_df(cls, df: pd.DataFrame):
        """Create/replace inventory table from a cleaned dataframe."""
        if not cls.enabled or df is None or df.empty:
            return
        cls.con.register("df_inv", df)
        cls.con.execute("CREATE OR REPLACE TABLE inventory AS SELECT * FROM df_inv;")
        cls.con.unregister("df_inv")

    @classmethod
    def read_inventory_df(cls) -> pd.DataFrame | None:
        if not cls.enabled:
            return None
        try:
            return cls.con.execute("SELECT * FROM inventory").fetch_df()
        except Exception:
            return None

    @classmethod
    def insert_shelf_gap(cls, image: str, gap_score: float, notes: str):
        if not cls.enabled:
            return
        cls.con.execute(
            "INSERT INTO shelf_gaps(image, gap_score, notes) VALUES (?, ?, ?)",
            [image, float(gap_score), str(notes or "")],
        )

    @classmethod
    def log_chat(cls, role: str, content: str):
        if not cls.enabled:
            return
        cls.con.execute("INSERT INTO chat_logs(role, content) VALUES (?, ?)", [role, content])

DB.init()

# =============================
# Sidebar & Navigation
# =============================
with st.sidebar:
    st.markdown("**Storage**")
    if DB.enabled:
        st.success(f"DuckDB: ON  \n`{DB.db_path}`")
    else:
        st.info("DuckDB: OFF (using CSV files only)")
    page = st.radio(
        "Navigation",
        ["Overview", "Upload & Clean", "Forecast", "Shelf Gaps (Vision)", "Chat", "Admin (DB Browser)"],
    )

# =============================
# Pages 1–4: Inventory Workflow
# =============================
if page == "Overview":
    st.subheader("Processed Inventory Snapshot")
    processed_fp = DATA_PROCESSED / "inventory_clean.csv"

    # Prefer DuckDB when available, else fall back to CSV
    df = None
    if DB.enabled:
        df = DB.read_inventory_df()

    if df is None and processed_fp.exists():
        df = pd.read_csv(processed_fp)

    if isinstance(df, pd.DataFrame) and not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Unique SKUs", int(df["sku"].nunique()))
        with c2:
            st.metric("Total On-Hand", int(df.get("on_hand", pd.Series(dtype=float)).sum()))
        with c3:
            mean_ads = round(df.get("avg_daily_sales", pd.Series(dtype=float)).mean() or 0, 2)
            st.metric("Avg Daily Sales (mean)", mean_ads)
        st.dataframe(df.head(100), use_container_width=True)
    else:
        st.info("No processed inventory found yet. Go to 'Upload & Clean' to ingest data.")

elif page == "Upload & Clean":
    st.subheader("Upload Inventory CSV")
    st.markdown(
        "Upload a CSV with columns like: `sku, product_name, on_hand, backroom_units, shelf_units, avg_daily_sales, lead_time_days`"
    )
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

        # NEW: persist to DuckDB if available
        if DB.enabled:
            try:
                DB.upsert_inventory_df(cleaned)
                st.success("Persisted cleaned inventory to DuckDB (table: `inventory`).")
            except Exception as e:
                st.warning(f"DuckDB persistence skipped: {e}")

elif page == "Forecast":
    st.subheader("Reorder Planning")
    processed_fp = DATA_PROCESSED / "inventory_clean.csv"

    # Prefer DuckDB inventory
    df = DB.read_inventory_df() if DB.enabled else None
    if df is None:
        if not processed_fp.exists():
            st.warning("No processed data yet. Upload & clean first.")
        else:
            df = pd.read_csv(processed_fp)

    if isinstance(df, pd.DataFrame):
        plan = compute_reorder_plan(df)
        st.dataframe(plan, use_container_width=True)
        csv = plan.to_csv(index=False).encode("utf-8")
        st.download_button("Download Reorder Plan CSV", data=csv, file_name="reorder_plan.csv")

elif page == "Shelf Gaps (Vision)":
    st.subheader("Shelf Gap Detection (Demo Stub)")
    st.markdown("Upload shelf images to detect likely gaps (demo uses a lightweight heuristic).")
    imgs = st.file_uploader("Shelf images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if imgs:
        results = []
        for f in imgs:
            # Save to shelves/ and run stub detector
            out = SHELVES / f.name
            out.write_bytes(f.read())
            gaps = detect_shelf_gaps(out)
            row = {
                "image": f.name,
                "gap_score": float(gaps.get("gap_score", 0.0)),
                "notes": gaps.get("notes", ""),
            }
            results.append(row)

            # NEW: persist result to DuckDB if available
            if DB.enabled:
                try:
                    DB.insert_shelf_gap(row["image"], row["gap_score"], row["notes"])
                except Exception as e:
                    st.warning(f"Could not persist shelf gap for {f.name}: {e}")

        st.dataframe(pd.DataFrame(results), use_container_width=True)


elif page == "Admin (DB Browser)":
    st.subheader("🗄️ Admin — Browse DuckDB Tables")
    if not DB.enabled:
        st.info("DuckDB is OFF. Set DUCKDB_PATH and restart to enable the DB browser.")
    else:
        # ---- Inventory browser ----
        st.markdown("### Inventory")
        inv = DB.read_inventory_df()
        if inv is None or inv.empty:
            st.caption("No rows in `inventory`. Upload & Clean to populate.")
        else:
            # simple search on SKU or product_name
            c1, c2 = st.columns([2,1])
            with c1:
                q = st.text_input("Search (SKU or Product)", placeholder="e.g., SKU-123 or shampoo")
            with c2:
                top_n = st.number_input("Max rows", 50, 5000, 500, step=50)
            df_view = inv
            if q:
                q_lower = q.lower()
                mask = inv["sku"].astype(str).str.lower().str.contains(q_lower) | inv["product_name"].astype(str).str.lower().str.contains(q_lower)
                df_view = inv[mask]
            st.dataframe(df_view.head(int(top_n)), use_container_width=True)
            st.download_button(
                "⬇️ Download inventory (CSV)",
                data=df_view.to_csv(index=False).encode("utf-8"),
                file_name="inventory_admin_export.csv",
                mime="text/csv"
            )

        st.markdown("---")

        # ---- Chat logs browser ----
        st.markdown("### Chat Logs")
        try:
            chat_df = DB.con.execute("SELECT * FROM chat_logs ORDER BY created_at DESC").fetch_df()
        except Exception as e:
            chat_df = None
            st.warning(f"Could not read chat_logs: {e}")

        if chat_df is None or chat_df.empty:
            st.caption("No chat logs yet. Talk to the assistant in the Chat tab.")
        else:
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                role_filter = st.multiselect("Role filter", options=sorted(chat_df["role"].dropna().unique().tolist()), default=[])
            with c2:
                top_n_chat = st.number_input("Max rows", 50, 5000, 500, step=50, key="chat_max_rows")
            with c3:
                search_chat = st.text_input("Search text", placeholder="keywords in content", key="chat_search")
            df_chat_view = chat_df
            if role_filter:
                df_chat_view = df_chat_view[df_chat_view["role"].isin(role_filter)]
            if search_chat:
                s = search_chat.lower()
                df_chat_view = df_chat_view[df_chat_view["content"].astype(str).str.lower().str.contains(s)]
            st.dataframe(df_chat_view.head(int(top_n_chat)), use_container_width=True)
            st.download_button(
                "⬇️ Download chat logs (CSV)",
                data=df_chat_view.to_csv(index=False).encode("utf-8"),
                file_name="chat_logs_admin_export.csv",
                mime="text/csv"
            )

# =============================
# Page 5: Guarded Chat (LangGraph)
# =============================
if page == "Chat":
    st.subheader("💬 Inventory / Timeline / Forecast Chat")

    with st.sidebar:
        st.markdown("**Chat Settings**")
        default_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        model_name = st.text_input("Model name", value=default_model, help="Any OpenAI-compatible chat model.")
        temp = st.slider("Temperature", 0.0, 1.0, float(os.environ.get("MODEL_TEMPERATURE", 0.6)), 0.05)
        if st.button("♻️ Reset conversation", type="secondary"):
            st.session_state.pop("chat_messages", None)
            st.success("Conversation cleared.")
        st.caption(
            "Env vars respected: OPENAI_API_KEY, OPENAI_BASE_URL (optional), OPENAI_MODEL, MODEL_TEMPERATURE, DUCKDB_PATH"
        )

    # -------------
    # LangGraph state
    # -------------
    class MessagesState(TypedDict):
        messages: Annotated[List[dict], add_messages]

    def call_model(state: MessagesState) -> MessagesState:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        chat_messages = state.get("messages", [])
        if not chat_messages:
            return {"messages": []}
        resp = client.chat.completions.create(
            model=model,
            messages=chat_messages,
            temperature=float(os.environ.get("MODEL_TEMPERATURE", 0.6)),
        )
        assistant_text = resp.choices[0].message.content or ""
        return {"messages": [{"role": "assistant", "content": assistant_text}]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("llm", call_model)
    workflow.set_entry_point("llm")
    workflow.add_edge("llm", END)
    app_graph = workflow.compile()

    # Conversation store
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "system",
                "content": (
                    "You are a specialized assistant. You ONLY answer questions about: (1) inventory (stock levels, "
                    "availability, quantities), (2) timelines (schedules, deadlines, ETAs, roadmaps), and (3) future "
                    "predictions (forecasts, projections, outlooks, trends). If a user asks for anything outside these "
                    "three areas, briefly refuse and redirect them to those topics. Be concise and actionable."
                ),
            }
        ]

    # Allow runtime overrides via sidebar
    os.environ["OPENAI_MODEL"] = model_name
    os.environ["MODEL_TEMPERATURE"] = str(temp)

    # Render transcript (hide system)
    for msg in st.session_state.chat_messages:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about inventory, timelines, or forecasts…")
    if prompt:
        user_msg = {"role": "user", "content": prompt}
        st.session_state.chat_messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(prompt)
        # NEW: persist user message to DuckDB
        DB.log_chat("user", prompt)

        # Guardrail: allow only inventory, timelines, and future predictions
        allowed_keywords = [
            "inventory", "stock", "stocks", "in stock", "out of stock", "availability", "available",
            "quantity", "quantities", "units", "sku", "skus", "restock", "re-stock", "backorder", "back-ordered",
            "timeline", "timelines", "schedule", "schedules", "deadline", "deadlines", "milestone", "milestones",
            "ETA", "ETAs", "when", "date", "dates", "roadmap", "release", "ship", "shipping", "deliver", "delivery",
            "forecast", "forecasts", "predict", "prediction", "predictions", "projection", "projections", "outlook", "trend", "trends",
            "demand", "supply", "price forecast", "capacity"
        ]
        lower_q = prompt.lower()
        is_allowed = any(k in lower_q for k in allowed_keywords)

        if not is_allowed:
            policy_msg = (
                "Sorry — I’m limited to **inventory**, **timelines**, and **future predictions**. "
                "Try asking about availability/stock, schedules/ETAs, or forecasts/projections."
            )
            assistant_msg = {"role": "assistant", "content": policy_msg}
            st.session_state.chat_messages.append(assistant_msg)
            with st.chat_message("assistant"):
                st.markdown(policy_msg)
            DB.log_chat("assistant", policy_msg)
        else:
            # Optional intent helpers before executing the graph
            ctx_msgs = []

            # quick summary intent
            if any(k in lower_q for k in ["summary", "overview", "snapshot", "status"]):
                try:
                    ctx_msgs.append({"role": "system", "content": tool_load_inventory(DATA_PROCESSED)})
                except Exception as e:
                    ctx_msgs.append({"role": "system", "content": f"Inventory summary unavailable: {e}"})

            # simple SKU extraction intent
            m = re.search(r"(?:^|\b)sku\s*[:#]?\s*([\w\-]+)", prompt, flags=re.IGNORECASE)
            if m:
                sku_id = m.group(1)
                try:
                    ctx_msgs.append({"role": "system", "content": tool_lookup_sku(sku_id, DATA_PROCESSED)})
                except Exception as e:
                    ctx_msgs.append({"role": "system", "content": f"Lookup error for SKU {sku_id}: {e}"})

            # gap detection intent: e.g., "gap detect image.jpg"
            g = re.search(r"\bgap\s*(?:detect|detection)\s+(.+)$", prompt, flags=re.IGNORECASE)
            if g:
                image_path = g.group(1).strip().strip('"\'')
                try:
                    ctx_msgs.append({"role": "system", "content": tool_detect_gap(image_path)})
                except Exception as e:
                    ctx_msgs.append({"role": "system", "content": f"Gap detect error for {image_path}: {e}"})

            # reorder plan intent (only if not a specific SKU request)
            if any(k in lower_q for k in ["reorder plan", "reorder", "restock plan", "restock"]) and not m:
                try:
                    ctx_msgs.append({"role": "system", "content": tool_reorder_plan(20, DATA_PROCESSED)})
                except Exception as e:
                    ctx_msgs.append({"role": "system", "content": f"Reorder plan unavailable: {e}"})

            if ctx_msgs:
                st.session_state.chat_messages.extend(ctx_msgs)

            # Execute graph
            state_in: MessagesState = {"messages": st.session_state.chat_messages}
            state_out = app_graph.invoke(state_in)

            # Merge assistant reply
            assistant_msg = state_out["messages"][-1] if state_out.get("messages") else None
            if assistant_msg and assistant_msg.get("role") == "assistant":
                st.session_state.chat_messages.append(assistant_msg)
                with st.chat_message("assistant"):
                    st.markdown(assistant_msg["content"])
                # NEW: persist assistant reply
                DB.log_chat("assistant", assistant_msg["content"])
            else:
                st.error("No response from the model. Check API credentials and model name.")

    with st.expander("ℹ️ Tips & Next Steps", expanded=False):
        st.markdown(
            """
            **Extend this chat:**
            - 🔧 Add tool nodes (e.g., a SKU lookup that reads `inventory_clean.csv` for real-time availability).
            - 🧠 Memory: persist summaries per SKU to enrich future forecasts.
            - 📚 RAG: prepend retrieved inventory rows before the LLM call.
            - ⏱️ Streaming: swap `.invoke` with `.stream` and render tokens incrementally.
            - 🧭 Routing: Add a simple router node to send timeline questions to a different policy.
            - 🗄️ Storage: With DuckDB enabled, inspect data via the CLI:
              ```bash
              duckdb "$DUCKDB_PATH"  # e.g., data/backroom.duckdb
              DESCRIBE SELECT * FROM inventory;
              SELECT COUNT(*) FROM chat_logs;
              ```
            """
        )


# =============================
# --- End of File ---
# =============================
