#!/usr/bin/env python3
"""
Multi-Item Inventory Analysis: Which Items Need to be Ordered Soon?

This script analyzes all items to determine reorder priorities.
"""

import sys
import pandas as pd
from datetime import datetime
sys.path.append('/Users/shtabari/Documents/AITX/backroom/seyed-test')

from forecasting_agent import ForecastingAgent
from inventory_management import InventoryManager
from database_manager import DatabaseManager

def find_items_to_reorder():
    """Find which items need to be ordered soon based on inventory analysis."""
    
    results_string = "🔍 ANALYZING ALL ITEMS FOR REORDER NEEDS\n"
    results_string += "=" * 60 + "\n"
    
    # Initialize components
    db_manager = DatabaseManager()
    forecasting_agent = ForecastingAgent(db_manager)
    inventory_manager = InventoryManager(db_manager)
    
    # Get all items with inventory
    results_string += "📊 Getting all items with inventory...\n"
    inventory_query = "SELECT item_id FROM inv ORDER BY item_id"
    inventory_result = db_manager.execute_query(inventory_query)
    
    if not inventory_result.get("success", False):
        error_msg = f"❌ Error getting inventory data: {inventory_result.get('error')}\n"
        print(error_msg)
        return error_msg
    
    all_items = inventory_result["data"]["item_id"].tolist()
    results_string += f"📦 Found {len(all_items)} items with inventory data\n\n"
    
    # Analyze each item
    reorder_analysis = []
    
    for i, item_id in enumerate(all_items, 1):
        print(f"🔍 Analyzing {item_id} ({i}/{len(all_items)})...")
        
        try:
            # Generate forecast for this item
            forecast_df, model = forecasting_agent.generate_forecast(item_id, 30)
            
            # Get inventory insights
            inventory_insights = inventory_manager.generate_inventory_insights(item_id, forecast_df)
            
            if inventory_insights['success']:
                item_details = inventory_insights['item_details']
                coverage = inventory_insights['coverage_analysis']
                reorder = inventory_insights['reorder_analysis']
                financial = inventory_insights['financial_analysis']
                current_inventory = inventory_insights['current_inventory']
                
                # Determine reorder urgency
                urgency_score = 0
                urgency_reasons = []
                
                # Coverage-based urgency
                if coverage['status'] == 'critical':
                    urgency_score += 100
                    urgency_reasons.append(f"CRITICAL: {coverage['coverage_days']} days coverage")
                elif coverage['status'] == 'low':
                    urgency_score += 50
                    urgency_reasons.append(f"LOW: {coverage['coverage_days']} days coverage")
                
                # ROP-based urgency
                if current_inventory <= reorder['reorder_point']:
                    urgency_score += 75
                    urgency_reasons.append(f"Below ROP: {current_inventory} ≤ {reorder['reorder_point']}")
                
                # Financial consideration (low profit margin = lower priority)
                if financial['profit_margin'] < 10:
                    urgency_score -= 20
                    urgency_reasons.append(f"Low margin: {financial['profit_margin']}%")
                
                reorder_analysis.append({
                    'item_id': item_id,
                    'description': item_details['description'],
                    'current_inventory': current_inventory,
                    'coverage_days': coverage['coverage_days'],
                    'coverage_status': coverage['status'],
                    'reorder_point': reorder['reorder_point'],
                    'below_rop': current_inventory <= reorder['reorder_point'],
                    'expected_revenue': financial['expected_revenue'],
                    'profit_margin': financial['profit_margin'],
                    'urgency_score': urgency_score,
                    'urgency_reasons': urgency_reasons,
                    'recommendations': inventory_insights.get('recommendations', [])
                })
                
                print(f"   ✅ Coverage: {coverage['coverage_days']} days, Status: {coverage['status']}")
                
            else:
                print(f"   ❌ Analysis failed: {inventory_insights.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {item_id}: {str(e)}")
    
    results_string += "\n" + "=" * 60 + "\n"
    
    if not reorder_analysis:
        no_analysis_msg = "❌ No successful analyses completed\n"
        print(no_analysis_msg)
        return no_analysis_msg
    
    # Sort by urgency score (highest first)
    reorder_analysis.sort(key=lambda x: x['urgency_score'], reverse=True)
    
    # Build display string
    results_string += "🎯 REORDER PRIORITY ANALYSIS RESULTS\n"
    results_string += "=" * 60 + "\n"
    
    # High priority items (urgency score >= 75)
    high_priority = [item for item in reorder_analysis if item['urgency_score'] >= 75]
    medium_priority = [item for item in reorder_analysis if 25 <= item['urgency_score'] < 75]
    low_priority = [item for item in reorder_analysis if item['urgency_score'] < 25]
    
    if high_priority:
        results_string += "🚨 HIGH PRIORITY - ORDER IMMEDIATELY:\n"
        results_string += "-" * 40 + "\n"
        for item in high_priority:
            results_string += f"📦 {item['item_id']}: {item['description'][:50]}...\n"
            results_string += f"   📊 Stock: {item['current_inventory']:,} units\n"
            results_string += f"   📅 Coverage: {item['coverage_days']} days ({item['coverage_status'].upper()})\n"
            results_string += f"   🔄 ROP: {item['reorder_point']:,} units (Below: {'Yes' if item['below_rop'] else 'No'})\n"
            results_string += f"   💰 Revenue Impact: ${item['expected_revenue']:,.2f}\n"
            results_string += f"   🎯 Reasons: {', '.join(item['urgency_reasons'])}\n"
            if item['recommendations']:
                results_string += f"   💡 Action: {item['recommendations'][0]}\n"
            results_string += "\n"
    
    if medium_priority:
        results_string += "⚠️ MEDIUM PRIORITY - ORDER SOON:\n"
        results_string += "-" * 40 + "\n"
        for item in medium_priority[:3]:  # Show top 3
            results_string += f"📦 {item['item_id']}: {item['description'][:50]}...\n"
            results_string += f"   📅 Coverage: {item['coverage_days']} days, Stock: {item['current_inventory']:,} units\n"
            results_string += f"   🎯 Reasons: {', '.join(item['urgency_reasons']) if item['urgency_reasons'] else 'Moderate priority'}\n\n"
        
        if len(medium_priority) > 3:
            results_string += f"   ... and {len(medium_priority) - 3} more medium priority items\n\n"
    
    if low_priority:
        results_string += f"✅ LOW PRIORITY: {len(low_priority)} items have adequate inventory levels\n\n"
    
    # Summary statistics
    results_string += "📊 SUMMARY STATISTICS:\n"
    results_string += "-" * 25 + "\n"
    results_string += f"🚨 High Priority (Order Now): {len(high_priority)} items\n"
    results_string += f"⚠️ Medium Priority (Order Soon): {len(medium_priority)} items\n"  
    results_string += f"✅ Low Priority (Adequate Stock): {len(low_priority)} items\n"
    
    total_revenue_at_risk = sum(item['expected_revenue'] for item in high_priority)
    results_string += f"💰 Revenue at Risk (High Priority): ${total_revenue_at_risk:,.2f}\n"
    
    # Create simple CSV export
    df_results = pd.DataFrame(reorder_analysis)
    csv_path = f"reorder_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"📄 Detailed results exported to: {csv_path}")

    return results_string

if __name__ == "__main__":
    analysis_summary = find_items_to_reorder()
    print(analysis_summary)