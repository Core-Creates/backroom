from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
import pandas as pd
import operator

# Import necessary existing modules and agents
from db.database_manager import DatabaseManager
from agents.query_agents import QueryGeneratorAgent, ResponseFormatterAgent
from agents.visualization_agent import VisualizationAgent
from agents.forecasting_agent import ForecastingAgent

class GraphState(TypedDict):
    """State for the LangGraph workflow."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_question: str
    analysis: Dict[str, Any]
    database_schema: Dict[str, Any]
    generated_query: Dict[str, Any]
    query_result: Dict[str, Any]
    visualization: Dict[str, Any]
    forecast: Dict[str, Any]
    final_response: str
    error: str

class RetailDataQueryGraph:
    """LangGraph implementation for querying retail data based on user questions."""
    
    def __init__(self, db_path: str = None):
        # Initialize database manager first
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize other agents
        self.query_generator = QueryGeneratorAgent()
        self.response_formatter = ResponseFormatterAgent()
        self.visualization_agent = VisualizationAgent(db_manager=self.db_manager)
        self.forecasting_agent = ForecastingAgent(self.db_manager)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _extract_conversation_context(self, state: GraphState) -> str:
        """Extract relevant conversation context for query generation."""
        messages = state.get("messages", [])
        
        if len(messages) < 2:
            return None
            
        # Get the last few exchanges for context
        recent_messages = messages[-6:]  # Last 3 exchanges
        
        context_lines = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                context_lines.append(f"Previous Question: {msg.content}")
            elif isinstance(msg, AIMessage):
                # Extract key data from AI responses for context
                content = msg.content
                if "DATA OVERVIEW" in content:
                    # Extract just the overview section
                    start = content.find("DATA OVERVIEW:")
                    end = content.find("📈", start) if "📈" in content else len(content)
                    if start != -1:
                        overview = content[start:end].strip()
                        context_lines.append(f"Previous Result: {overview[:200]}...")
        
        return "\n".join(context_lines) if context_lines else None
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("analyze_question", self._analyze_question)
        workflow.add_node("generate_query", self._generate_query)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("create_visualization", self._create_visualization)
        workflow.add_node("create_forecast", self._create_forecast)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Add edges
        workflow.add_edge(START, "analyze_question")
        workflow.add_conditional_edges(
            "analyze_question",
            self._should_continue_after_analysis,
            {
                "generate_query": "generate_query",
                "create_forecast": "create_forecast",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "generate_query",
            self._should_continue_after_generation,
            {
                "execute_query": "execute_query",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "execute_query",
            self._should_continue_after_execution,
            {
                "create_visualization": "create_visualization",
                "error": "handle_error"
            }
        )
        workflow.add_edge("create_visualization", "format_response")
        workflow.add_edge("create_forecast", "format_response")
        workflow.add_edge("format_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_question(self, state: GraphState) -> GraphState:
        """Analyze the user's question to determine the appropriate action."""
        print("🔍 Analyzing question...")
        
        question = state["messages"][-1].content
        
        # Simple analysis - in production, use more sophisticated NLP
        requires_viz = self.visualization_agent.should_create_visualization(question)
        requires_forecast = self.forecasting_agent.should_create_forecast(question)
        
        analysis = {
            "intent": "query",  # could be "query", "visualization", "help", "forecast", etc.
            "confidence": 0.8,
            "requires_visualization": requires_viz,
            "requires_forecasting": requires_forecast,
        }
        
        return {**state, "analysis": analysis}
    
    def _generate_query(self, state: GraphState) -> GraphState:
        """Generate SQL query from the user's question."""
        print("🗃️ Getting database schema...")
        try:
            # Get database schema if not already in state
            database_schema = state.get("database_schema", {})
            if not database_schema:
                database_schema = self.db_manager.get_database_schema()
                print(f"   Found {len(database_schema.get('tables', {}))} tables")
            
            # Extract conversation context for context-aware queries
            conversation_context = self._extract_conversation_context(state)
            
            print("🧠 Generating SQL query...")
            query_info = self.query_generator.generate_query(
                state["user_question"],
                database_schema,
                conversation_context
            )
            
            return {
                **state,
                "database_schema": database_schema,
                "generated_query": query_info
            }
        except Exception as e:
            return {
                **state,
                "error": f"Error generating query: {str(e)}"
            }
    
    def _execute_query(self, state: GraphState) -> GraphState:
        """Execute the generated SQL query."""
        try:
            if not state["generated_query"].get("success", False):
                return {
                    **state,
                    "error": f"Query generation failed: {state['generated_query'].get('error', 'Unknown error')}"
                }
            
            query = state["generated_query"]["query"]
            result = self.db_manager.execute_query(query)
            
            return {
                **state,
                "query_result": result
            }
        except Exception as e:
            return {
                **state,
                "error": f"Error executing query: {str(e)}"
            }
    
    def _create_visualization(self, state: GraphState) -> GraphState:
        """Create visualization if needed."""
        if not state.get("analysis", {}).get("requires_visualization", False):
            print("📊 No visualization needed")
            return state
        
        print("📊 Creating visualization...")
        
        question = state["messages"][-1].content
        query_result = state.get("query_result", {})
        query_info = state.get("generated_query", {})
        
        try:
            viz_result = self.visualization_agent.create_visualization(
                question=question,
                query_result=query_result,
                query_info=query_info
            )
            
            return {**state, "visualization": viz_result}
            
        except Exception as e:
            print(f"❌ Visualization error: {e}")
            return {**state, "visualization": {"success": False, "error": str(e)}}
    
    def _create_forecast(self, state: GraphState) -> GraphState:
        """Create forecast if needed."""
        if not state.get("analysis", {}).get("requires_forecasting", False):
            print("🔮 No forecasting needed")
            return state
        
        print("🔮 Creating forecast...")
        
        question = state["messages"][-1].content
        query_data = state.get("query_data", pd.DataFrame())
        
        try:
            forecast_result = self.forecasting_agent.process_forecast_request(
                question=question,
                item_data=query_data
            )
            
            return {**state, "forecast": forecast_result}
            
        except Exception as e:
            print(f"❌ Forecast error: {e}")
            return {**state, "forecast": {"success": False, "error": str(e)}}
    
    def _format_response(self, state: GraphState) -> GraphState:
        """Format the final response."""
        print("📝 Formatting response...")
        
        try:
            query_result = state.get("query_result", {})
            visualization = state.get("visualization", {})
            forecast = state.get("forecast", {})
            

            
            # Handle forecasting responses
            if forecast.get("success", False):
                response = forecast.get("response_text", "Forecast completed successfully.")
                return {**state, "final_response": response}
            
            # Handle regular query responses
            if query_result.get("success", False):
                data = query_result.get("data")
                viz_info = ""
                
                if visualization.get("success", False):
                    viz_path = visualization.get("chart_path", "")
                    chart_type = visualization.get("chart_type", "chart")
                    if viz_path:
                        viz_info = f"\n\n📊 **Visualization Created:** {chart_type.title()} saved as `{viz_path.split('/')[-1]}`"
                
                response = self.response_formatter.format_response(
                    question=state["user_question"],
                    query_result=query_result
                ) + viz_info
            else:
                # Check for forecast errors
                if forecast.get("success") == False:
                    response = forecast.get("response_text", f"❌ Forecast error: {forecast.get('error', 'Unknown error')}")
                else:
                    response = f"❌ I encountered an error: {query_result.get('error', 'Unknown error')}"
            
            return {**state, "final_response": response}
            
        except Exception as e:
            error_msg = f"Error formatting response: {str(e)}"
            print(f"❌ {error_msg}")
            return {**state, "final_response": f"❌ {error_msg}"}
    
    def _handle_error(self, state: GraphState) -> GraphState:
        """Handle errors that occur during processing."""
        error_message = f"❌ Sorry, I encountered an error: {state.get('error', 'Unknown error')}"
        
        # Add error message to the conversation
        error_ai_message = AIMessage(content=error_message)
        
        return {
            **state,
            "final_response": error_message,
            "messages": state["messages"] + [error_ai_message]
        }
    
    def _should_continue_after_analysis(self, state: GraphState) -> str:
        """Decide whether to continue after question analysis."""
        if state.get("error"):
            return "error"
        
        analysis = state.get("analysis", {})
        
        # Check if forecasting is required
        if analysis.get("requires_forecasting", False):
            return "create_forecast"
        
        # Default to regular query processing
        return "generate_query"
    
    def _should_continue_after_generation(self, state: GraphState) -> str:
        """Decide whether to continue after query generation."""
        if state.get("error") or not state.get("generated_query", {}).get("success", False):
            return "error"
        return "execute_query"
    
    def _should_continue_after_execution(self, state: GraphState) -> str:
        """Decide whether to continue after query execution."""
        if state.get("error") or not state.get("query_result", {}).get("success", False):
            return "error"
        return "create_visualization"
    
    def query(self, question: str) -> str:
        """Main method to process a user question and return a response."""
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "user_question": question,
            "analysis": {},
            "database_schema": {},
            "generated_query": {},
            "query_result": {},
            "visualization": {},
            "forecast": {},
            "final_response": "",
            "error": ""
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state.get("final_response", "No response generated")
    
    def chat(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Chat interface that maintains conversation history."""
        if not messages:
            return [AIMessage(content="Hello! I can help you query retail data. What would you like to know?")]
        
        initial_state = {
            "messages": messages,
            "user_question": messages[-1].content if messages else "",
            "database_schema": {},
            "generated_query": {},
            "query_result": {},
            "visualization": {},
            "final_response": "",
            "error": ""
        }
        
        final_state = self.graph.invoke(initial_state)
        return final_state.get("messages", messages)