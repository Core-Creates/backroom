from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, TypedDict
import re
import json

class QueryGeneratorAgent:
    """Generates SQL queries based on natural language questions about retail data."""
    
    def __init__(self, llm=None):
        if llm is None:
            self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        else:
            self.llm = llm
    
    def generate_query(self, question: str, database_schema: Dict[str, Any], 
                      conversation_context: str = None) -> Dict[str, Any]:
        """Generate SQL query based on user question, database schema, and conversation context."""
        
        schema_context = self._format_schema_context(database_schema)
        
        # Build context-aware prompt
        context_section = ""
        if conversation_context:
            context_section = f"""
Previous Conversation Context:
{conversation_context}

This context may help understand references like 'those items', 'the previous results', etc.
"""
        
        prompt = f"""
You are a SQL expert working with a retail database. Based on the user's question and conversation context, generate an appropriate SQL query.

Database Schema:
{schema_context}

{context_section}

User Question: {question}

Guidelines:
1. Only use tables and columns that exist in the schema
2. Return a valid DuckDB-compatible SQL query
3. Use appropriate JOINs when data spans multiple tables
4. Add LIMIT clauses for exploratory queries to avoid large results
5. Use proper aggregations when asking for summaries or totals
6. If the question references previous results or uses pronouns, use the context to understand what they mean
7. For follow-up questions, build upon previous queries when relevant
8. If the question is ambiguous, make reasonable assumptions

Response format - return ONLY a JSON object:
{{
    "query": "SELECT ... FROM ... WHERE ...",
    "explanation": "Brief explanation of what the query does",
    "tables_used": ["table1", "table2"],
    "context_used": "How conversation context influenced this query (if applicable)"
}}
"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "query": result.get("query", ""),
                    "explanation": result.get("explanation", ""),
                    "tables_used": result.get("tables_used", [])
                }
            else:
                return {
                    "success": False,
                    "error": "Could not parse LLM response as JSON"
                }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing error: {str(e)}"
            }
    
    def _format_schema_context(self, database_schema: Dict[str, Any]) -> str:
        """Format database schema for LLM context."""
        context = []
        
        context.append("Available Tables:")
        for table_name, description in database_schema.get("table_descriptions", {}).items():
            context.append(f"- {table_name}: {description}")
        
        context.append("\nTable Schemas:")
        for table_name, schema_info in database_schema.get("tables", {}).items():
            context.append(f"\n{table_name}:")
            columns = schema_info.get("columns", [])
            for col_name, col_type, nullable in columns:
                context.append(f"  - {col_name} ({col_type})")
            
            # Add sample data
            sample_data = schema_info.get("sample_data", [])
            if sample_data and len(sample_data) > 0:
                context.append(f"  Sample data: {sample_data[0] if len(sample_data) > 0 else 'No sample available'}")
        
        return "\n".join(context)

class ResponseFormatterAgent:
    """Formats query results into human-readable responses."""
    
    def __init__(self, llm=None):
        if llm is None:
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        else:
            self.llm = llm
    
    def format_response(self, question: str, query_result: Dict[str, Any], 
                       query_info: Dict[str, Any] = None) -> str:
        """Format query results into a natural language response."""
        
        if not query_result.get("success", False):
            return f"❌ Error executing query: {query_result.get('error', 'Unknown error')}"
        
        data = query_result.get("data")
        if data is None or len(data) == 0:
            return "📭 No data found matching your query."
        
        # Convert DataFrame to a more readable format
        if hasattr(data, 'to_dict'):
            data_dict = data.to_dict('records')
            data_preview = str(data.head(10)) if len(data) > 10 else str(data)
        else:
            data_dict = data
            data_preview = str(data)
        
        prompt = f"""
You are a retail data analyst AI. Based on the user's question and query results, provide a comprehensive analytical response.

User Question: {question}
Query Executed: {query_info.get('query', 'N/A') if query_info else 'N/A'}
Number of Rows Returned: {len(data)}

Query Results Preview:
{data_preview}

Provide a response with these sections:

📊 **DATA OVERVIEW:**
- Summarize what the data shows
- Present key data points in a readable format

📈 **KEY FINDINGS & INSIGHTS:**
- Analyze patterns, trends, and anomalies
- Compare values (highest/lowest, differences, ratios)
- Identify business implications
- Note any surprising or significant findings

🎯 **BUSINESS RECOMMENDATIONS:**
- What actions could be taken based on this data?
- Areas that need attention or investigation
- Opportunities identified from the patterns

📋 **SUMMARY:**
- Concise takeaway message
- Most important insight in 1-2 sentences

Make your analysis data-driven, specific, and actionable. Use retail business context and terminology. Include specific numbers and percentages where relevant.
"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content