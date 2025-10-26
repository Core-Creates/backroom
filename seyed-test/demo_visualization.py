#!/usr/bin/env python3
"""
Demo script showing the new visualization capabilities.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_visualization_queries():
    """Demo various visualization queries."""
    
    print("🎨 LangGraph Retail Data Query System - Visualization Demo")
    print("=" * 65)
    
    example_queries = [
        {
            "query": "plot sales trend over the last week",
            "description": "Creates a line chart showing sales trends over time"
        },
        {
            "query": "show me top 5 selling items in a bar chart",
            "description": "Creates a bar chart of top selling items"
        },
        {
            "query": "make a pie chart for top 3 best sellers",
            "description": "Creates a pie chart showing distribution of top sellers"
        },
        {
            "query": "visualize inventory distribution",
            "description": "Creates charts showing inventory levels across items"
        },
        {
            "query": "plot historical sales data for vanilla ice cream",
            "description": "Shows sales trend for a specific item over time"
        }
    ]
    
    print("📊 VISUALIZATION CAPABILITIES:")
    print()
    
    print("🎯 Chart Types Supported:")
    chart_types = [
        "📈 Line Charts: Sales trends over time, historical data",
        "📊 Bar Charts: Top selling items, comparisons",
        "🥧 Pie Charts: Distribution percentages, market share",
        "📦 Distribution Charts: Inventory levels, stock analysis"
    ]
    
    for chart_type in chart_types:
        print(f"  {chart_type}")
    
    print("\n🔍 Trigger Keywords:")
    trigger_words = [
        "plot, chart, graph, visualize",
        "trend, over time, historical, time-series", 
        "pie, pie chart, distribution, percentage",
        "top, best, highest, most",
        "inventory, stock, distribution"
    ]
    
    for words in trigger_words:
        print(f"  • {words}")
    
    print("\n💡 Example Queries:")
    print()
    
    for i, example in enumerate(example_queries, 1):
        print(f"{i}. \"{example['query']}\"")
        print(f"   → {example['description']}")
        print()
    
    print("🚀 HOW IT WORKS:")
    print()
    
    workflow_steps = [
        "1. User asks question with visualization keywords",
        "2. System generates appropriate SQL query", 
        "3. Query executes against retail database",
        "4. Visualization agent detects chart opportunity",
        "5. Creates appropriate chart (line/bar/pie/distribution)",
        "6. Saves chart as PNG file in visualizations folder",
        "7. Returns natural language response + chart info"
    ]
    
    for step in workflow_steps:
        print(f"  {step}")
    
    print("\n📁 OUTPUT:")
    print("  • Charts saved in: ./visualizations/")
    print("  • High-quality PNG files (300 DPI)")
    print("  • Timestamps in filenames for organization")
    print("  • Professional styling with colors and labels")
    
    print("\n🎯 TRY IT NOW:")
    print("  Run: python main.py")
    print("  Then ask: 'plot the top selling items'")
    print("  Or: 'make a pie chart for inventory distribution'")
    
    print("\n" + "=" * 65)

if __name__ == "__main__":
    demo_visualization_queries()