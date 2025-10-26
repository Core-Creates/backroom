# Retail Data Query System with LangGraph

A LangGraph-based system that allows users to ask natural language questions about retail data and automatically generates and executes SQL queries to provide answers.

## Features

- **Natural Language to SQL**: Ask questions in plain English about your retail data
- **Multi-table Support**: Automatically handles queries across sales, inventory, and item dimension tables
- **LangGraph Workflow**: Uses LangGraph for robust query processing pipeline
- **Error Handling**: Graceful error handling and informative error messages
- **Chat Interface**: Maintains conversation history for follow-up questions

## Database Schema

The system works with three main tables:

- **`sales`**: Sales transaction data
- **`inv`**: Inventory data for items  
- **`item_dim`**: Item master data and dimensions

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Test the system:**
   ```bash
   python test_system.py
   ```

## Usage

### Command Line Interface

```bash
# Start the interactive CLI
python main.py

# See example queries
python main.py examples
```

### Example Questions

Here are some questions you can ask:

- "Show me the top 10 selling items"
- "What's the total sales revenue?"
- "How many items are in inventory?" 
- "Which items have low stock levels?"
- "Show sales data for the last month"
- "What are the most popular product categories?"
- "Compare sales across different time periods"

### Programmatic Usage

```python
from retail_query_graph import RetailDataQueryGraph
from langchain_core.messages import HumanMessage

# Initialize the system
query_system = RetailDataQueryGraph()

# Ask a question
response = query_system.query("What are the top selling items?")
print(response)

# Or use the chat interface
messages = [HumanMessage(content="Show me inventory levels")]
updated_messages = query_system.chat(messages)
print(updated_messages[-1].content)
```

## Architecture

The system uses a LangGraph workflow with the following nodes:

1. **analyze_question**: Analyzes user input and loads database schema
2. **generate_query**: Uses LLM to convert natural language to SQL
3. **execute_query**: Executes the generated query against the database
4. **format_response**: Formats results into natural language response
5. **handle_error**: Handles any errors that occur during processing

## Files Structure

```
seyed-test/
├── main.py                    # CLI interface
├── retail_query_graph.py      # Main LangGraph implementation
├── query_agents.py            # LLM agents for query generation and formatting
├── database_manager.py        # DuckDB database operations
├── test_system.py             # Test suite
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Dependencies

- **LangGraph**: Workflow orchestration
- **LangChain**: LLM integration and message handling
- **DuckDB**: Database operations
- **OpenAI**: Language model (configurable)
- **Pandas**: Data manipulation

## Configuration

The system uses environment variables for configuration:

- `OPENAI_API_KEY`: Your OpenAI API key for GPT models
- Database path is automatically detected from the parent notebooks directory

## Error Handling

The system includes comprehensive error handling:

- Database connection errors
- SQL syntax errors  
- LLM API errors
- Invalid user input

All errors are presented to users in a friendly format with suggestions for resolution.

## Extending the System

To extend the system:

1. **Add new tables**: Update the `database_manager.py` schema descriptions
2. **Custom LLM**: Replace the ChatOpenAI instance with your preferred model
3. **Additional agents**: Add new nodes to the LangGraph workflow
4. **Custom formatting**: Modify the `ResponseFormatterAgent` for different output formats

## Troubleshooting

1. **Database not found**: Ensure the `retail.duckdb` file exists in the notebooks directory
2. **Import errors**: Install all requirements with `pip install -r requirements.txt`
3. **API key errors**: Verify your OpenAI API key is set in the `.env` file
4. **Query errors**: Check that your database tables have the expected schema

## License

This project is part of the AITX backroom system.