#!/usr/bin/env python3

"""
Quick Demo: Enhanced Forecasting with Inventory Management

Run this script to see your notebook insights in action!
"""

import os
import sys

# Add current directory to path
sys.path.append('/Users/shtabari/Documents/AITX/backroom/seyed-test')

from forecasting_agent import ForecastingAgent
from inventory_management import InventoryManager
from database_manager import DatabaseManager

def quick_demo():
    """Quick demonstration of enhanced capabilities."""
    
    print("🎯 QUICK DEMO: Your Notebook Code in Action!")
    print("=" * 55)
    
    # Initialize components
    db_manager = DatabaseManager()
    forecasting_agent = ForecastingAgent(db_manager)
    inventory_manager = InventoryManager(db_manager)
    
    # Test with vanilla ice cream
    item_id = "FOODS_3_090"
    
    print(f"📦 Item: {item_id} (Vanilla Ice Cream)")
    print("🔮 Generating forecast with inventory insights...")
    
    # This one call does everything from your notebook + more!
    result = forecasting_agent.process_forecast_request(
        "forecast vanilla ice cream for 30 days with inventory analysis"
    )
    
    if result['success']:
        print("\n✅ SUCCESS! Here's what your framework now provides:")
        print("-" * 55)
        
        # Basic forecast info
        print(f"📊 Forecast Days: {result['forecast_days']}")
        
        # Inventory insights (your notebook code integrated!)
        if result.get('inventory_analysis', {}).get('success'):
            inv = result['inventory_analysis']
            
            print(f"📦 Current Stock: {inv['current_inventory']:,} units")
            print(f"⏰ Coverage: {inv['coverage_analysis']['coverage_days']} days")
            print(f"🔄 Reorder Point: {inv['reorder_analysis']['reorder_point']:,} units")
            print(f"💰 Expected Revenue: ${inv['financial_analysis']['expected_revenue']:,.2f}")
            print(f"💸 Holding Costs: ${inv['financial_analysis']['holding_cost']:,.2f}")
            print(f"📊 Net Profit: ${inv['financial_analysis']['gross_profit']:,.2f}")
            print(f"📈 Profit Margin: {inv['financial_analysis']['profit_margin']}%")
            
            if inv.get('recommendations'):
                print(f"🎯 Recommendation: {inv['recommendations'][0]}")
            
            # Show files created
            if result.get('plot_path'):
                print(f"📊 Forecast Chart: {os.path.basename(result['plot_path'])}")
            if inv.get('visualization_path'):
                print(f"📊 Inventory Chart: {os.path.basename(inv['visualization_path'])}")
        
        print("\n" + "=" * 55)
        print("🎉 Your notebook insights are now FULLY INTEGRATED!")
        print("   • Cumulative demand tracking ✅")
        print("   • Coverage day calculations ✅") 
        print("   • Revenue vs holding costs ✅")
        print("   • Reorder point analysis ✅")
        print("   • AI-powered recommendations ✅")
        print("   • Comprehensive visualizations ✅")
        
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

def usage_examples():
    """Show different ways to use the enhanced system."""
    
    print(f"\n📚 USAGE EXAMPLES")
    print("=" * 55)
    
    print("1️⃣ Command Line (main.py):")
    print("   python main.py")
    print('   > "forecast milk for 2 weeks and analyze inventory"')
    
    print("\n2️⃣ Memory-Enabled CLI (memory_cli.py):")  
    print("   python memory_cli.py")
    print('   > "forecast vanilla ice cream for 30 days"')
    print('   > "what about the inventory situation?"')  # Follow-up works!
    
    print("\n3️⃣ Programmatic Usage:")
    print("   from forecasting_agent import ForecastingAgent")
    print("   agent = ForecastingAgent(db_manager)")
    print('   result = agent.process_forecast_request("forecast FOODS_3_090")')
    
    print("\n4️⃣ Direct Inventory Analysis:")
    print("   from inventory_management import InventoryManager")
    print("   manager = InventoryManager(db_manager)")
    print("   insights = manager.process_inventory_request(item_id, forecast_df)")
    
    print(f"\n🔥 ALL YOUR NOTEBOOK CODE IS NOW AUTOMATED! 🔥")

if __name__ == "__main__":
    quick_demo()
    usage_examples()