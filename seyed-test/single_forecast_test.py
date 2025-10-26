#!/usr/bin/env python3
"""
Single forecast test with proper environment setup
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ OpenAI API key not found")
    exit(1)

from retail_query_graph import RetailDataQueryGraph

# Initialize system
system = RetailDataQueryGraph()

# Test a single forecast
print("🔮 Testing single forecast query...")
response = system.query("forecast vanilla ice cream for 30 days")
print("\nResponse:")
print(response)