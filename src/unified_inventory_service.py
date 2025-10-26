"""
Unified Inventory Service

This service demonstrates how inventory analysis depends on forecasting.
It provides a clear workflow: Forecast → Inventory Analysis → Business Insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import warnings
from datetime import datetime

from db.database_manager import DatabaseManager
from agents.forecasting_agent import ForecastingAgent
from inventory_management import InventoryManager

warnings.filterwarnings('ignore')


class UnifiedInventoryService:
    """
    Unified service that combines forecasting and inventory analysis.
    
    This service makes the dependency clear:
    1. First get forecast from ForecastingAgent
    2. Then use forecast for inventory analysis via InventoryManager
    3. Combine both for complete business intelligence
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        # Initialize components
        self.db_manager = db_manager or DatabaseManager()
        self.forecasting_agent = ForecastingAgent(self.db_manager)
        self.inventory_manager = InventoryManager(self.db_manager)
        
    def get_complete_analysis(self, item_id: str, forecast_days: int = 30, 
                            include_visualizations: bool = True) -> Dict[str, Any]:
        """
        Get complete inventory analysis that depends on forecasting.
        
        Workflow:
        1. Generate forecast using ForecastingAgent
        2. Use forecast for inventory analysis via InventoryManager  
        3. Combine results for business intelligence
        
        Args:
            item_id: Item ID to analyze
            forecast_days: Number of days to forecast
            include_visualizations: Whether to generate charts
            
        Returns:
            Dict with complete analysis results
        """
        
        print(f"🔍 Starting Complete Analysis for {item_id}")
        print("=" * 60)
        
        try:
            # STEP 1: Generate Forecast (Required for Inventory Analysis)
            print("📈 Step 1: Generating Forecast...")
            print(f"   • Forecasting {forecast_days} days ahead")
            print(f"   • Using Prophet model for demand prediction")
            
            forecast_df, model = self.forecasting_agent.generate_forecast(
                item_id=item_id, 
                forecast_days=forecast_days
            )
            
            forecast_summary = {
                'total_periods': len(forecast_df),
                'forecast_start': forecast_df['ds'].min(),
                'forecast_end': forecast_df['ds'].max(),
                'avg_daily_demand': forecast_df['yhat'].mean(),
                'total_demand': forecast_df['yhat'].sum()
            }
            
            print(f"   ✅ Forecast generated: {len(forecast_df)} data points")
            print(f"   📊 Avg daily demand: {forecast_summary['avg_daily_demand']:.1f} units")
            
            # STEP 2: Inventory Analysis (Depends on Forecast)
            print("\n📦 Step 2: Inventory Analysis (using forecast data)...")
            print(f"   • Using forecast to calculate coverage days")
            print(f"   • Determining reorder points from demand patterns")
            print(f"   • Computing financial metrics based on projections")
            
            inventory_insights = self.inventory_manager.generate_inventory_insights(
                item_id=item_id, 
                forecast_df=forecast_df  # ← THIS IS THE KEY DEPENDENCY!
            )
            
            if not inventory_insights['success']:
                return {
                    'success': False,
                    'error': f"Inventory analysis failed: {inventory_insights.get('error')}",
                    'forecast_summary': forecast_summary
                }
            
            print(f"   ✅ Inventory analysis complete")
            coverage = inventory_insights['coverage_analysis']
            print(f"   📅 Coverage: {coverage['coverage_days']} days ({coverage['status']})")
            
            # STEP 3: Create Visualizations (Optional)
            visualization_paths = {}
            if include_visualizations:
                print("\n📊 Step 3: Creating Visualizations...")
                
                # Forecast visualization
                forecast_viz = self.forecasting_agent.create_forecast_visualization(
                    forecast_df, model, item_id, forecast_days
                )
                visualization_paths['forecast'] = forecast_viz
                print(f"   📈 Forecast chart: {forecast_viz}")
                
                # Inventory visualization 
                inventory_viz = self.inventory_manager.create_inventory_visualization(
                    item_id, forecast_df, inventory_insights
                )
                visualization_paths['inventory'] = inventory_viz
                print(f"   📦 Inventory chart: {inventory_viz}")
            
            # STEP 4: Combine Results
            print(f"\n🎯 Step 4: Combining Results...")
            
            result = {
                'success': True,
                'item_id': item_id,
                'analysis_timestamp': datetime.now().isoformat(),
                
                # Forecast Results (Input for Inventory Analysis)
                'forecast_data': {
                    'dataframe': forecast_df,
                    'model': model,
                    'summary': forecast_summary
                },
                
                # Inventory Results (Depends on Forecast)
                'inventory_analysis': inventory_insights,
                
                # Combined Business Intelligence
                'business_intelligence': self._create_business_intelligence(
                    forecast_summary, inventory_insights
                ),
                
                # Visualizations
                'visualizations': visualization_paths,
                
                # Dependency Information
                'workflow': {
                    'step_1': 'Forecast Generation (ForecastingAgent)',
                    'step_2': 'Inventory Analysis (InventoryManager using forecast)',
                    'step_3': 'Business Intelligence (Combined insights)',
                    'dependency': 'Inventory analysis REQUIRES forecast data'
                }
            }
            
            print("✅ Complete analysis ready!")
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}",
                'item_id': item_id
            }
    
    def _create_business_intelligence(self, forecast_summary: Dict, 
                                   inventory_insights: Dict) -> Dict[str, Any]:
        """
        Create combined business intelligence from forecast and inventory data.
        
        Args:
            forecast_summary: Summary of forecast results
            inventory_insights: Inventory analysis results
            
        Returns:
            Dict with business intelligence insights
        """
        
        if not inventory_insights.get('success'):
            return {'error': 'Cannot create BI without successful inventory analysis'}
        
        coverage = inventory_insights['coverage_analysis']
        reorder = inventory_insights['reorder_analysis']
        financial = inventory_insights['financial_analysis']
        
        # Combine insights
        business_intelligence = {
            'executive_summary': {
                'item_id': inventory_insights['item_id'],
                'item_description': inventory_insights['item_description'],
                'current_stock': inventory_insights['current_inventory'],
                'forecast_period': f"{len(inventory_insights.get('forecast_period_days', 30))} days",
                'status': coverage['status'].upper(),
                'priority_level': self._determine_priority_level(coverage, reorder, inventory_insights['current_inventory'])
            },
            
            'demand_forecast': {
                'avg_daily_demand': f"{forecast_summary['avg_daily_demand']:.1f} units/day",
                'total_forecast_demand': f"{forecast_summary['total_demand']:.0f} units",
                'forecast_accuracy': 'Based on Prophet time series model',
                'trend': self._analyze_trend(forecast_summary)
            },
            
            'inventory_status': {
                'days_of_cover': coverage['coverage_days'],
                'coverage_status': coverage['status'],
                'stock_exhaustion_date': coverage.get('cover_until', 'Beyond forecast period'),
                'reorder_needed': inventory_insights['current_inventory'] <= reorder['reorder_point']
            },
            
            'financial_impact': {
                'expected_revenue': f"${financial['expected_revenue']:,.2f}",
                'holding_costs': f"${financial['holding_cost']:,.2f}",
                'gross_profit': f"${financial['gross_profit']:,.2f}",
                'profit_margin': f"{financial['profit_margin']}%",
                'roi_status': self._assess_roi(financial['profit_margin'])
            },
            
            'action_items': inventory_insights.get('recommendations', []),
            
            'risk_assessment': {
                'stockout_risk': self._assess_stockout_risk(coverage['coverage_days']),
                'financial_risk': self._assess_financial_risk(financial['profit_margin']),
                'overall_risk': self._calculate_overall_risk(coverage, financial)
            }
        }
        
        return business_intelligence
    
    def _determine_priority_level(self, coverage: Dict, reorder: Dict, current_inventory: int) -> str:
        """Determine priority level based on multiple factors."""
        if coverage['status'] == 'critical' or current_inventory <= reorder['reorder_point']:
            return 'HIGH'
        elif coverage['status'] == 'low':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _analyze_trend(self, forecast_summary: Dict) -> str:
        """Analyze demand trend from forecast."""
        # This could be enhanced with actual trend analysis
        avg_demand = forecast_summary['avg_daily_demand']
        if avg_demand > 500:
            return 'High demand item'
        elif avg_demand > 200:
            return 'Moderate demand item'
        else:
            return 'Low demand item'
    
    def _assess_roi(self, profit_margin: float) -> str:
        """Assess ROI status."""
        if profit_margin >= 30:
            return 'Excellent'
        elif profit_margin >= 20:
            return 'Good'
        elif profit_margin >= 10:
            return 'Acceptable'
        else:
            return 'Poor'
    
    def _assess_stockout_risk(self, coverage_days: int) -> str:
        """Assess stockout risk."""
        if isinstance(coverage_days, str):  # e.g., ">30"
            return 'Low'
        elif coverage_days <= 3:
            return 'Critical'
        elif coverage_days <= 7:
            return 'High'
        elif coverage_days <= 14:
            return 'Medium'
        else:
            return 'Low'
    
    def _assess_financial_risk(self, profit_margin: float) -> str:
        """Assess financial risk."""
        if profit_margin < 10:
            return 'High'
        elif profit_margin < 20:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_overall_risk(self, coverage: Dict, financial: Dict) -> str:
        """Calculate overall risk level."""
        stockout_risk = self._assess_stockout_risk(coverage['coverage_days'])
        financial_risk = self._assess_financial_risk(financial['profit_margin'])
        
        if stockout_risk == 'Critical' or financial_risk == 'High':
            return 'HIGH'
        elif stockout_risk in ['High', 'Medium'] or financial_risk == 'Medium':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def explain_workflow(self) -> str:
        """
        Explain how inventory analysis depends on forecasting.
        
        Returns:
            String explaining the workflow dependency
        """
        
        explanation = """
🔗 INVENTORY ANALYSIS WORKFLOW DEPENDENCY

📈 STEP 1: FORECASTING (ForecastingAgent)
   ├── Generate Prophet model for demand prediction
   ├── Create forecast DataFrame with 'ds', 'yhat' columns  
   ├── Calculate future demand patterns
   └── Output: forecast_df (REQUIRED for next step)

📦 STEP 2: INVENTORY ANALYSIS (InventoryManager) 
   ├── Requires: forecast_df from Step 1
   ├── Calculate coverage days: fcst['cum_demand'] = fcst['yhat'].cumsum()
   ├── Find coverage limit: cover_day = fcst.loc[fcst['cum_demand'] >= inventory]
   ├── Compute reorder points based on lead time demand
   ├── Calculate financial metrics using projected sales
   └── Output: Complete inventory insights

🎯 STEP 3: BUSINESS INTELLIGENCE
   ├── Combine forecast + inventory results
   ├── Generate recommendations
   ├── Create executive summaries
   └── Output: Actionable business insights

🔥 KEY DEPENDENCY:
   Inventory Manager CANNOT work without forecast data!
   The forecast provides the demand projections needed for:
   • Coverage calculations
   • Reorder point analysis  
   • Financial projections
   • Business recommendations

💡 This is why your notebook code works:
   1. Prophet generates forecast
   2. Your code uses forecast['yhat'] for inventory calculations
   3. Enhanced framework automates this exact workflow!
        """
        
        return explanation


