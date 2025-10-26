# main.py
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# --- Your existing data/logic imports ---
# (These must be available in your environment)
from .retail_query_graph import RetailDataQueryGraph

# Optional/conditional imports used by inventory handler
# (kept inside method to avoid import errors if modules are absent)

# --- FastAPI bits ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <-- ADDED: CORS
from pydantic import BaseModel
from routes.express_to_fastapi import router as items_router

# =========================
# Shared environment setup
# =========================
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in environment variables")
    print("💡 Make sure your .env file contains: OPENAI_API_KEY=your_key_here")
    # We won't exit here because the API might have health endpoints, but
    # CLI and query calls will fail fast if key is missing.

# =========================
# Core Memory-Enabled class
# =========================
class MemoryEnabledMain:
    """Main engine with conversation memory and context awareness."""

    def __init__(self, save_conversations: bool = True):
        self.query_system = RetailDataQueryGraph()
        self.messages: List[BaseMessage] = []
        self.save_conversations = save_conversations
        self.conversation_file = Path("main_conversation_history.json")
        self.load_conversation_history()

    def load_conversation_history(self):
        """Load previous conversation history from file."""
        if self.conversation_file.exists() and self.save_conversations:
            try:
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)

                for msg_data in data.get("messages", []):
                    if msg_data["type"] == "human":
                        self.messages.append(HumanMessage(content=msg_data["content"]))
                    elif msg_data["type"] == "ai":
                        self.messages.append(AIMessage(content=msg_data["content"]))
                if self.messages:
                    print(f"📚 Loaded {len(self.messages)} previous messages")
            except Exception as e:
                print(f"⚠️ Could not load conversation history: {e}")

    def save_conversation_history(self):
        """Save current conversation to file."""
        if not self.save_conversations:
            return
        try:
            serializable_messages = []
            for msg in self.messages:
                if isinstance(msg, HumanMessage):
                    serializable_messages.append({
                        "type": "human",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
                elif isinstance(msg, AIMessage):
                    serializable_messages.append({
                        "type": "ai",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()
                    })

            data = {
                "messages": serializable_messages,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.conversation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save conversation: {e}")

    def get_context_summary(self) -> str:
        """Generate a summary of recent conversation for context."""
        if len(self.messages) < 2:
            return ""
        recent_messages = self.messages[-6:]  # last 3 exchanges
        context = "Previous conversation context:\n"
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                context += f"User: {msg.content[:100]}...\n"
            elif isinstance(msg, AIMessage):
                content = msg.content
                if "KEY FINDINGS" in content:
                    try:
                        key_section = content.split("KEY FINDINGS", 1)[1].split("BUSINESS RECOMMENDATIONS")[0]
                        context += f"AI found: {key_section[:150].strip()}...\n"
                    except Exception:
                        context += "AI: (summary unavailable)\n"
                else:
                    context += f"AI: {content[:100]}...\n"
        return context

    def process_query_with_context(self, user_input: str) -> str:
        """Process query with conversation context."""
        # Special case: multi-item reorder analysis
        multi_item_reorder_keywords = [
            "which items need to be ordered", "reorder priority", "order soon",
            "reorder list", "who needs ordering"
        ]
        if any(keyword in user_input.lower() for keyword in multi_item_reorder_keywords):
            try:
                from reorder_priority_analysis import find_items_to_reorder
                print("🔬 Running multi-item reorder analysis... This may take a moment.")
                return find_items_to_reorder()
            except Exception as e:
                return f"❌ Error during reorder analysis: {e}"

        # Inventory-specific questions with item ID extraction
        inventory_keywords = ["days of cover", "coverage", "inventory", "stock level", "reorder point"]
        is_inventory_question = any(keyword in user_input.lower() for keyword in inventory_keywords)

        import re
        item_pattern = r'FOODS_\d+_\d+'
        item_match = re.search(item_pattern, user_input.upper())

        if is_inventory_question and item_match:
            try:
                return self._handle_inventory_question(user_input, item_match.group())
            except Exception as e:
                print(f"⚠️ Inventory analysis error: {e}")
                # fall through to normal processing

        try:
            # Context-awareness for pronoun-y follow-ups
            context_keywords = ["this", "that", "it", "them", "those", "previous", "last", "above"]
            has_context_reference = any(keyword in user_input.lower() for keyword in context_keywords)

            if has_context_reference and len(self.messages) > 0:
                self.messages.append(HumanMessage(content=user_input))
                updated_messages = self.query_system.chat(self.messages.copy())
                ai_messages = [msg for msg in updated_messages if isinstance(msg, AIMessage)]
                if ai_messages:
                    response = ai_messages[-1].content
                    self.messages.append(AIMessage(content=response))
                    return response

            # Regular processing for new topics
            response = self.query_system.query(user_input)
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(AIMessage(content=response))
            return response

        except Exception as e:
            error_msg = f"❌ Processing error: {str(e)}"
            print(f"🔍 Debug info: {error_msg}")
            return f"Sorry, I encountered an error while processing your question. Error details: {str(e)}"

    def _handle_inventory_question(self, user_input: str, item_id: str) -> str:
        """Handle inventory-related questions directly using enhanced system."""
        from forecasting_agent import ForecastingAgent
        from inventory_management import InventoryManager
        from database_manager import DatabaseManager

        db_manager = DatabaseManager()
        forecasting_agent = ForecastingAgent(db_manager)
        inventory_manager = InventoryManager(db_manager)

        item_details = inventory_manager.get_item_details(item_id)
        current_inventory = inventory_manager.get_item_inventory(item_id)

        if not item_details or current_inventory is None:
            return f"❌ Sorry, I couldn't find inventory data for {item_id}"

        forecast_df, _model = forecasting_agent.generate_forecast(item_id, 30)
        inventory_insights = inventory_manager.generate_inventory_insights(item_id, forecast_df)

        if not inventory_insights.get('success'):
            return f"❌ Sorry, I couldn't analyze inventory for {item_id}: {inventory_insights.get('error', 'Unknown error')}"

        coverage = inventory_insights['coverage_analysis']
        reorder = inventory_insights['reorder_analysis']
        financial = inventory_insights['financial_analysis']

        parts = []
        parts.append(f"📊 **Inventory Analysis for {item_details['description']} ({item_id})**")
        parts.append(f"📦 **Current Stock:** {current_inventory:,} units")
        parts.append(f"📅 **Days of Cover:** {coverage['coverage_days']} days ({coverage['status'].upper()})")
        if coverage.get('cover_until'):
            parts.append(f"📅 **Stock Exhaustion:** {coverage['cover_until']}")
        parts.append(f"🔄 **Reorder Point:** {reorder['reorder_point']:,} units")
        parts.append(f"💰 **Expected Revenue:** ${financial['expected_revenue']:,.2f}")
        parts.append(f"📈 **Profit Margin:** {financial['profit_margin']}%")
        if inventory_insights.get('recommendations'):
            parts.append(f"🎯 **Priority Action:** {inventory_insights['recommendations'][0]}")
        return "\n".join(parts)

    def show_conversation_stats(self) -> dict:
        """Return statistics about the current conversation."""
        human_msgs = len([m for m in self.messages if isinstance(m, HumanMessage)])
        ai_msgs = len([m for m in self.messages if isinstance(m, AIMessage)])
        return {
            "your_questions": human_msgs,
            "ai_responses": ai_msgs,
            "memory": "Enabled" if self.save_conversations else "Disabled"
        }

    def clear_memory(self):
        """Clear conversation history."""
        self.messages = []
        if self.conversation_file.exists():
            self.conversation_file.unlink()
        print("🧹 Conversation memory cleared!")

# =========================
# FastAPI App (merged)
# =========================
app = FastAPI(title="Backroom API + Retail Memory")

# --- CORS (Dev) ---
# Allow local frontends during development. In production, replace with real origins.
_default_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",  # Next.js dev
    "http://localhost:8501", "http://127.0.0.1:8501",  # Streamlit
]
# Comma-separated ORIGINS env override, e.g. "https://app.example.com,https://ops.example.com"
_env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
_allowed_origins = _env_origins or _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount your existing router under /items to mirror Express-style grouping
app.include_router(items_router, prefix="/items")

# Singleton engine for API usage
_engine: Optional[MemoryEnabledMain] = None
_engine_init_error: Optional[str] = None

def get_engine() -> MemoryEnabledMain:
    global _engine, _engine_init_error
    if _engine is None and _engine_init_error is None:
        try:
            _engine = MemoryEnabledMain(save_conversations=True)
        except Exception as e:
            _engine_init_error = f"Initialization error: {e}"
    if _engine_init_error:
        raise HTTPException(status_code=500, detail=_engine_init_error)
    return _engine

# --------- API Schemas ---------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class StatsResponse(BaseModel):
    your_questions: int
    ai_responses: int
    memory: str

# --------- API Routes ----------
@app.get("/health")
def health():
    return {"status": "ok", "openai_key": bool(os.getenv("OPENAI_API_KEY"))}

# --- NEW: simple test route for connectivity checks ---
@app.get("/test")
def test():
    """Simple connectivity test endpoint for frontends / ops tools."""
    return {"ok": True, "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    engine = get_engine()
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not set.")
    result = engine.process_query_with_context(req.message)
    # Auto-save every 2 exchanges (same heuristic)
    if len(engine.messages) % 4 == 0:
        engine.save_conversation_history()
    return ChatResponse(response=result)

@app.get("/stats", response_model=StatsResponse)
def stats():
    engine = get_engine()
    return StatsResponse(**engine.show_conversation_stats())

@app.post("/clear")
def clear():
    engine = get_engine()
    engine.clear_memory()
    engine.save_conversation_history()
    return {"cleared": True}

@app.get("/context")
def context():
    engine = get_engine()
    return {"context": engine.get_context_summary()}

# =========================
# CLI Mode (optional)
# =========================
def cli_main():
    print("🧠 Retail Data Query System (Memory-Enabled)")
    print("=" * 60)
    print("🎯 Features:")
    print("  • 💬 Remembers our conversation")
    print("  • 🔗 Understands follow-up questions")
    print("  • 💾 Saves conversation history")
    print("  • 📊 Full data analysis & visualization")
    print()
    print("Available data: sales, inventory (inv), and item dimensions (item_dim)")
    print()
    print("🗣️ Commands:")
    print("  • 'stats' - Show conversation statistics")
    print("  • 'clear' - Clear conversation memory")
    print("  • 'quit'  - Exit system")
    print("Type 'quit' to exit\n")

    try:
        memory_system = MemoryEnabledMain()
        if len(memory_system.messages) > 0:
            print("👋 Welcome back! I remember our previous conversation.")
            stats = memory_system.show_conversation_stats()
            print(f"📝 Your questions: {stats['your_questions']}")
            print(f"🤖 AI responses: {stats['ai_responses']}")
            print(f"💾 Memory: {stats['memory']}")
        else:
            print("👋 Hello! I'm ready to help with your retail data questions.")
        print("✅ Connected to retail database")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return

    while True:
        try:
            try:
                user_input = input("\n🤔 Your question: ").strip()
            except EOFError:
                print("\n👋 EOF detected. Goodbye!")
                memory_system.save_conversation_history()
                break

            if user_input.lower() in ['quit', 'exit', 'q']:
                memory_system.save_conversation_history()
                print("👋 Goodbye! Conversation saved for next time.")
                break
            elif user_input.lower() == 'stats':
                s = memory_system.show_conversation_stats()
                print("Conversation Stats:")
                print(f"   📝 Your questions: {s['your_questions']}")
                print(f"   🤖 AI responses: {s['ai_responses']}")
                print(f"   💾 Memory: {s['memory']}")
                continue
            elif user_input.lower() == 'clear':
                memory_system.clear_memory()
                continue

            if not user_input:
                continue

            print("� Processing (with memory)...")
            ai_response = memory_system.process_query_with_context(user_input)
            if ai_response and ai_response.strip():
                print(f"\n🤖 {ai_response}")
                if len(memory_system.messages) % 4 == 0:
                    memory_system.save_conversation_history()
            else:
                print("❌ No response generated")

        except KeyboardInterrupt:
            memory_system.save_conversation_history()
            print("\n👋 Goodbye! Conversation saved.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def example_queries():
    examples = [
        "Show me the top 10 selling items",
        "What's the total sales revenue?",
        "How many items are in inventory?",
        "Which items have low stock levels?",
        "Show sales data for the last month",
        "What are the most popular product categories?",
        "Compare sales across different time periods",
        "Show inventory turnover rates",
        "Create a chart for those items",
        "What about their inventory levels?"
    ]

    print("\n💡 Example questions you can ask:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")

    print("\n🔗 Memory Features:")
    print("  • Ask follow-up questions using 'those', 'that', 'them'")
    print("  • Reference previous results with 'it', 'the previous data'")
    print("  • Build conversations naturally with context awareness")

if __name__ == "__main__":
    # Entry strategy:
    # - `python main.py cli`     → run interactive CLI
    # - `python main.py examples`→ print examples
    # - otherwise, importable FastAPI app (use `uvicorn main:app --reload`)
    if len(sys.argv) > 1:
        if sys.argv[1] == "cli":
            cli_main()
        elif sys.argv[1] == "examples":
            example_queries()
        elif sys.argv[1] in ("--help", "-h"):
            print("Merged Backroom API + Retail Memory CLI")
            print("Usage:")
            print("  python main.py cli        # run CLI")
            print("  python main.py examples   # show example queries")
            print("  uvicorn main:app --reload # run FastAPI server")
        else:
            # Unrecognized arg: just print a hint
            print("Unrecognized argument. Try '--help'.")
    else:
        # No CLI launch by default; this file exposes FastAPI app for uvicorn.
        print("💡 FastAPI app ready. Start with: uvicorn main:app --reload")
