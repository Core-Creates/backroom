#!/usr/bin/env python3
"""
Debug script to see exactly what code is being generated
"""

import pandas as pd
from visualization_agent import VisualizationAgent
from dotenv import load_dotenv

load_dotenv()

def debug_generated_code():
    """Debug the generated visualization code."""
    
    # Sample data
    data = pd.DataFrame({
        'item_id': ['FOODS_3_090'],
        'description': ['Vanilla Ice Cream'],
        'total_sales': [50170]
    })
    
    print("🐛 Debugging Generated Code")
    print("=" * 40)
    
    viz_agent = VisualizationAgent()
    
    question = "show best seller in a bar chart"
    
    print(f"Question: {question}")
    print("\n🧠 Generating code...")
    
    # Generate code
    code = viz_agent.generate_chart_code(question, data)
    
    print("\n📝 Generated Code:")
    print("-" * 40)
    print(code)
    print("-" * 40)
    
    print("\n🔍 Looking for datetime issues...")
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if 'datetime' in line:
            print(f"Line {i}: {line}")

if __name__ == "__main__":
    debug_generated_code()