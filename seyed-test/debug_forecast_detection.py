#!/usr/bin/env python3
"""
Debug script to check forecasting detection
"""

import os
from dotenv import load_dotenv
load_dotenv()

from retail_query_graph import RetailDataQueryGraph

def test_forecast_detection():
    system = RetailDataQueryGraph()
    
    # Test forecast detection directly
    questions = [
        "forecast vanilla ice cream sales for next 30 days",
        "predict milk sales for the next 2 weeks", 
        "show me regular sales data"
    ]
    
    for q in questions:
        print(f"\nQuestion: {q}")
        
        # Test the forecasting agent detection
        forecast_needed = system.forecasting_agent.should_create_forecast(q)
        print(f"Forecast needed: {forecast_needed}")
        
        # Test the visualization agent detection  
        viz_needed = system.visualization_agent.should_create_visualization(q)
        print(f"Visualization needed: {viz_needed}")

if __name__ == "__main__":
    test_forecast_detection()