def demo_workflow_dependency():
    """Demonstrate how inventory analysis depends on forecasting."""
    
    print("🔗 DEMONSTRATING WORKFLOW DEPENDENCY")
    print("=" * 60)
    
    # Initialize service
    service = UnifiedInventoryService()
    
    # Show workflow explanation
    print(service.explain_workflow())
    
    # Demonstrate with actual data
    print("\n🧪 LIVE DEMONSTRATION:")
    print("=" * 30)
    
    item_id = "FOODS_3_090"
    
    # Get complete analysis (showing the dependency)
    result = service.get_complete_analysis(
        item_id=item_id, 
        forecast_days=30,
        include_visualizations=False  # Skip viz for demo speed
    )
    
    if result['success']:
        print(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"📊 Business Intelligence Summary:")
        
        bi = result['business_intelligence']
        exec_summary = bi['executive_summary']
        
        print(f"   • Item: {exec_summary['item_description']}")
        print(f"   • Status: {exec_summary['status']} priority")
        print(f"   • Coverage: {bi['inventory_status']['days_of_cover']} days")
        print(f"   • Revenue: {bi['financial_impact']['expected_revenue']}")
        print(f"   • Action: {bi['action_items'][0] if bi['action_items'] else 'No immediate action needed'}")
        
        print(f"\n🔗 Dependency Confirmed:")
        workflow = result['workflow']
        print(f"   1. {workflow['step_1']}")
        print(f"   2. {workflow['step_2']}")
        print(f"   3. {workflow['step_3']}")
        print(f"   💡 {workflow['dependency']}")
        
    else:
        print(f"❌ Demo failed: {result.get('error')}")


if __name__ == "__main__":
    demo_workflow_dependency()