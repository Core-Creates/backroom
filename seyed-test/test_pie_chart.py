#!/usr/bin/env python3
"""
Simple test for the visualization functionality.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🧪 Testing Visualization Integration...")
    
    try:
        from retail_query_graph import RetailDataQueryGraph
        
        # Initialize the system
        query_system = RetailDataQueryGraph()
        print("✅ System initialized with visualization agent")
        
        # Test a visualization query
        test_query = "make a pie chart for top 3 best sellers"
        print(f"\n🔍 Testing query: '{test_query}'")
        
        response = query_system.query(test_query)
        print(f"\n🤖 Response:\n{response}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()