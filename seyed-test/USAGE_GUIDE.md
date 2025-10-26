# 🛒 LangGraph Retail Data Query System

A sophisticated LangGraph-based system that transforms natural language questions about retail data into SQL queries and returns human-readable answers.

## 📋 Overview

This system consists of two main modes:
1. **Full LangGraph Mode**: Uses LLM to convert natural language to SQL
2. **Simple Demo Mode**: Basic SQL interface without LLM dependencies

## 🗂️ Database Schema

Your retail database contains:

- **`sales`**: 1,001 sales records with columns:
  - `item_id`: Product identifier (e.g., "FOODS_3_090")
  - `date`: Sale date
  - `sale`: Sale amount/quantity

- **`inv`**: 11 inventory records with columns:
  - `item_id`: Product identifier
  - `unit`: Units in inventory

- **`item_dim`**: 11 item master records with product details

## 🚀 Quick Start

### Option 1: Simple Demo (No Setup Required)
```bash
cd /Users/shtabari/Documents/AITX/backroom/seyed-test
python simple_demo.py
```

### Option 2: Full LangGraph System
```bash
# Install dependencies
pip install -r requirements.txt

# Set up OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the full system
python main.py
```

## 📁 Files Created

```
seyed-test/
├── 📄 main.py                    # Full LangGraph CLI interface
├── 🧠 retail_query_graph.py      # LangGraph workflow implementation
├── 🔍 query_agents.py            # LLM agents (query generation & formatting)
├── 🗄️ database_manager.py        # DuckDB connection and operations
├── 🎮 simple_demo.py             # Demo without LLM (works immediately)
├── 🧪 test_system.py             # Test suite
├── 🌐 streamlit_app.py           # Web interface
├── ⚙️ setup.py                  # Installation helper
├── 📦 requirements.txt           # Python dependencies
├── 🔧 .env.example              # Environment variables template
└── 📚 README.md                 # Documentation
```

## 🎯 Example Queries (Natural Language)

Once you have the full system set up with LangGraph, you can ask:

- **"Show me the top 10 selling items"**
- **"What's the total sales revenue?"**
- **"Which items have low inventory?"**
- **"How many sales were there in the last week?"**
- **"Show me items that sold more than 500 units"**
- **"What's the average sale amount per item?"**

## 🎮 Simple Demo Usage

The simple demo works immediately and supports:

**Keywords:**
- `sales count` → Count all sales
- `inventory sample` → Show inventory sample  
- `item sample` → Show item sample

**Direct SQL:**
```sql
SELECT * FROM sales WHERE sale > 500
SELECT item_id, SUM(sale) as total FROM sales GROUP BY item_id
SELECT * FROM inv WHERE unit < 1000
```

## 🏗️ LangGraph Architecture

The full system uses this workflow:

1. **analyze_question** → Parse user input & load schema
2. **generate_query** → LLM converts natural language to SQL
3. **execute_query** → Run SQL against DuckDB
4. **format_response** → LLM formats results into natural language
5. **handle_error** → Graceful error handling

## 🔧 System Requirements

**Minimum (Simple Demo):**
- Python 3.8+
- DuckDB
- Pandas

**Full System:**
- All above, plus:
- LangGraph
- LangChain
- OpenAI API key

## 🎈 Next Steps

1. **Try the simple demo** to see your data structure
2. **Set up OpenAI API key** for natural language queries
3. **Install full requirements** for LangGraph features
4. **Run streamlit app** for web interface: `streamlit run streamlit_app.py`

## 💡 Sample Interactions

**Simple Demo:**
```
💭 Enter a SQL query: SELECT item_id, SUM(sale) as total_sales FROM sales GROUP BY item_id LIMIT 5

✅ Found 5 records:
    item_id  total_sales
FOODS_3_090       77821
FOODS_3_226        8247  
FOODS_3_252       13140
FOODS_3_333       12891
FOODS_3_340       19238
```

**Full LangGraph System:**
```
🤔 Your question: Which items sold the most?

🤖 Based on your sales data, here are the top-selling items:

1. **FOODS_3_090**: 77,821 total sales - This is clearly your bestseller!
2. **FOODS_3_340**: 19,238 total sales  
3. **FOODS_3_252**: 13,140 total sales

The item FOODS_3_090 significantly outperforms others, generating almost 4x more sales than the second-best item. You might want to ensure adequate inventory for this high-performer!
```

## ✅ Validation

The system has been tested and works with your retail database containing:
- ✅ 1,001 sales records
- ✅ 11 inventory items  
- ✅ 11 item dimension records
- ✅ Proper database connections
- ✅ SQL query execution
- ✅ Error handling

Ready to start querying your retail data! 🎉