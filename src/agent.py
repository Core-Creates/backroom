# backroom/src/agent.py
from __future__ import annotations
from typing import TypedDict, Literal, List, Optional
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langchain_openai import ChatOpenAI

# --- Backroom domain helpers (reuse your modules)
from cleaning import clean_inventory_df
from forcast import compute_reorder_plan
from detect import detect_shelf_gaps

DATA_PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

# --------------------------
# Tools (callable functions)
# --------------------------

def tool_load_inventory() -> str:
    """Load processed inventory CSV and return a short KPI summary."""
    fp = DATA_PROCESSED / "inventory_clean.csv"
    if not fp.exists():
        return "No processed inventory found. Please upload/clean data first."
    df = pd.read_csv(fp)
    summary = {
        "rows": len(df),
        "unique_sku": int(df["sku"].nunique()),
        "total_on_hand": int(df["on_hand"].sum()),
        "avg_daily_sales_mean": round(float(df["avg_daily_sales"].mean()), 3),
    }
    return f"Inventory summary: {summary}"

def tool_reorder_plan(top_n: int = 20) -> str:
    """Compute reorder plan and return top N rows as CSV snippet."""
    fp = DATA_PROCESSED / "inventory_clean.csv"
    if not fp.exists():
        return "No processed inventory found. Please upload/clean data first."
    df = pd.read_csv(fp)
    plan = compute_reorder_plan(df)
    plan = plan.sort_values("reorder_qty", ascending=False).head(top_n)
    return plan.to_csv(index=False)

def tool_detect_gap(image_path: str) -> str:
    """Run simple shelf-gap heuristic on an uploaded image path."""
    res = detect_shelf_gaps(Path(image_path))
    return f"gap_score={res.get('gap_score')}, notes={res.get('notes')}"

# --------------------------
# LangGraph: Agent with tools
# --------------------------

class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AgentState(TypedDict):
    messages: List[Msg]   # chat history

def build_agent():
    # Wrap your tools so LangGraph can call them
    from langchain.tools import tool

    @tool("load_inventory")
    def _load_inventory():
        """Summarize the current processed inventory dataset."""
        return tool_load_inventory()

    @tool("reorder_plan")
    def _reorder_plan(top_n: int = 20):
        """Compute reorder recommendations and return top N CSV rows."""
        return tool_reorder_plan(top_n=top_n)

    @tool("detect_gap")
    def _detect_gap(image_path: str):
        """Detect shelf gaps in an image on disk."""
        return tool_detect_gap(image_path)

    tools = [_load_inventory, _reorder_plan, _detect_gap]

    # LLM (set OPENAI_API_KEY in env at runtime)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # choose your model

    # Prebuilt ReAct agent that knows how to call tools
    agent = create_react_agent(llm, tools)

    # LangGraph wiring: LLM node + Tool node with conditional branch
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    graph.add_edge("agent", END)
    return graph.compile()
