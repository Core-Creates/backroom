#!/usr/bin/env python3
"""
Simple test to isolate the graph initialization issue
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Debugging graph initialization...")

try:
    print("1. Testing DatabaseManager...")
    from database_manager import DatabaseManager
    db = DatabaseManager()
    print("   ✅ DatabaseManager OK")
    
    print("2. Testing QueryGeneratorAgent...")
    from query_agents import QueryGeneratorAgent
    qga = QueryGeneratorAgent()
    print("   ✅ QueryGeneratorAgent OK")
    
    print("3. Testing ResponseFormatterAgent...")
    from query_agents import ResponseFormatterAgent  
    rfa = ResponseFormatterAgent()
    print("   ✅ ResponseFormatterAgent OK")
    
    print("4. Testing VisualizationAgent...")
    from visualization_agent import VisualizationAgent
    va = VisualizationAgent(db)
    print("   ✅ VisualizationAgent OK")
    
    print("5. Testing ForecastingAgent...")
    from forecasting_agent import ForecastingAgent
    fa = ForecastingAgent(db)
    print("   ✅ ForecastingAgent OK")
    
    print("6. Testing RetailDataQueryGraph initialization...")
    from retail_query_graph import RetailDataQueryGraph
    
    # Initialize step by step to isolate the issue
    print("   6a. Creating instance...")
    graph = RetailDataQueryGraph()
    print("   ✅ RetailDataQueryGraph initialized successfully!")
    
    print("7. Testing simple query...")
    response = graph.query("show me sales data")
    print("   ✅ Query executed successfully!")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Debug complete!")