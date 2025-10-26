#!/usr/bin/env python3
"""
Quick CLI for one-shot queries
"""

import sys
import os
from dotenv import load_dotenv
from retail_query_graph import RetailDataQueryGraph

load_dotenv()

def quick_query(question):
    """Run a single query and exit."""
    try:
        system = RetailDataQueryGraph()
        response = system.query(question)
        print(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line argument mode
        question = " ".join(sys.argv[1:])
        quick_query(question)
    else:
        print("Usage: python quick.py 'your question here'")
        print("Examples:")
        print("  python quick.py 'what are the top 5 sellers?'")
        print("  python quick.py 'forecast milk for 10 days'")
        print("  python quick.py 'show sales in a pie chart'")