"""
Test the enhanced forecasting and inventory management integration.
"""

import os
import sys

# Add current directory to path
sys.path.append('/Users/shtabari/Documents/AITX/backroom/seyed-test')

from database_manager import DatabaseManager
from forecasting_agent import ForecastingAgent
from inventory_management import InventoryManager

def test_inventory_integration():
    """Test the inventory management integration with forecasting."""
    
    print("🧪 Testing Enhanced Forecasting with Inventory Management")
    print("=" * 60)
    
    # Initialize components
    db_manager = DatabaseManager()
    forecasting_agent = ForecastingAgent(db_manager)
    inventory_manager = InventoryManager(db_manager)
    
    # Test item
    item_id = "FOODS_3_090"  # Vanilla Ice Cream
    
    print(f"📦 Testing item: {item_id}")
    
    # 1. Test standalone forecasting
    print("\n1️⃣ Testing Standalone Forecasting...")
    forecast_result = forecasting_agent.process_forecast_request(
        "forecast vanilla ice cream for 30 days",
        include_inventory_analysis=False
    )
    
    if forecast_result['success']:
        print("✅ Forecasting successful")
        print(f"   📊 Forecast days: {forecast_result['forecast_days']}")
        print(f"   📈 Data points: {len(forecast_result['forecast_data'])}")
    else:
        print(f"❌ Forecasting failed: {forecast_result.get('error', 'Unknown error')}")
        return
    
    # 2. Test standalone inventory analysis
    print("\n2️⃣ Testing Standalone Inventory Analysis...")
    inventory_result = inventory_manager.process_inventory_request(
        item_id, 
        forecast_result['forecast_data']
    )
    
    if inventory_result['success']:
        print("✅ Inventory analysis successful")
        print(f"   📦 Current inventory: {inventory_result['current_inventory']:,} units")
        print(f"   📅 Coverage: {inventory_result['coverage_analysis']['coverage_days']} days")
        print(f"   🔄 Reorder point: {inventory_result['reorder_analysis']['reorder_point']:,} units")
        print(f"   💰 Expected revenue: ${inventory_result['financial_analysis']['expected_revenue']:,.2f}")
    else:
        print(f"❌ Inventory analysis failed: {inventory_result.get('error', 'Unknown error')}")
    
    # 3. Test integrated forecasting with inventory
    print("\n3️⃣ Testing Integrated Forecasting with Inventory...")
    integrated_result = forecasting_agent.process_forecast_request(
        "forecast vanilla ice cream sales and analyze inventory for 30 days",
        include_inventory_analysis=True
    )
    
    if integrated_result['success']:
        print("✅ Integrated analysis successful")
        print(f"   🔮 Forecast available: {'forecast_data' in integrated_result}")
        print(f"   📦 Inventory analysis available: {'inventory_analysis' in integrated_result}")
        
        if integrated_result.get('inventory_analysis'):
            inv_success = integrated_result['inventory_analysis'].get('success', False)
            print(f"   📊 Inventory analysis success: {inv_success}")
            
            if inv_success:
                recommendations = integrated_result['inventory_analysis'].get('recommendations', [])
                print(f"   🎯 Recommendations: {len(recommendations)} provided")
        
        # Show the response text (truncated)
        response_text = integrated_result.get('response_text', '')
        if response_text:
            lines = response_text.split('\n')
            print(f"\n📝 Response Preview ({len(lines)} lines):")
            for i, line in enumerate(lines[:10]):  # Show first 10 lines
                print(f"   {line}")
            if len(lines) > 10:
                print(f"   ... ({len(lines) - 10} more lines)")
        
    else:
        print(f"❌ Integrated analysis failed: {integrated_result.get('error', 'Unknown error')}")
    
    # 4. Test the specific code from notebook
    print("\n4️⃣ Testing Notebook Code Integration...")
    
    # Get forecast data
    forecast_df = integrated_result['forecast_data']
    
    # Extract the specific insights (matching your notebook code)
    fcst = forecast_df[['ds', 'yhat']].copy()
    fcst['cum_demand'] = fcst['yhat'].cumsum()
    
    # Get inventory and item details
    current_inventory = inventory_manager.get_item_inventory(item_id)
    item_details = inventory_manager.get_item_details(item_id)
    
    if current_inventory and item_details:
        # Calculate coverage day
        cover_day = fcst.loc[fcst['cum_demand'] >= current_inventory, 'ds'].min()
        print(f"   📅 Inventory will cover until: {cover_day}")
        
        # Financial calculations
        price = item_details['price']
        holding_cost = 0.5 * item_details['holding_cost']
        
        total_demand = fcst['yhat'].sum()
        sales = min(current_inventory, total_demand)
        revenue = sales * price
        
        # Approximate daily inventory (on-hand declining by demand)
        fcst['inventory'] = current_inventory - fcst['cum_demand']
        fcst['inventory'] = fcst['inventory'].clip(lower=0)
        
        holding = (fcst['inventory'].mean() * holding_cost * len(fcst))
        
        print(f"   💰 Expected revenue: ${revenue:.2f}")
        print(f"   💸 Estimated holding cost: ${holding:.2f}")
        print(f"   📊 Gross profit: ${revenue - holding:.2f}")
        
        print("\n✅ All notebook code integrated successfully!")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   Item: {item_details['description']}")
        print(f"   Current Stock: {current_inventory:,} units")
        print(f"   Forecast Period: {len(fcst)} days")
        print(f"   Expected Sales: {sales:.0f} units")
        print(f"   Revenue: ${revenue:.2f}")
        print(f"   Holding Cost: ${holding:.2f}")
        print(f"   Net Profit: ${revenue - holding:.2f}")
        
    else:
        print("❌ Could not retrieve inventory or item details")

if __name__ == "__main__":
    test_inventory_integration()