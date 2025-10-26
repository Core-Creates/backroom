#!/usr/bin/env python3
"""
Test the enhanced analytical response formatting
"""

import os
from dotenv import load_dotenv
load_dotenv()

from retail_query_graph import RetailDataQueryGraph

def test_analytical_responses():
    """Test queries that will showcase the enhanced analytical capabilities."""
    
    print("🧪 Testing Enhanced Analytical Response System")
    print("=" * 60)
    
    system = RetailDataQueryGraph()
    
    test_queries = [
        "What are the total sales for each item?",
        "Show me the top 5 selling items",
        "What is the inventory level for each item?",
        "Compare sales between different food items"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 50)
        
        try:
            response = system.query(query)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_analytical_responses()