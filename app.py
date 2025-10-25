"""
Backroom — Inventory Intelligence + Chatbot (Streamlit + LangGraph)
------------------------------------------------------------------
Single-file Streamlit app that provides:
1) Inventory workflow (overview → upload/clean → reorder forecast → shelf-gaps demo)
2) A guarded chatbot powered by LangGraph that ONLY answers about:
   - Inventory (stock, availability, quantities),
   - Timelines (schedules, deadlines, ETAs, roadmaps), and
   - Future predictions (forecasts, projections, outlooks, trends).

Run locally
----------
# 1) Install deps
pip install -U streamlit langgraph openai typing_extensions pydantic pandas

# 2) Your project utilities (expected in ./src)
#    src/utils.py  -> ensure_dirs, get_data_paths, logger
#    src/cleaning.py -> clean_inventory_df, save_cleaned_inventory
#    src/forecast.py -> compute_reorder_plan
#    src/detect.py   -> detect_shelf_gaps

# 3) Environment
export OPENAI_API_KEY="sk-..."              # or setx on Windows
# Optional for OpenAI-compatible endpoints:
# export OPENAI_BASE_URL="https://your.endpoint/v1"
# Optional model override:
# export OPENAI_MODEL="gpt-4o-mini"
# export MODEL_TEMPERATURE="0.4"

# 4) Launch
streamlit run app.py
"""

from __future__ import annotations

# --- Standard libs ---
import os
import re

from pathlib import Path
from typing import Annotated, TypedDict, List

# --- Third party ---
import streamlit as st
import pandas as pd
from openai import OpenAI


# --- LangGraph ---
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# --- Project utils (user-provided) ---
from src.utils import ensure_dirs, get_data_paths
from src.cleaning import clean_inventory_df, save_cleaned_inventory
from src.forecast import compute_reorder_plan
from src.detect import detect_shelf_gaps

# ------ Project tools (reused in agent) ------
from src.tools import tool_load_inventory, tool_lookup_sku, tool_reorder_plan

# =============================
# Streamlit App Configuration
# =============================
st.set_page_config(page_title="Backroom — Inventory Intelligence", layout="wide")
st.title("Backroom — Inventory Intelligence")

# Prepare data directories and known paths
ensure_dirs()
DATA_RAW, DATA_PROCESSED, SHELVES = get_data_paths()

# =============================
# Sidebar & Navigation
# =============================
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Upload & Clean", "Forecast", "Shelf Gaps (Vision)", "Chat"],
)

# =============================
# Pages 1–4: Inventory Workflow
# =============================
if page == "Overview":
    st.subheader("Processed Inventory Snapshot")
    processed_fp = DATA_PROCESSED / "inventory_clean.csv"
    if processed_fp.exists():
        df = pd.read_csv(processed_fp)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Unique SKUs", df["sku"].nunique())
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
    imgs = st.file_uploader("Shelf images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if imgs:
        results = []
        for f in imgs:
            # Save to shelves/ and run stub detector
            out = SHELVES / f.name
            out.write_bytes(f.read())
            gaps = detect_shelf_gaps(out)
            results.append(
                {
                    "image": f.name,
                    "gap_score": gaps.get("gap_score", 0.0),
                    "notes": gaps.get("notes", ""),
                }
            )
        st.dataframe(pd.DataFrame(results), use_container_width=True)

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
            "Env vars respected: OPENAI_API_KEY, OPENAI_BASE_URL (optional), OPENAI_MODEL, MODEL_TEMPERATURE"
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
            """
        )


# =============================
# --- End of File ---
# =============================
