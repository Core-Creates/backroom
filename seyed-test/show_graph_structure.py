#!/usr/bin/env python3
"""
Text-based visualization of the LangGraph workflow.
Shows the graph structure and flow in ASCII format.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def print_graph_structure():
    """Print a text-based representation of the LangGraph workflow."""
    
    print("🛒 LangGraph Retail Data Query Workflow")
    print("=" * 60)
    print()
    
    print("📊 WORKFLOW STRUCTURE:")
    print()
    
    workflow_ascii = """
    ┌─────────────┐
    │    START    │
    └──────┬──────┘
           │ (always)
           ▼
    ┌─────────────────┐
    │ analyze_question│◄─────────────────────────────────────────┐
    └──────┬─────┬────┘                                          │
           │     │                                               │
    (success)   (error)                                          │
           │     └─────────────────┐                             │
           ▼                       │                             │
    ┌─────────────────┐           │                             │
    │ generate_query  │◄──────────┼─────────────────────────────┤
    └──────┬─────┬────┘           │                             │
           │     │                │                             │
    (success)   (error)           │                             │
           │     └────────────────┤                             │
           ▼                      │                             │
    ┌─────────────────┐          │                             │
    │ execute_query   │◄─────────┼─────────────────────────────┤
    └──────┬─────┬────┘          │                             │
           │     │               │                             │
    (success)   (error)          │                             │
           │     └───────────────┤                             │
           ▼                     │                             │
    ┌─────────────────────┐     │                             │
    │ create_visualization│     │                             │
    └──────┬──────────────┘     │                             │
           │ (always)            │                             │
           ▼                     │                             │
    ┌─────────────────┐         │                             │
    │ format_response │         │                             │
    └──────┬──────────┘         │                             │
           │                    │                             │
        (always)                │                             │
           │                    ▼                             │
           │             ┌─────────────┐                      │
           │             │handle_error │──────────────────────┘
           │             └──────┬──────┘
           │                    │ (always)
           │                    │
           ▼                    ▼
         ┌─────────────┐
         │     END     │
         └─────────────┘
    """
    
    print(workflow_ascii)
    print()
    
    print("📋 NODE DESCRIPTIONS:")
    print()
    
    nodes_desc = {
        "🎯 analyze_question": [
            "• Extracts user question from message history",
            "• Loads complete database schema and table descriptions", 
            "• Prepares context for SQL generation",
            "• Handles: sales, inventory (inv), item dimensions (item_dim)"
        ],
        "🧠 generate_query": [
            "• Uses OpenAI GPT-4 to convert natural language to SQL",
            "• Provides database schema context to LLM",
            "• Validates SQL syntax and table/column references",
            "• Returns structured query information with explanations"
        ],
        "⚡ execute_query": [
            "• Executes generated SQL against DuckDB database",
            "• Handles database connections and transactions",
            "• Returns results as pandas DataFrame",
            "• Captures execution errors and performance metrics"
        ],
        "💬 format_response": [
            "• Uses OpenAI GPT-4 to format results into natural language",
            "• Provides context-aware explanations and insights",
            "• Creates conversational, user-friendly responses",
            "• Handles data summaries and key findings presentation"
        ],
        "🎨 create_visualization": [
            "• Detects when charts would enhance the response",
            "• Creates line charts for time-series data (sales trends)",
            "• Generates bar charts for comparisons (top items)",
            "• Produces pie charts for distributions (market share)",
            "• Creates inventory analysis charts with dual views",
            "• Saves high-quality PNG files with professional styling"
        ],
        "❌ handle_error": [
            "• Catches and processes all workflow errors gracefully",
            "• Creates informative error messages for users",
            "• Logs errors for debugging and system monitoring",
            "• Ensures system never crashes on invalid input"
        ]
    }
    
    for node, descriptions in nodes_desc.items():
        print(f"{node}:")
        for desc in descriptions:
            print(f"    {desc}")
        print()
    
    print("🔄 CONDITIONAL FLOW LOGIC:")
    print()
    
    conditions = [
        ("analyze_question → generate_query", "✅ Success: Schema loaded, question parsed"),
        ("analyze_question → handle_error", "❌ Error: Database connection failed, schema loading error"),
        ("generate_query → execute_query", "✅ Success: Valid SQL generated, no syntax errors"),
        ("generate_query → handle_error", "❌ Error: LLM API failure, invalid SQL generated"),
        ("execute_query → create_visualization", "✅ Success: Query executed, results returned"),
        ("execute_query → handle_error", "❌ Error: SQL execution failed, database error"),
        ("create_visualization → format_response", "✅ Always: Charts created (if appropriate), ready for formatting"),
        ("format_response → END", "✅ Always: Response formatted and added to conversation"),
        ("handle_error → END", "🔶 Always: Error message created and system recovered")
    ]
    
    for transition, condition in conditions:
        print(f"  {transition}")
        print(f"    {condition}")
        print()
    
    print("💾 STATE MANAGEMENT:")
    print()
    
    state_fields = {
        "messages": "List[BaseMessage] - Full conversation history",
        "user_question": "str - Current user question being processed",
        "database_schema": "Dict - Complete database schema and metadata",
        "generated_query": "Dict - Generated SQL query with explanations",
        "query_result": "Dict - Execution results with success/error status",
        "final_response": "str - Formatted natural language response",
        "error": "str - Any error messages from processing"
    }
    
    for field, description in state_fields.items():
        print(f"  • {field}: {description}")
    
    print()
    print("🎯 KEY FEATURES:")
    print()
    
    features = [
        "🔍 Natural Language Processing: Converts questions like 'show top selling items' to SQL",
        "🗄️ Multi-table Queries: Automatically joins sales, inventory, and item dimension tables",
        "💡 Intelligent Responses: Provides insights and explanations, not just raw data",
        "🎨 Automatic Visualizations: Creates charts for trends, comparisons, and distributions",
        "� Professional Charts: High-quality line, bar, and pie charts with proper styling",
        "�🛡️ Error Recovery: Gracefully handles all failure scenarios with helpful messages",
        "💬 Conversation Memory: Maintains chat history for follow-up questions",
        "⚡ Real-time Processing: Fast query generation and execution",
        "� File Organization: Charts saved with timestamps in organized directories"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print()
    print("=" * 60)

def show_example_flow():
    """Show an example of how a question flows through the system."""
    
    print("\n🎬 EXAMPLE WORKFLOW EXECUTION:")
    print("Question: 'What are my top selling items?'")
    print()
    
    steps = [
        ("1️⃣ START", "User submits question via main.py CLI"),
        ("2️⃣ analyze_question", "• Extract: 'What are my top selling items?'\n    • Load schema: sales, inv, item_dim tables\n    • Status: ✅ Success"),
        ("3️⃣ generate_query", "• LLM Input: Question + Database schema\n    • Generated SQL: SELECT item_id, SUM(sale) as total_sales FROM sales GROUP BY item_id ORDER BY total_sales DESC LIMIT 10\n    • Status: ✅ Success"),
        ("4️⃣ execute_query", "• Execute SQL on DuckDB\n    • Results: 10 rows with item_id and total_sales\n    • Status: ✅ Success"),
        ("5️⃣ create_visualization", "• Detect keywords: 'top selling items'\n    • Create bar chart with top 10 items\n    • Save as: top_items_20251025_133041.png\n    • Status: ✅ Success"),
        ("6️⃣ format_response", "• LLM formats results into natural language\n    • Add chart information to response\n    • Response: 'Here are your top selling items... [Chart Created]'\n    • Status: ✅ Success"),
        ("7️⃣ END", "Return formatted response with chart info to user")
    ]
    
    for step, description in steps:
        print(f"{step}: {description}")
        print()

if __name__ == "__main__":
    print_graph_structure()
    show_example_flow()