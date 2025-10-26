#!/usr/bin/env python3
"""
Test just the enhanced analytical response formatting directly
"""

import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from query_agents import ResponseFormatterAgent

def test_analytical_formatting():
    """Test the enhanced analytical response formatting with sample data."""
    
    print("🧪 Testing Enhanced Analytical Response Formatting")
    print("=" * 60)
    
    # Create sample retail data
    sample_sales_data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_586', 'FOODS_3_252', 'FOODS_3_282', 'FOODS_3_555'],
        'description': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apple', 'Chocolate Ice Cream', 'Strawberry Yogurt'],
        'total_sales': [50170, 37802, 28945, 15632, 12890],
        'price': [4.99, 3.49, 2.99, 5.29, 1.99]
    })
    
    # Mock query result
    query_result = {
        "success": True,
        "data": sample_sales_data,
        "row_count": len(sample_sales_data)
    }
    
    # Test query info
    query_info = {
        "query": "SELECT item_id, description, SUM(sale) as total_sales, price FROM sales JOIN item_dim ON sales.item_id = item_dim.item_id GROUP BY item_id, description, price ORDER BY total_sales DESC",
        "explanation": "Get total sales for each item with descriptions and prices"
    }
    
    # Test the formatter
    formatter = ResponseFormatterAgent()
    
    print("📊 Testing Query: 'What are the total sales for each item with their descriptions and prices?'")
    print("-" * 60)
    
    try:
        response = formatter.format_response(
            question="What are the total sales for each item with their descriptions and prices?",
            query_result=query_result,
            query_info=query_info
        )
        
        print("✅ Analytical Response:")
        print(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analytical_formatting()