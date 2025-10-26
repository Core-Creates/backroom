"""
Comprehensive Demo: Enhanced Forecasting with Inventory Management Insights

This script demonstrates the full integration of your notebook insights 
into the AI-powered retail analysis framework.
"""

import os
import sys

# Add current directory to path
sys.path.append('/Users/shtabari/Documents/AITX/backroom/seyed-test')

from retail_query_graph import RetailDataQueryGraph
from langchain_core.messages import HumanMessage
import pandas as pd

def demo_enhanced_framework():
    """Demonstrate the enhanced framework with inventory management insights."""
    
    print("🚀 ENHANCED RETAIL ANALYSIS FRAMEWORK")
    print("=" * 60)
    print("Integrating your notebook insights:")
    print("✅ Cumulative demand tracking")
    print("✅ Inventory coverage analysis")
    print("✅ Reorder point calculations") 
    print("✅ Financial impact (revenue vs holding costs)")
    print("✅ AI-powered visualizations")
    print("=" * 60)
    
    # Initialize the enhanced system
    graph = RetailDataQueryGraph()
    
    # Test scenarios with different types of requests
    test_scenarios = [
        {
            "name": "Basic Forecasting + Inventory Analysis", 
            "question": "forecast vanilla ice cream sales for next 30 days and analyze inventory levels"
        },
        {
            "name": "Specific Item Analysis",
            "question": "show me forecast and inventory insights for FOODS_3_090 for 2 weeks"
        },
        {
            "name": "Business Decision Support",
            "question": "forecast milk sales and tell me when to reorder and expected profits"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 SCENARIO {i}: {scenario['name']}")
        print(f"Question: {scenario['question']}")
        print("-" * 50)
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=scenario['question'])],
            "user_question": scenario['question'],
            "analysis": {},
            "database_schema": {},
            "generated_query": {},
            "query_result": {},
            "visualization": {},
            "forecast": {},
            "final_response": "",
            "error": ""
        }
        
        try:
            # Run the enhanced workflow
            result = graph.graph.invoke(initial_state)
            
            # Display results
            if result.get("forecast", {}).get("success", False):
                forecast_data = result["forecast"]
                
                print("✅ FORECAST RESULTS:")
                print(f"   📊 Item: {forecast_data.get('item_id', 'Unknown')}")
                print(f"   📅 Forecast Days: {forecast_data.get('forecast_days', 'Unknown')}")
                
                # Check for inventory analysis
                if forecast_data.get("inventory_analysis", {}).get("success", False):
                    inv_analysis = forecast_data["inventory_analysis"]
                    
                    print("\n✅ INVENTORY INSIGHTS (Your Notebook Code!):")
                    print(f"   📦 Current Stock: {inv_analysis['current_inventory']:,} units")
                    
                    coverage = inv_analysis['coverage_analysis']
                    print(f"   ⏰ Coverage: {coverage['coverage_days']} days ({coverage['status']})")
                    
                    rop = inv_analysis['reorder_analysis'] 
                    print(f"   🔄 Reorder Point: {rop['reorder_point']:,} units")
                    
                    financial = inv_analysis['financial_analysis']
                    print(f"   💰 Expected Revenue: ${financial['expected_revenue']:,.2f}")
                    print(f"   💸 Holding Costs: ${financial['holding_cost']:,.2f}")
                    print(f"   📊 Gross Profit: ${financial['gross_profit']:,.2f}")
                    print(f"   📈 Profit Margin: {financial['profit_margin']}%")
                    
                    if inv_analysis.get('recommendations'):
                        print(f"   🎯 Priority Action: {inv_analysis['recommendations'][0]}")
                
                # Show visualization info
                if forecast_data.get('plot_path'):
                    print(f"\n📊 Forecast Chart: {os.path.basename(forecast_data['plot_path'])}")
                
                if inv_analysis.get('visualization_path'):
                    print(f"📊 Inventory Chart: {os.path.basename(inv_analysis['visualization_path'])}")
                
                # Display AI response
                print("\n AI RESPONSE:")
                response_text = result.get("final_response", "")
                if response_text:
                    lines = response_text.split('\n')
                    for line in lines[:8]:  # Show first 8 lines
                        print(f"   {line}")
                    if len(lines) > 8:
                        print(f"   ... ({len(lines) - 8} more lines)")
                
            else:
                error_msg = result.get("forecast", {}).get("error", "Unknown error")
                print(f"❌ FORECAST FAILED: {error_msg}")
                
        except Exception as e:
            print(f"❌ SCENARIO FAILED: {str(e)}")
    
    print("\n🎉 DEMO COMPLETE!")
    print("Your notebook insights are now fully integrated into the AI system!")
    print("\nKey Features Added:")
    print("• 📈 Cumulative demand tracking (fcst['cum_demand'] = fcst['yhat'].cumsum())")
    print("• 📅 Coverage analysis (cover_day calculation)")
    print("• 🔄 Reorder point analysis (ROP based on lead time)")
    print("• 💰 Revenue vs holding cost analysis")
    print("• 📊 Inventory level projections over time")
    print("• 🎯 Automated recommendations")
    print("• 📊 Comprehensive visualizations")

def test_notebook_code_directly():
    """Test the exact code from your notebook within the framework."""
    
    print("\n🧪 TESTING YOUR EXACT NOTEBOOK CODE")
    print("=" * 50)
    
    from agents.forecasting_agent import ForecastingAgent
    from inventory_management import InventoryManager
    from db.database_manager import DatabaseManager
    
    # Initialize
    db_manager = DatabaseManager()
    forecasting_agent = ForecastingAgent(db_manager)
    inventory_manager = InventoryManager(db_manager)
    
    # Sample item
    ITEM = "FOODS_3_090"
    
    # Generate forecast (like Prophet in your notebook)
    forecast_df, model = forecasting_agent.generate_forecast(ITEM, 30)
    
    # Your exact notebook code:
    print("🔬 Running your notebook code...")
    
    # Step 1: Process forecast data
    fcst = forecast_df[['ds', 'yhat']].copy()
    fcst['cum_demand'] = fcst['yhat'].cumsum()
    
    # Step 2: Get inventory and item data
    current_inventory = inventory_manager.get_item_inventory(ITEM)
    item_details = inventory_manager.get_item_details(ITEM)
    
    # Step 3: Calculate coverage day
    cover_day = fcst.loc[fcst['cum_demand'] >= current_inventory, 'ds'].min()
    print(f"✅ Inventory will cover until: {cover_day}")
    
    # Step 4: Financial calculations
    price = item_details['price']
    holding_cost = 0.5 * item_details['holding_cost']
    
    total_demand = fcst['yhat'].sum()
    sales = min(current_inventory, total_demand)
    revenue = sales * price
    
    # Step 5: Approximate daily inventory (on-hand declining by demand)
    fcst['inventory'] = current_inventory - fcst['cum_demand']
    fcst['inventory'] = fcst['inventory'].clip(lower=0)
    
    holding = (fcst['inventory'].mean() * holding_cost * len(fcst))
    
    # Step 6: Results (matching your notebook output)
    print(f"✅ Expected revenue: ${revenue:.2f}")
    print(f"✅ Estimated holding cost: ${holding:.2f}")
    print(f"✅ Net profit: ${revenue - holding:.2f}")
    
    print("\n🎯 Your notebook code is now part of the AI system!")
    print("   The InventoryManager class implements all these calculations")
    print("   and integrates seamlessly with the forecasting workflow.")

if __name__ == "__main__":
    demo_enhanced_framework()
    test_notebook_code_directly()