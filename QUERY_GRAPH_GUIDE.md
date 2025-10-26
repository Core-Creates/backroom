# Query-Based Graph Generation Guide

This guide explains how to use the natural language query system to generate dynamic graphs based on your questions.

## 🚀 Quick Start

### 1. Access the Query Interface
1. Go to http://localhost:3000
2. Click the **"Query Graphs"** tab
3. Type your question in the text box
4. Click "Ask" or press Enter

### 2. Example Queries
Try these example questions to get started:

**Trend Analysis:**
- "Show me stock trends for SKU-001 over the last month"
- "Show me the trend of organic apples over time"
- "How has milk inventory changed recently?"

**Comparisons:**
- "Compare inventory levels across all products"
- "Compare dairy products vs fresh produce"
- "Show me which items have the highest stock"

**Forecasting:**
- "Forecast demand for the next week"
- "Predict when we will run out of milk"
- "Show me future stock levels for SKU-002"

**Analysis:**
- "Analyze the relationship between sales and stock levels"
- "Why are some items running low?"
- "What's causing inventory fluctuations?"

**Summaries:**
- "Give me a summary of high priority items"
- "Show me total inventory by category"
- "What's the overall inventory status?"

## 🧠 How It Works

### 1. Natural Language Processing
The system analyzes your question to understand:
- **Intent Type**: What kind of analysis you want (trend, comparison, forecast, etc.)
- **Entities**: Which products, SKUs, or categories you're asking about
- **Timeframe**: What time period you're interested in
- **Metrics**: What data you want to see (stock levels, sales, etc.)

### 2. Data Retrieval
Based on your question, the system:
- Fetches relevant data from your Parquet files
- Filters by specific SKUs or categories if mentioned
- Gets historical data for trend analysis
- Applies time-based filters

### 3. Graph Generation
The system automatically:
- Chooses the best chart type for your question
- Configures axes and labels appropriately
- Applies styling and colors
- Adds relevant annotations

## 📊 Supported Chart Types

### Line Charts
- **Use for**: Trends over time, forecasting
- **Example**: "Show me stock trends for SKU-001"
- **Features**: Time series data, trend lines, forecast projections

### Bar Charts
- **Use for**: Comparisons between items
- **Example**: "Compare inventory levels across products"
- **Features**: Side-by-side comparisons, category breakdowns

### Scatter Plots
- **Use for**: Correlation analysis, relationships
- **Example**: "Analyze sales vs stock levels"
- **Features**: Data point relationships, correlation patterns

### Area Charts
- **Use for**: Cumulative data, volume over time
- **Example**: "Show me total inventory over time"
- **Features**: Filled areas, cumulative values

### Pie Charts
- **Use for**: Proportions, summaries
- **Example**: "Show me inventory by category"
- **Features**: Percentage breakdowns, category distributions

## 🎯 Query Patterns

### SKU-Specific Queries
```
"Show me trends for SKU-001"
"Forecast SKU-002 for next week"
"Analyze SKU-003 performance"
```

### Category-Based Queries
```
"Compare dairy vs fresh produce"
"Show me all bakery items"
"Analyze health & beauty products"
```

### Time-Based Queries
```
"Show me last month's trends"
"Forecast next week"
"Compare this year vs last year"
```

### Metric-Specific Queries
```
"Show me sales trends"
"Compare stock levels"
"Analyze demand patterns"
"Show me revenue by category"
```

## 🔧 Advanced Features

### Intent Recognition
The system recognizes these intent types:
- **trend**: "show trends", "over time", "change"
- **comparison**: "compare", "vs", "versus"
- **forecast**: "forecast", "predict", "future"
- **analysis**: "analyze", "why", "relationship"
- **summary**: "summary", "overview", "total"

### Entity Extraction
Automatically identifies:
- **SKUs**: "SKU-001", "SKU-002"
- **Categories**: "dairy", "fresh produce", "bakery"
- **Products**: "milk", "apples", "bread"
- **Timeframes**: "last month", "next week", "this year"

### Smart Filtering
- Filters data based on your question context
- Applies category filters when mentioned
- Gets historical data for specific SKUs
- Handles time-based queries

## 📈 Real Data Integration

### Parquet File Support
- Works with your uploaded Parquet files
- Automatically converts to JSON for frontend
- Supports both inventory and historical data
- Handles large datasets efficiently

### API Integration
- Fetches data from `/api/inventory/real`
- Gets history from `/api/inventory/history/{sku}`
- Real-time data updates
- Error handling and fallbacks

## 🎨 Customization

### Chart Styling
- Automatic color schemes
- Responsive design
- Interactive elements
- Professional styling

### Data Formatting
- Smart axis labels
- Appropriate number formatting
- Date formatting
- Unit handling

## 🚨 Troubleshooting

### Common Issues

1. **No Data Showing**
   - Check if Parquet files are uploaded
   - Verify data format matches expected schema
   - Check browser console for errors

2. **Query Not Working**
   - Try simpler, more specific questions
   - Use exact SKU names (e.g., "SKU-001")
   - Check spelling of categories

3. **Graph Not Rendering**
   - Refresh the page
   - Check if data is available
   - Try a different query

### Debug Tips
```bash
# Check if data is available
curl http://localhost:3000/api/inventory/real

# Check specific SKU history
curl http://localhost:3000/api/inventory/history/SKU-001

# Check browser console for errors
# Open Developer Tools (F12) and look at Console tab
```

## 🎉 Success!

Your query-based graph generation system is now fully functional! You can:

1. **Ask Natural Questions**: Use plain English to ask about your data
2. **Get Instant Visualizations**: See graphs generated automatically
3. **Explore Real Data**: Work with your actual Parquet data
4. **Save Queries**: Access recent queries for quick reference
5. **Multiple Chart Types**: Get the right visualization for each question

The system intelligently understands your questions and generates appropriate visualizations, making data analysis as simple as asking a question! 🎉

