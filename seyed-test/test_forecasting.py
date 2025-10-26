#!/usr/bin/env python3
"""
Test script for the forecasting agent integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OpenAI API key not found in environment variables")
    sys.exit(1)

from retail_query_graph import RetailDataQueryGraph

def test_forecasting_agent():
    """Test the forecasting agent with various queries."""
    
    print("🚀 Testing Forecasting Agent Integration")
    print("=" * 50)
    
    # Initialize system
    try:
        system = RetailDataQueryGraph()
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    # Test queries
    forecast_queries = [
        "forecast vanilla ice cream sales for next 30 days",
        "predict milk sales for the next 2 weeks",
        "show me a forecast for chocolate ice cream for next month and save as parquet",
        "forecast FOODS_3_090 sales for 14 days with visualization"
    ]
    
    print(f"\n🧪 Running {len(forecast_queries)} forecast tests...\n")
    
    for i, query in enumerate(forecast_queries, 1):
        print(f"{i}. Testing: '{query}'")
        print("-" * 60)
        
        try:
            response = system.query(query)
            print("✅ Response:")
            print(response)
            
            if "forecast" in response.lower() or "prediction" in response.lower():
                print("✅ Forecast response detected")
            else:
                print("⚠️  Forecast response not clearly detected")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*60 + "\n")
    
    # Check created files
    print("📁 Checking for generated files...")
    
    # Check forecasts directory
    if os.path.exists("forecasts"):
        files = os.listdir("forecasts")
        print(f"📊 Forecast files created: {len(files)}")
        for f in files:
            print(f"   • {f}")
    else:
        print("📂 No forecasts directory found")
    
    print("\n🎯 Forecasting Agent Test Complete!")

if __name__ == "__main__":
    test_forecasting_agent()