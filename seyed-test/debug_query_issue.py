#!/usr/bin/env python3
"""
Debug script to identify where the regular queries are failing
"""

import os
from dotenv import load_dotenv
load_dotenv()

from database_manager import DatabaseManager
from query_agents import QueryGeneratorAgent

def debug_query_generation():
    """Debug the query generation process step by step."""
    
    print("🔧 Debugging Query Generation Process")
    print("=" * 50)
    
    try:
        # Test 1: Database Manager
        print("1. Testing DatabaseManager...")
        db = DatabaseManager()
        print("   ✅ DatabaseManager initialized")
        
        # Test 2: Get schema
        print("2. Getting database schema...")
        schema = db.get_database_schema()
        print(f"   Schema keys: {list(schema.keys())}")
        print(f"   Tables: {list(schema.get('tables', {}).keys())}")
        
        # Test 3: Query Generator
        print("3. Testing QueryGeneratorAgent...")
        query_gen = QueryGeneratorAgent()
        print("   ✅ QueryGeneratorAgent initialized")
        
        # Test 4: Generate a simple query
        print("4. Generating query for 'top 3 sellers'...")
        result = query_gen.generate_query("what are the top 3 best sellers?", schema)
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   Query: {result.get('query')}")
            print(f"   Explanation: {result.get('explanation')}")
        else:
            print(f"   Error: {result.get('error')}")
            
        # Test 5: Execute the query if generated successfully
        if result.get('success') and result.get('query'):
            print("5. Executing generated query...")
            exec_result = db.execute_query(result['query'])
            print(f"   Execution success: {exec_result.get('success', False)}")
            if exec_result.get('success'):
                print(f"   Rows returned: {len(exec_result.get('data', []))}")
            else:
                print(f"   Execution error: {exec_result.get('error')}")
        
    except Exception as e:
        print(f"❌ Error in debug process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_query_generation()