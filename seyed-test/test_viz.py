#!/usr/bin/env python3
"""
Test script for the new AI-powered visualization agent
"""

import pandas as pd
import numpy as np
from visualization_agent import VisualizationAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_visualization_agent():
    """Test the visualization agent with sample data."""
    
    # Create sample data similar to retail data
    sample_data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_586', 'FOODS_3_252', 'FOODS_3_555', 'FOODS_3_123'],
        'description': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apple', 'Strawberry Yogurt', 'Orange Juice'],
        'total_sales': [50170, 37802, 26051, 19234, 15678]
    })
    
    print("📊 Testing AI-Powered Visualization Agent")
    print("=" * 50)
    
    # Initialize agent
    viz_agent = VisualizationAgent()
    
    # Test different types of charts
    test_cases = [
        "create a colorful horizontal bar chart with sales values labeled",
        "make a pie chart showing the distribution",
        "show a vertical bar chart with different colors for each item"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{question}'")
        print("-" * 40)
        
        try:
            # Create mock query result
            query_result = {
                "success": True,
                "data": sample_data
            }
            
            # Generate visualization
            result = viz_agent.create_visualization(question, query_result)
            
            if result["created"]:
                print(f"✅ Success: {result['chart_type']}")
                print(f"📁 Saved to: {result['chart_path']}")
                if 'generated_code' in result:
                    print(f"🐍 Generated {len(result['generated_code'].split('n'))} lines of code")
            else:
                print(f"❌ Failed: {result['reason']}")
                
        except Exception as e:
            print(f"💥 Error: {e}")
    
    print(f"\n🎨 Charts saved to: {viz_agent.output_dir}")

if __name__ == "__main__":
    test_visualization_agent()