"""
Inventory Management Module

This module provides inventory insights based on forecasting results.
It calculates key inventory metrics like coverage days, reorder points,
expected revenue, and holding costs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings

from db.database_manager import DatabaseManager

warnings.filterwarnings('ignore')


class InventoryManager:
    """
    Inventory management system that provides insights based on forecasting results.
    
    Capabilities:
    - Calculate inventory coverage days
    - Determine reorder points (ROP)
    - Calculate expected revenue and holding costs
    - Provide inventory optimization recommendations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def get_item_inventory(self, item_id: str) -> Optional[int]:
        """
        Get current inventory level for an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            Current inventory units, or None if not found
        """
        query = "SELECT unit FROM inv WHERE item_id = ?"
        result = self.db_manager.execute_query(query, (item_id,))
        
        if result.get("success", False) and not result["data"].empty:
            return int(result["data"]["unit"].iloc[0])
        return None
    
    def get_item_details(self, item_id: str) -> Dict[str, Union[str, float]]:
        """
        Get item details including price, lead time, and holding cost.
        
        Args:
            item_id: Item ID
            
        Returns:
            Dict with item details
        """
        query = """
        SELECT description, price, lead_time, holding_cost 
        FROM item_dim 
        WHERE item_id = ?
        """
        result = self.db_manager.execute_query(query, (item_id,))
        
        if result.get("success", False) and not result["data"].empty:
            row = result["data"].iloc[0]
            return {
                'description': row['description'],
                'price': float(row['price']),
                'lead_time': int(row['lead_time']),
                'holding_cost': float(row['holding_cost'])
            }
        return {}
    
    def calculate_coverage_days(self, forecast_df: pd.DataFrame, current_inventory: int) -> Dict[str, Union[str, int]]:
        """
        Calculate how many days the current inventory will last.
        
        Args:
            forecast_df: Forecast DataFrame with 'ds', 'yhat' columns
            current_inventory: Current inventory level
            
        Returns:
            Dict with coverage information
        """
        # Create cumulative demand column
        fcst = forecast_df[['ds', 'yhat']].copy()
        fcst['cum_demand'] = fcst['yhat'].cumsum()
        
        # Find when inventory will be exhausted
        cover_until = fcst.loc[fcst['cum_demand'] >= current_inventory, 'ds'].min()
        
        if pd.isna(cover_until):
            # Inventory lasts beyond forecast period
            forecast_days = len(fcst)
            total_forecast_demand = fcst['cum_demand'].iloc[-1]
            remaining_inventory = current_inventory - total_forecast_demand
            
            return {
                'cover_until': None,
                'coverage_days': f">{forecast_days}",
                'status': 'sufficient',
                'remaining_inventory': remaining_inventory,
                'message': f"Inventory will last beyond {forecast_days} day forecast period"
            }
        else:
            # Calculate exact coverage days
            coverage_days = (cover_until - fcst['ds'].min()).days
            
            status = 'critical' if coverage_days <= 7 else 'low' if coverage_days <= 14 else 'adequate'
            
            return {
                'cover_until': cover_until.strftime('%Y-%m-%d'),
                'coverage_days': coverage_days,
                'status': status,
                'remaining_inventory': 0,
                'message': f"Inventory will be exhausted in {coverage_days} days ({cover_until.strftime('%Y-%m-%d')})"
            }
    
    def calculate_reorder_point(self, forecast_df: pd.DataFrame, lead_time: int, safety_factor: float = 1.25) -> Dict[str, Union[float, int]]:
        """
        Calculate reorder point (ROP) based on lead time and forecast demand.
        
        Args:
            forecast_df: Forecast DataFrame with 'ds', 'yhat' columns
            lead_time: Lead time in days
            safety_factor: Safety stock multiplier (default 1.25 = 25% safety stock)
            
        Returns:
            Dict with ROP information
        """
        if len(forecast_df) < lead_time:
            avg_daily_demand = forecast_df['yhat'].mean()
            lead_time_demand = avg_daily_demand * lead_time
        else:
            lead_time_demand = forecast_df['yhat'].iloc[:lead_time].sum()
        
        # Calculate safety stock
        safety_stock = lead_time_demand * (safety_factor - 1)
        reorder_point = lead_time_demand * safety_factor
        
        return {
            'reorder_point': round(reorder_point),
            'lead_time_demand': round(lead_time_demand),
            'safety_stock': round(safety_stock),
            'safety_factor': safety_factor,
            'message': f"Reorder when inventory reaches {round(reorder_point)} units"
        }
    
    def calculate_financial_metrics(self, forecast_df: pd.DataFrame, current_inventory: int, 
                                  price: float, holding_cost_rate: float) -> Dict[str, float]:
        """
        Calculate expected revenue and holding costs.
        
        Args:
            forecast_df: Forecast DataFrame with 'ds', 'yhat' columns
            current_inventory: Current inventory level
            price: Item price per unit
            holding_cost_rate: Holding cost rate (e.g., 0.5 for $0.50 per unit per period)
            
        Returns:
            Dict with financial metrics
        """
        fcst = forecast_df[['ds', 'yhat']].copy()
        fcst['cum_demand'] = fcst['yhat'].cumsum()
        
        # Calculate expected sales and revenue
        total_demand = fcst['yhat'].sum()
        expected_sales = min(current_inventory, total_demand)
        expected_revenue = expected_sales * price
        
        # Calculate inventory levels over time (declining by demand)
        fcst['inventory'] = current_inventory - fcst['cum_demand']
        fcst['inventory'] = fcst['inventory'].clip(lower=0)
        
        # Calculate holding costs
        avg_inventory = fcst['inventory'].mean()
        holding_cost = avg_inventory * holding_cost_rate * len(fcst)
        
        # Calculate profit margin
        gross_profit = expected_revenue - holding_cost
        
        return {
            'expected_revenue': round(expected_revenue, 2),
            'expected_sales': round(expected_sales),
            'total_demand': round(total_demand),
            'avg_inventory': round(avg_inventory, 1),
            'holding_cost': round(holding_cost, 2),
            'gross_profit': round(gross_profit, 2),
            'profit_margin': round((gross_profit / expected_revenue * 100) if expected_revenue > 0 else 0, 1)
        }
    
    def generate_inventory_insights(self, item_id: str, forecast_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive inventory insights for an item.
        
        Args:
            item_id: Item ID
            forecast_df: Forecast DataFrame from Prophet
            
        Returns:
            Dict with all inventory insights
        """
        try:
            # Get current inventory and item details
            current_inventory = self.get_item_inventory(item_id)
            item_details = self.get_item_details(item_id)
            
            if current_inventory is None:
                return {
                    'success': False,
                    'error': f"No inventory data found for item {item_id}",
                    'item_id': item_id
                }
            
            if not item_details:
                return {
                    'success': False,
                    'error': f"No item details found for item {item_id}",
                    'item_id': item_id
                }
            
            # Calculate insights
            coverage_info = self.calculate_coverage_days(forecast_df, current_inventory)
            rop_info = self.calculate_reorder_point(forecast_df, item_details['lead_time'])
            financial_info = self.calculate_financial_metrics(
                forecast_df, current_inventory, 
                item_details['price'], item_details['holding_cost']
            )
            
            # Determine inventory status and recommendations
            recommendations = []
            
            # Coverage-based recommendations
            if coverage_info['status'] == 'critical':
                recommendations.append("🚨 URGENT: Reorder immediately - low inventory coverage")
            elif coverage_info['status'] == 'low':
                recommendations.append("⚠️ WARNING: Consider reordering soon - inventory running low")
            
            # ROP-based recommendations
            if current_inventory <= rop_info['reorder_point']:
                recommendations.append(f"📦 REORDER: Current inventory ({current_inventory}) is at or below reorder point ({rop_info['reorder_point']})")
            
            # Financial recommendations
            if financial_info['profit_margin'] < 10:
                recommendations.append("💰 Consider optimizing inventory levels to improve profit margins")
            
            return {
                'success': True,
                'item_id': item_id,
                'item_description': item_details['description'],
                'current_inventory': current_inventory,
                'item_details': item_details,
                'coverage_analysis': coverage_info,
                'reorder_analysis': rop_info,
                'financial_analysis': financial_info,
                'recommendations': recommendations,
                'forecast_period_days': len(forecast_df)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'item_id': item_id
            }
    
    def create_inventory_visualization(self, item_id: str, forecast_df: pd.DataFrame, 
                                    insights: Dict[str, Any]) -> str:
        """
        Create inventory management visualization.
        
        Args:
            item_id: Item ID
            forecast_df: Forecast DataFrame
            insights: Inventory insights dictionary
            
        Returns:
            Path to saved visualization
        """
        if not insights['success']:
            raise ValueError(f"Cannot create visualization: {insights['error']}")
        
        # Prepare data
        fcst = forecast_df[['ds', 'yhat']].copy()
        fcst['cum_demand'] = fcst['yhat'].cumsum()
        current_inventory = insights['current_inventory']
        fcst['inventory'] = current_inventory - fcst['cum_demand']
        fcst['inventory'] = fcst['inventory'].clip(lower=0)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Inventory Levels Over Time
        ax1.plot(fcst['ds'], fcst['inventory'], 'b-', linewidth=2, label='Inventory Level')
        ax1.axhline(y=insights['reorder_analysis']['reorder_point'], 
                   color='r', linestyle='--', label='Reorder Point')
        ax1.axhline(y=insights['reorder_analysis']['safety_stock'], 
                   color='orange', linestyle=':', label='Safety Stock')
        ax1.fill_between(fcst['ds'], 0, fcst['inventory'], alpha=0.3, color='blue')
        ax1.set_title('Inventory Levels Over Forecast Period', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Inventory Units')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Daily Demand vs Cumulative Demand
        ax2_twin = ax2.twinx()
        ax2.bar(fcst['ds'], fcst['yhat'], alpha=0.6, color='green', label='Daily Demand')
        ax2_twin.plot(fcst['ds'], fcst['cum_demand'], 'r-', linewidth=2, label='Cumulative Demand')
        ax2.set_title('Demand Forecast', fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Daily Demand', color='green')
        ax2_twin.set_ylabel('Cumulative Demand', color='red')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Financial Metrics (Pie Chart)
        financial = insights['financial_analysis']
        labels = ['Revenue', 'Holding Costs']
        sizes = [financial['expected_revenue'] - financial['holding_cost'], financial['holding_cost']]
        colors = ['#2E8B57', '#DC143C']
        ax3.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax3.set_title(f"Revenue vs Holding Costs\nProfit: ${financial['gross_profit']:.2f}", fontweight='bold')
        
        # Plot 4: Key Metrics Summary (Text)
        ax4.axis('off')
        coverage = insights['coverage_analysis']
        
        metrics_text = f"""
INVENTORY INSIGHTS - {insights['item_description']}

📦 CURRENT INVENTORY
• Stock Level: {current_inventory:,} units
• Status: {coverage['status'].upper()}

⏰ COVERAGE ANALYSIS  
• Coverage Days: {coverage['coverage_days']}
• Stock Until: {coverage.get('cover_until', 'Beyond forecast')}

🔄 REORDER ANALYSIS
• Reorder Point: {insights['reorder_analysis']['reorder_point']:,} units
• Lead Time: {insights['item_details']['lead_time']} days
• Safety Stock: {insights['reorder_analysis']['safety_stock']:,} units

💰 FINANCIAL METRICS
• Expected Revenue: ${financial['expected_revenue']:,.2f}
• Holding Costs: ${financial['holding_cost']:,.2f}
• Gross Profit: ${financial['gross_profit']:,.2f}
• Profit Margin: {financial['profit_margin']}%

🎯 RECOMMENDATIONS
{chr(10).join(['• ' + rec for rec in insights['recommendations'][:3]])}
        """
        
        ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inventory_analysis_{item_id}_{timestamp}.png"
        filepath = f"visualizations/{filename}"
        
        # Ensure directory exists
        import os
        os.makedirs("visualizations", exist_ok=True)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def process_inventory_request(self, item_id: str, forecast_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Main method to process inventory management requests.
        
        Args:
            item_id: Item ID
            forecast_df: Forecast DataFrame from Prophet
            
        Returns:
            Dict with inventory analysis results
        """
        try:
            # Generate insights
            insights = self.generate_inventory_insights(item_id, forecast_df)
            
            if not insights['success']:
                return insights
            
            # Create visualization
            plot_path = self.create_inventory_visualization(item_id, forecast_df, insights)
            insights['visualization_path'] = plot_path
            
            # Build response text
            coverage = insights['coverage_analysis']
            rop = insights['reorder_analysis']
            financial = insights['financial_analysis']
            
            response_parts = []
            response_parts.append(f"📦 **Inventory Analysis for {insights['item_description']}**")
            response_parts.append("")
            
            # Current Status
            response_parts.append("**📊 Current Status:**")
            response_parts.append(f"• Stock Level: {insights['current_inventory']:,} units")
            response_parts.append(f"• Status: {coverage['status'].upper()}")
            response_parts.append(f"• {coverage['message']}")
            response_parts.append("")
            
            # Reorder Analysis
            response_parts.append("**🔄 Reorder Analysis:**")
            response_parts.append(f"• Reorder Point: {rop['reorder_point']:,} units")
            response_parts.append(f"• Lead Time Demand: {rop['lead_time_demand']:,} units")
            response_parts.append(f"• Safety Stock: {rop['safety_stock']:,} units")
            response_parts.append("")
            
            # Financial Impact
            response_parts.append("**💰 Financial Metrics:**")
            response_parts.append(f"• Expected Revenue: ${financial['expected_revenue']:,.2f}")
            response_parts.append(f"• Holding Costs: ${financial['holding_cost']:,.2f}")
            response_parts.append(f"• Gross Profit: ${financial['gross_profit']:,.2f}")
            response_parts.append(f"• Profit Margin: {financial['profit_margin']}%")
            response_parts.append("")
            
            # Recommendations
            if insights['recommendations']:
                response_parts.append("**🎯 Recommendations:**")
                for rec in insights['recommendations']:
                    response_parts.append(f"• {rec}")
                response_parts.append("")
            
            response_parts.append(f"📊 **Visualization:** {plot_path}")
            
            insights['response_text'] = "\n".join(response_parts)
            
            return insights
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'item_id': item_id,
                'response_text': f"❌ **Inventory Analysis Error:** {str(e)}"
            }


