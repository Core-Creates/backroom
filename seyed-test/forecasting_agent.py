"""
Forecasting Agent for Retail Sales using Prophet

This agent handles forecasting requests, generates predictions using Prophet,
and can create visualizations or save results as parquet files.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Optional, Union
import os

# Suppress Prophet warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
except ImportError:
    print("Prophet not installed. Run: pip install prophet")
    raise

from database_manager import DatabaseManager


class ForecastingAgent:
    """
    Sales forecasting agent using Facebook Prophet.
    
    Capabilities:
    - Forecast sales for specific items
    - Generate forecast visualizations
    - Save forecast results as parquet files
    - Integrate with natural language queries
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.forecasts_dir = Path("forecasts")
        self.forecasts_dir.mkdir(exist_ok=True)
        
    def should_create_forecast(self, question: str, sql_query: str = "", data_preview: str = "") -> bool:
        """
        Determine if the question requires forecasting.
        
        Args:
            question: User's question
            sql_query: Generated SQL query
            data_preview: Preview of query results
            
        Returns:
            bool: True if forecasting is needed
        """
        forecast_keywords = [
            'forecast', 'predict', 'projection', 'future', 'predict sales',
            'forecast sales', 'sales projection', 'future sales', 'predict demand',
            'demand forecast', 'sales forecast', 'trend forecast', 'next month',
            'next week', 'coming days', 'upcoming', 'prophet', 'prediction'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in forecast_keywords)
    
    def extract_forecast_params(self, question: str) -> Dict[str, Union[str, int]]:
        """
        Extract forecasting parameters from the question.
        
        Args:
            question: User's question
            
        Returns:
            Dict containing item_id, forecast_days, and other parameters
        """
        import re
        
        params = {
            'item_id': None,
            'forecast_days': 30,  # default
            'save_as_parquet': False,
            'plot_results': True
        }
        
        # Extract item mentions
        item_patterns = [
            r'FOODS_\d+_\d+',  # Direct item ID
            r'vanilla ice cream', r'chocolate ice cream', r'strawberry',
            r'milk', r'yogurt', r'apple', r'banana', r'cheese', r'orange juice'
        ]
        
        question_lower = question.lower()
        
        # Check for specific items
        for pattern in item_patterns:
            if re.search(pattern, question_lower):
                if pattern.startswith('FOODS_'):
                    params['item_id'] = pattern
                else:
                    # Map common names to item IDs
                    item_mapping = {
                        'vanilla ice cream': 'FOODS_3_090',
                        'chocolate ice cream': 'FOODS_3_282',
                        'milk': 'FOODS_3_586',
                        'yogurt': 'FOODS_3_555',
                        'apple': 'FOODS_3_252',
                        'banana': 'FOODS_3_226',
                        'cheese': 'FOODS_3_714',
                        'orange juice': 'FOODS_3_681'
                    }
                    params['item_id'] = item_mapping.get(pattern)
                break
        
        # Extract forecast period
        day_patterns = [
            (r'(\d+)\s*days?', 1),
            (r'(\d+)\s*weeks?', 7),
            (r'(\d+)\s*months?', 30),
            (r'next\s+week', 7),
            (r'next\s+month', 30),
            (r'next\s+(\d+)\s*days?', 1)
        ]
        
        for pattern, multiplier in day_patterns:
            match = re.search(pattern, question_lower)
            if match:
                if 'next' in pattern and pattern.endswith('days?', 1):
                    params['forecast_days'] = int(match.group(1))
                elif 'next' in pattern:
                    params['forecast_days'] = multiplier
                else:
                    params['forecast_days'] = int(match.group(1)) * multiplier
                break
        
        # Check for save/export requests
        if any(word in question_lower for word in ['save', 'export', 'parquet', 'file']):
            params['save_as_parquet'] = True
        
        # Check if plot is requested
        if any(word in question_lower for word in ['plot', 'chart', 'graph', 'visualize', 'show']):
            params['plot_results'] = True
        
        return params
    
    def prepare_forecast_data(self, item_id: str) -> pd.DataFrame:
        """
        Prepare historical sales data for Prophet forecasting.
        
        Args:
            item_id: Item ID to forecast
            
        Returns:
            DataFrame formatted for Prophet (ds, y columns)
        """
        # Get historical sales data
        query = """
        SELECT date, SUM(sale) as sales
        FROM sales 
        WHERE item_id = ?
        GROUP BY date
        ORDER BY date
        """
        
        result = self.db_manager.execute_query(query, (item_id,))
        
        if not result.get("success", False) or result.get("data") is None:
            raise ValueError(f"No sales data found for item {item_id}")
            
        df = result["data"]
        
        if df.empty:
            raise ValueError(f"No sales data found for item {item_id}")
        
        # Ensure datetime and sorted
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        # Fill missing days with 0
        full_idx = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
        df = (
            df.set_index("date")
               .reindex(full_idx)
               .rename_axis("date")
               .fillna({"sales": 0})
               .reset_index()
        )
        
        # Rename for Prophet
        dfp = df.rename(columns={"date": "ds", "sales": "y"})[["ds", "y"]]
        
        return dfp
    
    def create_prophet_model(self, historical_data: pd.DataFrame, **kwargs) -> Prophet:
        """
        Create and fit Prophet model.
        
        Args:
            historical_data: DataFrame with ds, y columns
            **kwargs: Additional Prophet parameters
            
        Returns:
            Fitted Prophet model
        """
        # Default Prophet parameters optimized for retail sales
        default_params = {
            'weekly_seasonality': True,      # capture weekends
            'daily_seasonality': False,      # no sub-daily seasonality  
            'yearly_seasonality': False,     # unless you have >1yr of data
            'seasonality_mode': 'additive',  # additive seasonality
            'changepoint_prior_scale': 0.05, # flexibility in trend changes
            'seasonality_prior_scale': 10.0, # flexibility in seasonality
        }
        
        # Update with any provided parameters
        default_params.update(kwargs)
        
        # Create and fit model
        model = Prophet(**default_params)
        model.fit(historical_data)
        
        return model
    
    def generate_forecast(self, item_id: str, forecast_days: int = 30, **prophet_params) -> Tuple[pd.DataFrame, Prophet]:
        """
        Generate sales forecast for an item.
        
        Args:
            item_id: Item ID to forecast
            forecast_days: Number of days to forecast
            **prophet_params: Additional Prophet parameters
            
        Returns:
            Tuple of (forecast_df, fitted_model)
        """
        # Prepare data
        historical_data = self.prepare_forecast_data(item_id)
        
        # Create and fit model
        model = self.create_prophet_model(historical_data, **prophet_params)
        
        # Generate future dates
        future = model.make_future_dataframe(periods=forecast_days, freq="D")
        
        # Make predictions
        forecast = model.predict(future)
        
        # Add item_id to forecast
        forecast['item_id'] = item_id
        
        # Ensure non-negative predictions
        for col in ['yhat', 'yhat_lower', 'yhat_upper']:
            if col in forecast.columns:
                forecast[col] = forecast[col].clip(lower=0)
        
        return forecast, model
    
    def create_forecast_visualization(self, forecast_df: pd.DataFrame, model: Prophet, 
                                   item_id: str, forecast_days: int) -> str:
        """
        Create forecast visualization.
        
        Args:
            forecast_df: Forecast results from Prophet
            model: Fitted Prophet model
            item_id: Item ID
            forecast_days: Number of forecast days
            
        Returns:
            str: Path to saved plot
        """
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Main forecast plot
        model.plot(forecast_df, ax=ax1)
        ax1.set_title(f'{item_id} — Sales Forecast ({forecast_days} days)', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Sales Units', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Components plot (trend + seasonality)
        try:
            model.plot_components(forecast_df, ax=ax2)
            ax2.set_title('Forecast Components', fontsize=14, fontweight='bold')
        except:
            # If components plot fails, create a simple trend plot
            ax2.plot(forecast_df['ds'], forecast_df['trend'], label='Trend', color='red', linewidth=2)
            ax2.set_title('Sales Trend', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_ylabel('Trend', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"forecast_{item_id}_{timestamp}.png"
        filepath = self.forecasts_dir / filename
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def save_forecast_parquet(self, forecast_df: pd.DataFrame, item_id: str) -> str:
        """
        Save forecast results as parquet file.
        
        Args:
            forecast_df: Forecast DataFrame
            item_id: Item ID
            
        Returns:
            str: Path to saved file
        """
        # Select relevant columns
        columns_to_save = ['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'item_id']
        save_df = forecast_df[columns_to_save].copy()
        
        # Rename columns for clarity
        save_df = save_df.rename(columns={
            'ds': 'date',
            'yhat': 'forecast_sales',
            'yhat_lower': 'forecast_lower_bound',
            'yhat_upper': 'forecast_upper_bound'
        })
        
        # Save as parquet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"forecast_{item_id}_{timestamp}.parquet"
        filepath = self.forecasts_dir / filename
        
        save_df.to_parquet(filepath, index=False)
        
        return str(filepath)
    
    def process_forecast_request(self, question: str, item_data: pd.DataFrame = None, include_inventory_analysis: bool = True) -> Dict:
        """
        Main method to process forecasting requests.
        
        Args:
            question: User's forecasting question
            item_data: Optional pre-filtered item data
            include_inventory_analysis: Whether to include inventory management insights
            
        Returns:
            Dict with forecast results, file paths, and response text
        """
        try:
            # Extract parameters from question
            params = self.extract_forecast_params(question)
            
            if not params['item_id']:
                # Try to get item from available data or use default
                if item_data is not None and not item_data.empty:
                    # Get the first item from the data
                    if 'item_id' in item_data.columns:
                        params['item_id'] = item_data['item_id'].iloc[0]
                    else:
                        # Default to popular item
                        params['item_id'] = 'FOODS_3_090'  # Vanilla Ice Cream
                else:
                    params['item_id'] = 'FOODS_3_090'  # Default item
            
            # Generate forecast
            forecast_df, model = self.generate_forecast(
                params['item_id'], 
                params['forecast_days']
            )
            
            result = {
                'success': True,
                'item_id': params['item_id'],
                'forecast_days': params['forecast_days'],
                'forecast_data': forecast_df,
                'model': model,
                'plot_path': None,
                'parquet_path': None,
                'inventory_analysis': None,
                'response_text': ""
            }
            
            # Create visualization if requested
            if params['plot_results']:
                plot_path = self.create_forecast_visualization(
                    forecast_df, model, params['item_id'], params['forecast_days']
                )
                result['plot_path'] = plot_path
            
            # Save parquet if requested
            if params['save_as_parquet']:
                parquet_path = self.save_forecast_parquet(forecast_df, params['item_id'])
                result['parquet_path'] = parquet_path
            
            # Get item description
            item_query = "SELECT description FROM item_dim WHERE item_id = ?"
            item_result = self.db_manager.execute_query(item_query, (params['item_id'],))
            if item_result.get("success", False) and not item_result["data"].empty:
                item_name = item_result["data"]['description'].iloc[0]
            else:
                item_name = params['item_id']
            
            # Calculate forecast statistics
            future_forecast = forecast_df[forecast_df['ds'] > forecast_df['ds'].max() - pd.Timedelta(days=params['forecast_days'])]
            avg_forecast = future_forecast['yhat'].mean()
            total_forecast = future_forecast['yhat'].sum()
            
            # Include inventory analysis if requested
            if include_inventory_analysis:
                try:
                    from inventory_management import InventoryManager
                    inventory_manager = InventoryManager(self.db_manager)
                    
                    # Generate inventory insights
                    inventory_result = inventory_manager.process_inventory_request(params['item_id'], forecast_df)
                    result['inventory_analysis'] = inventory_result
                    
                except ImportError:
                    # Inventory management not available
                    pass
                except Exception as e:
                    # Log error but don't fail the forecast
                    print(f"Warning: Inventory analysis failed: {e}")
            
            # Build response text
            response_parts = []
            response_parts.append(f"📊 **Sales Forecast for {item_name}**")
            response_parts.append(f"🔮 **Forecast Period:** {params['forecast_days']} days")
            response_parts.append(f"📈 **Predicted Average Daily Sales:** {avg_forecast:.1f} units")
            response_parts.append(f"📦 **Total Forecast Sales:** {total_forecast:.0f} units")
            
            if result.get('plot_path'):
                response_parts.append(f"📊 **Visualization Created:** {os.path.basename(result['plot_path'])}")
            
            if result.get('parquet_path'):
                response_parts.append(f"💾 **Data Export:** {os.path.basename(result['parquet_path'])}")
            
            # Add forecast insights
            response_parts.append("\n**📋 Forecast Summary:**")
            
            # Weekly pattern analysis
            if len(future_forecast) >= 7:
                weekly_avg = future_forecast.head(7)['yhat'].mean()
                response_parts.append(f"• Next 7 days average: {weekly_avg:.1f} units/day")
            
            # Trend analysis
            if len(future_forecast) >= 2:
                trend_start = future_forecast['yhat'].iloc[0]
                trend_end = future_forecast['yhat'].iloc[-1]
                trend_direction = "📈 Increasing" if trend_end > trend_start else "📉 Decreasing" if trend_end < trend_start else "➡️ Stable"
                response_parts.append(f"• Trend: {trend_direction}")
            
            # Add inventory insights if available
            if result.get('inventory_analysis') and result['inventory_analysis'].get('success'):
                inv_analysis = result['inventory_analysis']
                response_parts.append(f"\n**📦 Inventory Management Insights:**")
                
                # Coverage analysis
                coverage = inv_analysis['coverage_analysis']
                response_parts.append(f"• Current Stock: {inv_analysis['current_inventory']:,} units")
                response_parts.append(f"• Coverage: {coverage['coverage_days']} days ({coverage['status']})")
                
                # Reorder analysis
                rop = inv_analysis['reorder_analysis']
                response_parts.append(f"• Reorder Point: {rop['reorder_point']:,} units")
                
                # Financial insights
                financial = inv_analysis['financial_analysis']
                response_parts.append(f"• Expected Revenue: ${financial['expected_revenue']:,.2f}")
                response_parts.append(f"• Profit Margin: {financial['profit_margin']}%")
                
                # Key recommendations
                if inv_analysis.get('recommendations'):
                    response_parts.append(f"• Priority: {inv_analysis['recommendations'][0]}")
            
            result['response_text'] = "\n".join(response_parts)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_text': f"❌ **Forecast Error:** Unable to generate forecast. {str(e)}"
            }


def create_forecasting_agent(db_manager: DatabaseManager) -> ForecastingAgent:
    """
    Factory function to create a forecasting agent.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        ForecastingAgent instance
    """
    return ForecastingAgent(db_manager)


# Example usage and testing
if __name__ == "__main__":
    # Test the forecasting agent
    from database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    forecasting_agent = ForecastingAgent(db_manager)
    
    # Test forecast generation
    test_questions = [
        "forecast vanilla ice cream sales for next 30 days",
        "predict milk sales for next week and save as parquet",
        "show me a forecast for FOODS_3_090 for 14 days"
    ]
    
    for question in test_questions:
        print(f"\n🧪 Testing: {question}")
        result = forecasting_agent.process_forecast_request(question)
        print(f"✅ Success: {result['success']}")
        if result['success']:
            print(f"📊 Item: {result['item_id']}")
            print(f"📅 Days: {result['forecast_days']}")
            if result['plot_path']:
                print(f"🎨 Plot: {result['plot_path']}")
            if result['parquet_path']:
                print(f"💾 Data: {result['parquet_path']}")
        else:
            print(f"❌ Error: {result['error']}")