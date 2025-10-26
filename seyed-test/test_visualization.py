#!/usr/bin/env python3
"""
Test script for the visualization agent.
Creates sample charts to verify functionality.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def create_sample_data():
    """Create sample retail data for testing visualizations."""
    
    # Sample sales trend data
    dates = pd.date_range(start='2025-10-01', end='2025-10-25', freq='D')
    sales_trend_data = pd.DataFrame({
        'date': dates,
        'sale': np.random.randint(300, 800, len(dates)),
        'item_id': 'FOODS_3_090'
    })
    
    # Sample top items data
    top_items_data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_226', 'FOODS_3_252', 'FOODS_3_333', 'FOODS_3_340'],
        'total_sales': [77821, 19238, 13140, 12891, 8247],
        'item_name': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apples', 'Strawberry Yogurt', 'Orange Juice']
    })
    
    # Sample inventory data
    inventory_data = pd.DataFrame({
        'item_id': ['FOODS_3_090', 'FOODS_3_226', 'FOODS_3_252', 'FOODS_3_333', 'FOODS_3_340'],
        'unit': [2102, 562, 932, 700, 1270],
        'item_name': ['Vanilla Ice Cream', 'Whole Milk', 'Red Apples', 'Strawberry Yogurt', 'Orange Juice']
    })
    
    return sales_trend_data, top_items_data, inventory_data

def test_visualizations():
    """Test different visualization types."""
    
    print("🧪 Testing Visualization Agent...")
    
    try:
        from visualization_agent import VisualizationAgent
        
        # Create visualization agent
        viz_agent = VisualizationAgent()
        print("✅ Visualization agent initialized")
        
        # Create sample data
        sales_trend_data, top_items_data, inventory_data = create_sample_data()
        print("✅ Sample data created")
        
        # Test 1: Sales trend chart
        print("\n📈 Testing Sales Trend Chart...")
        trend_result = {
            "success": True,
            "data": sales_trend_data
        }
        
        viz_info = viz_agent.create_visualization(
            "show me sales trend over time", 
            trend_result
        )
        
        if viz_info.get("created"):
            print(f"✅ Sales trend chart created: {viz_info['chart_path']}")
        else:
            print(f"❌ Failed to create trend chart: {viz_info.get('reason', 'Unknown')}")
        
        # Test 2: Top items chart
        print("\n📊 Testing Top Items Chart...")
        top_items_result = {
            "success": True,
            "data": top_items_data
        }
        
        viz_info = viz_agent.create_visualization(
            "show me the top selling items", 
            top_items_result
        )
        
        if viz_info.get("created"):
            print(f"✅ Top items chart created: {viz_info['chart_path']}")
        else:
            print(f"❌ Failed to create top items chart: {viz_info.get('reason', 'Unknown')}")
        
        # Test 3: Inventory distribution
        print("\n📦 Testing Inventory Distribution Chart...")
        inventory_result = {
            "success": True,
            "data": inventory_data
        }
        
        viz_info = viz_agent.create_visualization(
            "show inventory distribution", 
            inventory_result
        )
        
        if viz_info.get("created"):
            print(f"✅ Inventory chart created: {viz_info['chart_path']}")
        else:
            print(f"❌ Failed to create inventory chart: {viz_info.get('reason', 'Unknown')}")
        
        print("\n🎉 All visualization tests completed!")
        print(f"📁 Charts saved in: {viz_agent.output_dir}")
        
        # List created files
        chart_files = list(viz_agent.output_dir.glob("*.png"))
        print(f"\n📋 Created {len(chart_files)} chart files:")
        for file in sorted(chart_files)[-5:]:  # Show last 5 files
            print(f"  • {file.name}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure matplotlib and seaborn are installed")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_visualizations()