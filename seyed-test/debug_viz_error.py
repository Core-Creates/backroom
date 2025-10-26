#!/usr/bin/env python3
"""
Debug script to identify and fix the visualization error.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()
print(f"API key loaded: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")

def debug_visualization_error():
    """Debug the visualization error step by step."""
    
    print("🔍 Debugging Visualization Error...")
    
    try:
        print("\n1. Testing basic imports...")
        from retail_query_graph import RetailDataQueryGraph
        from visualization_agent import VisualizationAgent
        from database_manager import DatabaseManager
        print("✅ All imports successful")
        
        print("\n2. Testing database connection...")
        db = DatabaseManager()
        tables = db.get_all_tables()
        print(f"✅ Database connected - tables: {tables}")
        
        print("\n3. Testing query execution...")
        # Test a simple query first
        result = db.execute_query("SELECT * FROM sales WHERE item_id LIKE '%FOODS_3_090%' LIMIT 10")
        if result["success"]:
            print(f"✅ Query executed - found {len(result['data'])} records")
            print("Sample data:")
            print(result["data"].head())
        else:
            print(f"❌ Query failed: {result['error']}")
            return
        
        print("\n4. Testing visualization agent...")
        viz_agent = VisualizationAgent()
        
        # Test if it should create visualization
        test_question = "plot ice cream sales for last month as time-series"
        should_viz = viz_agent.should_create_visualization(test_question, result)
        print(f"Should create visualization: {should_viz}")
        
        if should_viz:
            print("\n5. Testing chart creation...")
            viz_result = viz_agent.create_visualization(test_question, result)
            print(f"Visualization result: {viz_result}")
        
        print("\n6. Testing full system...")
        query_system = RetailDataQueryGraph()
        
        # Try the problematic query
        test_query = "plot ice cream sales for last month as time-series"
        print(f"Testing query: '{test_query}'")
        
        response = query_system.query(test_query)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_visualization_error()