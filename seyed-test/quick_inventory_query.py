#!/usr/bin/env python3
"""
Quick Inventory Query Tool

Direct answer to inventory questions without the interactive loop.
"""

import sys
import os
sys.path.append('/Users/shtabari/Documents/AITX/backroom/seyed-test')

from forecasting_agent import ForecastingAgent
from inventory_management import InventoryManager
from database_manager import DatabaseManager
import re

def get_inventory_answer(question: str) -> str:
    """Get direct answer to inventory question."""
    
    # Extract item ID from question
    item_pattern = r'FOODS_\d+_\d+'
    item_match = re.search(item_pattern, question.upper())
    
    if not item_match:
        return "❌ Please specify an item ID (e.g., FOODS_3_090)"
    
    item_id = item_match.group()
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        forecasting_agent = ForecastingAgent(db_manager)
        inventory_manager = InventoryManager(db_manager)
        
        # Get item details
        item_details = inventory_manager.get_item_details(item_id)
        current_inventory = inventory_manager.get_item_inventory(item_id)
        
        if not item_details or current_inventory is None:
            return f"❌ No inventory data found for {item_id}"
        
        # Generate forecast and analysis
        print("🔮 Generating forecast...")
        forecast_df, model = forecasting_agent.generate_forecast(item_id, 30)
        
        print("📊 Analyzing inventory...")
        inventory_insights = inventory_manager.generate_inventory_insights(item_id, forecast_df)
        
        if not inventory_insights['success']:
            return f"❌ Analysis failed: {inventory_insights.get('error', 'Unknown error')}"
        
        # Format comprehensive response
        coverage = inventory_insights['coverage_analysis']
        reorder = inventory_insights['reorder_analysis']
        financial = inventory_insights['financial_analysis']
        
        response = []
        response.append("🎯 INVENTORY ANALYSIS RESULTS")
        response.append("=" * 50)
        response.append(f"📦 Item: {item_details['description']} ({item_id})")
        response.append(f"📊 Current Stock: {current_inventory:,} units")
        response.append("")
        
        response.append("📅 COVERAGE ANALYSIS:")
        response.append(f"   • Days of Cover: {coverage['coverage_days']} days")
        response.append(f"   • Status: {coverage['status'].upper()}")
        response.append(f"   • {coverage['message']}")
        response.append("")
        
        response.append("🔄 REORDER ANALYSIS:")
        response.append(f"   • Reorder Point: {reorder['reorder_point']:,} units")
        response.append(f"   • Lead Time: {item_details['lead_time']} days")
        response.append(f"   • Safety Stock: {reorder['safety_stock']:,} units")
        response.append("")
        
        response.append("💰 FINANCIAL METRICS:")
        response.append(f"   • Expected Revenue: ${financial['expected_revenue']:,.2f}")
        response.append(f"   • Holding Costs: ${financial['holding_cost']:,.2f}")
        response.append(f"   • Gross Profit: ${financial['gross_profit']:,.2f}")
        response.append(f"   • Profit Margin: {financial['profit_margin']}%")
        response.append("")
        
        if inventory_insights.get('recommendations'):
            response.append("🎯 RECOMMENDATIONS:")
            for i, rec in enumerate(inventory_insights['recommendations'], 1):
                response.append(f"   {i}. {rec}")
        
        return "\n".join(response)
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line argument
        question = " ".join(sys.argv[1:])
    else:
        # Default question
        question = "the days of cover for FOODS_3_090 ?"
    
    print(f"🤔 Question: {question}")
    print("")
    
    answer = get_inventory_answer(question)
    print(answer)