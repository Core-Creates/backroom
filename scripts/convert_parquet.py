#!/usr/bin/env python3
"""
Convert Parquet files to JSON for easier frontend consumption
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path

def convert_parquet_to_json(parquet_path: str, output_path: str = None):
    """Convert a Parquet file to JSON format"""
    try:
        # Read Parquet file
        df = pd.read_parquet(parquet_path)
        
        # Convert to JSON
        if output_path is None:
            output_path = parquet_path.replace('.parquet', '.json')
        
        # Convert to records format (list of dictionaries)
        records = df.to_dict('records')
        
        # Write JSON file
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2, default=str)
        
        print(f"✅ Converted {parquet_path} to {output_path}")
        print(f"📊 Records: {len(records)}")
        print(f"📋 Columns: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting {parquet_path}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_parquet.py <parquet_file> [output_file]")
        print("Example: python convert_parquet.py data/inventory.parquet")
        sys.exit(1)
    
    parquet_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(parquet_file):
        print(f"❌ File not found: {parquet_file}")
        sys.exit(1)
    
    success = convert_parquet_to_json(parquet_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

