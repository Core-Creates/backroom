#!/usr/bin/env python3
"""
Working CLI for the retail intelligence system
"""

import os
import sys
from dotenv import load_dotenv
from retail_query_graph import RetailDataQueryGraph

# Load environment variables
load_dotenv()

def main():
    """Interactive CLI that works properly."""
    
    print("🛒 Retail Intelligence System")
    print("=" * 50)
    print("Ask questions about your retail data!")
    print("Examples:")
    print("  • 'what are the top 5 selling items?'")
    print("  • 'forecast vanilla ice cream for 2 weeks'") 
    print("  • 'show me sales in a bar chart'")
    print("Type 'quit' to exit\n")
    
    # Initialize system
    try:
        system = RetailDataQueryGraph()
        print("✅ System ready!\n")
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        return
    
    # Interactive loop
    while True:
        try:
            # Get user input with proper error handling
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q', '']:
                print("👋 Goodbye!")
                break
                
            # Process the question
            print("🔍 Processing...")
            response = system.query(question)
            
            # Display response
            print(f"\n🤖 {response}\n")
            print("-" * 50)
            
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_mode():
    """Run predefined demo queries."""
    
    print("🚀 DEMO MODE - Retail Intelligence System")
    print("=" * 60)
    
    system = RetailDataQueryGraph()
    
    demo_queries = [
        ("Data Analysis", "what are the top 3 best sellers?"),
        ("Visualization", "show me top selling items in a bar chart"),
        ("Forecasting", "forecast vanilla ice cream for next 14 days")
    ]
    
    for i, (category, query) in enumerate(demo_queries, 1):
        print(f"\n{i}. {category}: '{query}'")
        print("=" * 50)
        
        try:
            response = system.query(query)
            # Show preview of response
            preview = response[:400] + "..." if len(response) > 400 else response
            print(f"Response: {preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    # Check if demo mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_mode()
    else:
        main()