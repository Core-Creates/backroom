#!/usr/bin/env python3
"""
Complete test of the AI-powered visualization system
"""

import pandas as pd
from visualization_agent import VisualizationAgent
from dotenv import load_dotenv

load_dotenv()

def complete_test():
    """Complete test showing all capabilities."""
    
    print("🎨 Complete AI Visualization System Test")
    print("=" * 50)
    
    # Sample retail data
    data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_586', 'FOODS_3_252', 'FOODS_3_555', 'FOODS_3_123'],
        'description': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apple', 'Strawberry Yogurt', 'Orange Juice'],
        'total_sales': [50170, 37802, 26051, 19234, 15678],
        'inventory': [2102, 1270, 891, 767, 623]
    })
    
    viz_agent = VisualizationAgent()
    
    # Test different chart types
    test_requests = [
        "create a rainbow colored horizontal bar chart with sales numbers on bars",
        "make a donut chart with pastel colors showing sales distribution",
        "show a scatter plot of inventory vs sales with bubble sizes",
        "create a multi-color stacked bar comparing sales and inventory"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🎯 Test {i}: {request}")
        print("-" * 60)
        
        try:
            # Mock query result
            query_result = {"success": True, "data": data}
            
            # Generate visualization
            result = viz_agent.create_visualization(request, query_result)
            
            if result["created"]:
                print(f"✅ Success: {result['chart_type']}")
                print(f"📁 File: {result['chart_path']}")
                
                # Show generated code (first 10 lines)
                code_lines = result.get('generated_code', '').split('\n')[:10]
                print("🐍 Generated Code Preview:")
                for line in code_lines:
                    print(f"   {line}")
                if len(result.get('generated_code', '').split('\n')) > 10:
                    print("   ... (truncated)")
            else:
                print(f"❌ Failed: {result['reason']}")
                
        except Exception as e:
            print(f"💥 Error: {e}")
        
        print("-" * 60)
    
    print(f"\n🎨 All charts saved to: {viz_agent.output_dir}")
    print("✨ AI-Powered Visualization System Test Complete!")

if __name__ == "__main__":
    complete_test()