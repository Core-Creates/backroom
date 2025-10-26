#!/usr/bin/env python3
"""
Simple test script to verify the retail data query system works.
Run this after installing dependencies to test basic functionality.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_connection():
    """Test database connection and basic queries."""
    print("🧪 Testing Database Connection...")
    
    try:
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        tables = db.get_all_tables()
        
        print(f"✅ Found {len(tables)} tables: {tables}")
        
        # Test basic query
        result = db.execute_query("SELECT COUNT(*) as total FROM sales")
        if result["success"]:
            print(f"✅ Sales table has {result['data'].iloc[0, 0]} records")
        else:
            print(f"❌ Error querying sales: {result['error']}")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_without_llm():
    """Test the system without LLM components."""
    print("\n🧪 Testing Basic Query Generation (without LLM)...")
    
    try:
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        
        # Test some basic queries manually
        queries = [
            "SELECT COUNT(*) as total_sales FROM sales",
            "SELECT COUNT(*) as total_inventory FROM inv",
            "SELECT COUNT(*) as total_items FROM item_dim"
        ]
        
        for query in queries:
            result = db.execute_query(query)
            if result["success"]:
                print(f"✅ {query}: {result['data'].iloc[0, 0]} records")
            else:
                print(f"❌ {query}: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Retail Data Query System - Test Suite")
    print("=" * 50)
    
    # Test 1: Database connection
    if not test_database_connection():
        return False
    
    # Test 2: Basic functionality without LLM
    if not test_without_llm():
        return False
    
    print("\n✅ All basic tests passed!")
    print("\n💡 Next steps:")
    print("1. Set up your OpenAI API key in .env file")
    print("2. Install LangGraph dependencies: pip install -r requirements.txt")
    print("3. Run: python main.py")
    
    return True

if __name__ == "__main__":
    main()