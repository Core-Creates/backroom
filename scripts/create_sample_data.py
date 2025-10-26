#!/usr/bin/env python3
"""
Create sample Parquet files for testing the inventory system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_sample_inventory_data():
    """Create sample inventory data"""
    data = {
        'sku': [
            'SKU-001', 'SKU-002', 'SKU-003', 'SKU-004', 'SKU-005',
            'SKU-006', 'SKU-007', 'SKU-008', 'SKU-009', 'SKU-010'
        ],
        'product_name': [
            'Premium Shampoo', 'Conditioner', 'Body Lotion', 'Organic Apples',
            'Whole Milk', 'Bread Loaf', 'Chicken Breast', 'Eggs (Dozen)',
            'Bananas', 'Orange Juice'
        ],
        'category': [
            'Health & Beauty', 'Health & Beauty', 'Health & Beauty', 'Fresh Produce',
            'Dairy & Eggs', 'Bakery', 'Meat & Seafood', 'Dairy & Eggs',
            'Fresh Produce', 'Beverages'
        ],
        'on_hand': [150, 75, 200, 45, 60, 25, 30, 40, 80, 35],
        'backroom_units': [100, 50, 150, 30, 40, 15, 20, 25, 50, 20],
        'shelf_units': [50, 25, 50, 15, 20, 10, 10, 15, 30, 15],
        'avg_daily_sales': [12.5, 8.2, 15.3, 18.7, 22.1, 14.2, 9.8, 16.5, 25.3, 11.7],
        'lead_time_days': [7, 5, 10, 3, 2, 1, 4, 2, 3, 5],
        'cost_per_unit': [8.50, 6.75, 4.25, 1.25, 2.15, 1.80, 4.50, 2.80, 0.75, 2.45],
        'selling_price': [15.99, 12.99, 9.99, 2.99, 4.49, 3.49, 8.99, 4.99, 1.49, 4.99],
        'supplier': [
            'Beauty Supply Co', 'Beauty Supply Co', 'Personal Care Inc', 'Fresh Farms',
            'Dairy Fresh', 'Local Bakery', 'Meat Market', 'Dairy Fresh',
            'Fresh Farms', 'Beverage Co'
        ],
        'last_updated': [datetime.now().isoformat()] * 10
    }
    
    df = pd.DataFrame(data)
    return df

def create_sample_history_data():
    """Create sample inventory history data"""
    skus = ['SKU-001', 'SKU-002', 'SKU-003', 'SKU-004', 'SKU-005']
    history_data = []
    
    for sku in skus:
        # Generate 30 days of history
        for i in range(30):
            date = datetime.now() - timedelta(days=29-i)
            
            # Simulate realistic inventory changes
            base_stock = 100 + np.random.normal(0, 20)
            daily_demand = 10 + np.random.normal(0, 3)
            stock_level = max(0, int(base_stock - (daily_demand * (29-i))))
            
            history_data.append({
                'sku': sku,
                'date': date.strftime('%Y-%m-%d'),
                'stock_level': stock_level,
                'demand': max(0, daily_demand),
                'reorder_point': 50,
                'cost': 5 + np.random.normal(0, 1),
                'revenue': 10 + np.random.normal(0, 2)
            })
    
    df = pd.DataFrame(history_data)
    return df

def main():
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Create sample inventory data
    print("Creating sample inventory data...")
    inventory_df = create_sample_inventory_data()
    inventory_df.to_parquet('data/inventory.parquet', index=False)
    inventory_df.to_json('data/inventory.json', orient='records', indent=2)
    print("✅ Created data/inventory.parquet and data/inventory.json")
    
    # Create sample history data
    print("Creating sample inventory history data...")
    history_df = create_sample_history_data()
    history_df.to_parquet('data/inventory_history.parquet', index=False)
    history_df.to_json('data/inventory_history.json', orient='records', indent=2)
    print("✅ Created data/inventory_history.parquet and data/inventory_history.json")
    
    print("\n📊 Sample data created successfully!")
    print("You can now:")
    print("1. View the data in your frontend at http://localhost:3000")
    print("2. Upload your own Parquet files using the 'Parquet Data' tab")
    print("3. Use the conversion script: python scripts/convert_parquet.py data/your_file.parquet")

if __name__ == "__main__":
    main()

