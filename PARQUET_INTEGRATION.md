# Parquet Data Integration Guide

This guide explains how to integrate real-life data using Parquet files in your Backroom inventory management system.

## 🚀 Quick Start

### 1. Sample Data Available
Sample Parquet files have been created in the `data/` directory:
- `data/inventory.parquet` - Main inventory data
- `data/inventory_history.parquet` - Historical inventory trends
- `data/inventory.json` - JSON version for frontend
- `data/inventory_history.json` - JSON version for frontend

### 2. View Real Data
Visit http://localhost:3000 and navigate to:
- **Overview Tab**: See real inventory data
- **Forecast Tab**: Click any row to see real historical trends
- **Parquet Data Tab**: Upload your own Parquet files

## 📊 Data Structure

### Inventory Data Format
Your Parquet files should contain these columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `sku` | string | ✅ | Product SKU identifier |
| `product_name` | string | ✅ | Product name |
| `category` | string | ❌ | Product category |
| `on_hand` | number | ✅ | Current stock level |
| `backroom_units` | number | ✅ | Backroom inventory |
| `shelf_units` | number | ✅ | Shelf inventory |
| `avg_daily_sales` | number | ✅ | Average daily sales |
| `lead_time_days` | number | ✅ | Lead time in days |
| `cost_per_unit` | number | ❌ | Cost per unit |
| `selling_price` | number | ❌ | Selling price |
| `supplier` | string | ❌ | Supplier name |
| `last_updated` | string | ❌ | Last update timestamp |

### History Data Format
For historical trends, use these columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `sku` | string | ✅ | Product SKU identifier |
| `date` | string | ✅ | Date (YYYY-MM-DD format) |
| `stock_level` | number | ✅ | Stock level on that date |
| `demand` | number | ✅ | Daily demand |
| `reorder_point` | number | ✅ | Reorder point threshold |
| `cost` | number | ❌ | Daily cost |
| `revenue` | number | ❌ | Daily revenue |

## 🛠️ How to Use

### Method 1: Upload via Frontend
1. Go to http://localhost:3000
2. Click the "Parquet Data" tab
3. Drag and drop your Parquet file
4. Click "Upload & Convert"
5. The system will automatically convert to JSON

### Method 2: Direct File Placement
1. Place your Parquet files in the `data/` directory
2. Run the conversion script:
   ```bash
   python3 scripts/convert_parquet.py data/your_file.parquet
   ```
3. Restart your frontend to see the data

### Method 3: Programmatic Integration
```python
import pandas as pd

# Read your Parquet file
df = pd.read_parquet('your_inventory_data.parquet')

# Ensure it has the required columns
required_columns = ['sku', 'product_name', 'on_hand', 'backroom_units', 'shelf_units', 'avg_daily_sales', 'lead_time_days']
df = df[required_columns]

# Save as JSON for frontend consumption
df.to_json('data/inventory.json', orient='records', indent=2)
```

## 🔧 API Endpoints

### Get Real Inventory Data
```http
GET /api/inventory/real
```
Returns the current inventory data from Parquet/JSON files.

### Get Inventory History
```http
GET /api/inventory/history/{sku}
```
Returns historical data for a specific SKU.

### Upload Parquet File
```http
POST /api/upload/parquet
Content-Type: multipart/form-data

file: your_file.parquet
```

## 📈 Features

### Real Data Visualization
- **Inventory Dashboard**: Shows real stock levels, categories, and metrics
- **Interactive Charts**: Click any item in the forecast table to see real historical trends
- **Category Filtering**: Use the dropdown to filter by grocery categories
- **Real-time Updates**: Data updates automatically when you upload new files

### Data Processing
- **Automatic Conversion**: Parquet files are converted to JSON for frontend consumption
- **Error Handling**: Graceful fallback to mock data if real data isn't available
- **Type Safety**: Full TypeScript support for data structures

## 🎯 Use Cases

### 1. Retail Inventory Management
- Upload daily inventory snapshots
- Track stock levels over time
- Identify reorder points
- Analyze sales patterns

### 2. Supply Chain Analytics
- Monitor supplier performance
- Track lead times
- Analyze cost trends
- Forecast demand

### 3. Business Intelligence
- Generate reports from real data
- Create dashboards with live data
- Export insights to other systems
- Integrate with existing data pipelines

## 🔄 Data Flow

```
Parquet File → Upload API → Data Service → Frontend Components
     ↓
JSON Conversion → Real-time Display → Interactive Charts
```

## 🚨 Troubleshooting

### Common Issues

1. **File Not Found Error**
   - Ensure Parquet files are in the `data/` directory
   - Check file permissions
   - Verify file format (.parquet extension)

2. **Conversion Errors**
   - Run: `python3 scripts/convert_parquet.py data/your_file.parquet`
   - Check column names match the expected format
   - Verify data types are correct

3. **Frontend Not Showing Data**
   - Restart the Next.js development server
   - Check browser console for errors
   - Verify API endpoints are working

### Debug Commands
```bash
# Check if data files exist
ls -la data/

# Test Parquet conversion
python3 scripts/convert_parquet.py data/inventory.parquet

# Check API endpoints
curl http://localhost:3000/api/inventory/real
```

## 📚 Next Steps

1. **Customize Data Structure**: Modify the data service to match your specific data format
2. **Add More Visualizations**: Create additional charts and graphs
3. **Real-time Updates**: Implement WebSocket connections for live data
4. **Data Validation**: Add schema validation for uploaded files
5. **Export Features**: Add ability to export data in various formats

## 🎉 Success!

Your system now supports real-life data through Parquet files! The frontend will automatically display your actual inventory data, and the charts will show real historical trends. This makes your inventory management system much more powerful and useful for real business operations.

