import duckdb
import pandas as pd
from typing import List, Dict, Any
import os

class DatabaseManager:
    """Manages DuckDB database connections and queries for retail data."""
    
    def __init__(self, db_path: str = None):
        # Default to the retail.duckdb in the notebooks directory
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "notebooks", "retail.duckdb")
        else:
            self.db_path = db_path
    
    def get_connection(self):
        """Get a DuckDB connection."""
        return duckdb.connect(self.db_path)
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table."""
        with self.get_connection() as con:
            try:
                # Get column information
                columns = con.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """).fetchall()
                
                # Get sample data
                sample_data = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "sample_data": sample_data
                }
            except Exception as e:
                return {"error": f"Error getting schema for {table_name}: {str(e)}"}
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        with self.get_connection() as con:
            tables = con.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            """).fetchall()
            return [table[0] for table in tables]
    
    def execute_query(self, query: str, params=None) -> Dict[str, Any]:
        """Execute a SQL query and return results."""
        with self.get_connection() as con:
            try:
                if params:
                    result = con.execute(query, params).df()
                else:
                    result = con.execute(query).df()
                return {
                    "success": True,
                    "data": result,
                    "row_count": len(result)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "data": None,
                    "row_count": 0
                }
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the database."""
        summary = {
            "tables": {},
            "table_descriptions": {
                "sales": "Contains sales transaction data with item sales information",
                "inv": "Contains inventory data for items",
                "item_dim": "Contains item dimension/master data with item details"
            }
        }
        
        tables = self.get_all_tables()
        for table in tables:
            schema_info = self.get_table_schema(table)
            if "error" not in schema_info:
                summary["tables"][table] = schema_info
        
        return summary
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Alias for get_database_summary for compatibility."""
        return self.get_database_summary()