def create_inventory_manager(db_manager: DatabaseManager) -> InventoryManager:
    """
    Factory function to create an inventory manager.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        InventoryManager instance
    """
    return InventoryManager(db_manager)


# Example usage and testing
if __name__ == "__main__":
    # Test the inventory manager
    from database_manager import DatabaseManager
    from forecasting_agent import ForecastingAgent
    
    db_manager = DatabaseManager()
    inventory_manager = InventoryManager(db_manager)
    forecasting_agent = ForecastingAgent(db_manager)
    
    # Test with a sample item
    item_id = "FOODS_3_090"  # Vanilla Ice Cream
    
    # Generate forecast
    forecast_df, model = forecasting_agent.generate_forecast(item_id, 30)
    
    # Analyze inventory
    result = inventory_manager.process_inventory_request(item_id, forecast_df)
    
    print("🧪 Testing Inventory Management")
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"📦 Item: {result['item_id']}")
        print(f"📊 Current Inventory: {result['current_inventory']:,} units")
        print(f"📅 Coverage: {result['coverage_analysis']['coverage_days']} days")
        print(f"🔄 Reorder Point: {result['reorder_analysis']['reorder_point']:,} units")
        print(f"💰 Expected Revenue: ${result['financial_analysis']['expected_revenue']:,.2f}")
        if result.get('visualization_path'):
            print(f"🎨 Visualization: {result['visualization_path']}")
    else:
        print(f"❌ Error: {result['error']}")