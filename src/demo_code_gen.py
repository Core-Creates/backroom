#!/usr/bin/env python3
"""
Demo script showing the AI-generated visualization code
"""

import pandas as pd
from agents.visualization_agent import VisualizationAgent
from dotenv import load_dotenv

load_dotenv()

def show_generated_code_demo():
    """Demonstrate the AI code generation capabilities."""
    
    # Sample data
    data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_586', 'FOODS_3_252'],
        'description': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apple'],
        'total_sales': [50170, 37802, 26051]
    })
    
    print("🎨 AI-Powered Visualization Code Generation Demo")
    print("=" * 55)
    
    viz_agent = VisualizationAgent()
    
    # Test request
    question = "create a donut chart with pastel colors showing sales distribution with percentages"
    
    print(f"🤔 Request: '{question}'")
    print("\n🧠 Generating AI code...")
    
    # Generate code
    code = viz_agent.generate_chart_code(question, data)
    
    print("\n🐍 Generated Python Code:")
    print("-" * 30)
    print(code)
    print("-" * 30)
    
    # Execute it
    print("\n🔧 Executing code...")
    query_result = {"success": True, "data": data}
    result = viz_agent.create_visualization(question, query_result)
    
    if result["created"]:
        print(f"✅ Success! Chart saved to: {result['chart_path']}")
        print(f"📊 Chart type: {result['chart_type']}")
    else:
        print(f"❌ Failed: {result['reason']}")

if __name__ == "__main__":
    show_generated_code_demo()