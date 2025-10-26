#!/usr/bin/env python3
"""
Simple demo without LangGraph dependencies.
Demonstrates basic functionality using hardcoded queries.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_without_llm():
    """Demo the system without LLM dependencies."""
    
    print("🛒 Retail Data Query Demo (No LLM Required)")
    print("=" * 60)
    
    try:
        # Import only the database manager
        from database_manager import DatabaseManager
        
        print("✅ Initializing database connection...")
        db = DatabaseManager()
        
        # Get available tables
        tables = db.get_all_tables()
        print(f"📦 Available tables: {', '.join(tables)}")
        
        # Demo queries with natural language descriptions
        demo_queries = [
            {
                "question": "How many total sales records do we have?",
                "query": "SELECT COUNT(*) as total_sales FROM sales",
                "description": "Counting all sales records"
            },
            {
                "question": "How many items are in our inventory?", 
                "query": "SELECT COUNT(*) as total_inventory_items FROM inv",
                "description": "Counting inventory items"
            },
            {
                "question": "How many different items do we sell?",
                "query": "SELECT COUNT(*) as total_item_types FROM item_dim", 
                "description": "Counting item types in our catalog"
            },
            {
                "question": "Show me a sample of sales data",
                "query": "SELECT * FROM sales LIMIT 5",
                "description": "Getting sample sales records"
            },
            {
                "question": "Show me inventory sample",
                "query": "SELECT * FROM inv LIMIT 3",
                "description": "Getting sample inventory records"  
            }
        ]
        
        print("\n🔍 Running demo queries...")
        
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n{i}. Question: {demo['question']}")
            print(f"   SQL: {demo['query']}")
            print(f"   {demo['description']}...")
            
            result = db.execute_query(demo['query'])
            
            if result["success"]:
                data = result["data"]
                if len(data) == 1 and len(data.columns) == 1:
                    # Single value result
                    print(f"   ✅ Answer: {data.iloc[0, 0]}")
                else:
                    # Multiple rows/columns
                    print(f"   ✅ Found {len(data)} records:")
                    print(data.to_string(index=False, max_rows=5))
            else:
                print(f"   ❌ Error: {result['error']}")
        
        # Interactive simple query mode
        print("\n" + "=" * 60)
        print("🎮 Interactive Mode - Try some simple queries!")
        print("Type 'help' for examples, 'quit' to exit")
        
        while True:
            try:
                user_input = input("\n💭 Enter a SQL query (or question keyword): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n💡 Try these keywords or SQL queries:")
                    print("- 'sales count' or 'SELECT COUNT(*) FROM sales'")
                    print("- 'inventory sample' or 'SELECT * FROM inv LIMIT 3'")
                    print("- 'item types' or 'SELECT COUNT(*) FROM item_dim'")
                    print("- Any valid SQL query")
                    continue
                
                if not user_input:
                    continue
                
                # Simple keyword mapping
                query_map = {
                    'sales count': "SELECT COUNT(*) as total_sales FROM sales",
                    'inventory count': "SELECT COUNT(*) as total_inventory FROM inv", 
                    'item count': "SELECT COUNT(*) as total_items FROM item_dim",
                    'sales sample': "SELECT * FROM sales LIMIT 5",
                    'inventory sample': "SELECT * FROM inv LIMIT 3",
                    'item sample': "SELECT * FROM item_dim LIMIT 3"
                }
                
                # Check if it's a keyword
                query = query_map.get(user_input.lower(), user_input)
                
                print(f"🔍 Executing: {query}")
                result = db.execute_query(query)
                
                if result["success"]:
                    data = result["data"]
                    print(f"✅ Found {len(data)} records")
                    print(data.to_string(index=False, max_rows=10))
                else:
                    print(f"❌ Error: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure DuckDB and pandas are installed:")
        print("   pip install duckdb pandas")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_without_llm()