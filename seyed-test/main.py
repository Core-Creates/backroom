import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from retail_query_graph import RetailDataQueryGraph
from typing import List
import json
from pathlib import Path
from datetime import datetime

# Load environment variables
load_dotenv()

# Verify API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in environment variables")
    print("💡 Make sure your .env file contains: OPENAI_API_KEY=your_key_here")
    sys.exit(1)

class MemoryEnabledMain:
    """Main CLI with conversation memory and context awareness."""
    
    def __init__(self, save_conversations: bool = True):
        self.query_system = RetailDataQueryGraph()
        self.messages: List[BaseMessage] = []
        self.save_conversations = save_conversations
        self.conversation_file = Path("main_conversation_history.json")
        
        # Load previous conversation if exists
        self.load_conversation_history()
    
    def load_conversation_history(self):
        """Load previous conversation history from file."""
        if self.conversation_file.exists() and self.save_conversations:
            try:
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert back to message objects
                for msg_data in data.get("messages", []):
                    if msg_data["type"] == "human":
                        self.messages.append(HumanMessage(content=msg_data["content"]))
                    elif msg_data["type"] == "ai":
                        self.messages.append(AIMessage(content=msg_data["content"]))
                
                if self.messages:
                    print(f"📚 Loaded {len(self.messages)} previous messages")
            except Exception as e:
                print(f"⚠️ Could not load conversation history: {e}")
    
    def save_conversation_history(self):
        """Save current conversation to file."""
        if not self.save_conversations:
            return
            
        try:
            # Convert messages to serializable format
            serializable_messages = []
            for msg in self.messages:
                if isinstance(msg, HumanMessage):
                    serializable_messages.append({
                        "type": "human",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
                elif isinstance(msg, AIMessage):
                    serializable_messages.append({
                        "type": "ai", 
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
            
            data = {
                "messages": serializable_messages,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.conversation_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save conversation: {e}")
    
    def get_context_summary(self) -> str:
        """Generate a summary of recent conversation for context."""
        if len(self.messages) < 2:
            return ""
        
        # Get last few messages for context
        recent_messages = self.messages[-6:]  # Last 3 exchanges
        
        context = "Previous conversation context:\n"
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                context += f"User: {msg.content[:100]}...\n"
            elif isinstance(msg, AIMessage):
                # Extract just the key findings for context
                content = msg.content
                if "KEY FINDINGS" in content:
                    key_section = content.split("KEY FINDINGS")[1].split("BUSINESS RECOMMENDATIONS")[0]
                    context += f"AI found: {key_section[:150].strip()}...\n"
        
        return context
    
    def process_query_with_context(self, user_input: str) -> str:
        """Process query with conversation context."""
        
        # Check for multi-item reorder analysis, which is a special case
        multi_item_reorder_keywords = ["which items need to be ordered", "reorder priority", "order soon", "reorder list", "who needs ordering"]
        if any(keyword in user_input.lower() for keyword in multi_item_reorder_keywords):
            try:
                from reorder_priority_analysis import find_items_to_reorder
                print("🔬 Running multi-item reorder analysis... This may take a moment.")
                return find_items_to_reorder()
            except Exception as e:
                return f"❌ Error during reorder analysis: {e}"

        # Check for inventory-specific questions that can be handled directly
        inventory_keywords = ["days of cover", "coverage", "inventory", "stock level", "reorder point"]
        is_inventory_question = any(keyword in user_input.lower() for keyword in inventory_keywords)
        
        # Extract item ID if present
        import re
        item_pattern = r'FOODS_\d+_\d+'
        item_match = re.search(item_pattern, user_input.upper())
        
        if is_inventory_question and item_match:
            try:
                return self._handle_inventory_question(user_input, item_match.group())
            except Exception as e:
                print(f"⚠️ Inventory analysis error: {e}")
                # Fall back to normal processing
        
        try:
            # Add context awareness for follow-up questions
            context_keywords = ["this", "that", "it", "them", "those", "previous", "last", "above"]
            has_context_reference = any(keyword in user_input.lower() for keyword in context_keywords)
            
            if has_context_reference and len(self.messages) > 0:
                # Use the chat interface for context-aware processing
                self.messages.append(HumanMessage(content=user_input))
                
                # Process with full message history
                updated_messages = self.query_system.chat(self.messages.copy())
                
                # Get the latest AI response
                ai_messages = [msg for msg in updated_messages if isinstance(msg, AIMessage)]
                if ai_messages:
                    response = ai_messages[-1].content
                    self.messages.append(AIMessage(content=response))
                    return response
            
            # Regular processing for new topics
            response = self.query_system.query(user_input)
            
            # Add to conversation history
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Processing error: {str(e)}"
            print(f"🔍 Debug info: {error_msg}")
            return f"Sorry, I encountered an error while processing your question. Error details: {str(e)}"
    
    def _handle_inventory_question(self, user_input: str, item_id: str) -> str:
        """Handle inventory-related questions directly using enhanced system."""
        from forecasting_agent import ForecastingAgent
        from inventory_management import InventoryManager
        from database_manager import DatabaseManager
        
        # Initialize components
        db_manager = DatabaseManager()
        forecasting_agent = ForecastingAgent(db_manager)
        inventory_manager = InventoryManager(db_manager)
        
        # Get item details
        item_details = inventory_manager.get_item_details(item_id)
        current_inventory = inventory_manager.get_item_inventory(item_id)
        
        if not item_details or current_inventory is None:
            return f"❌ Sorry, I couldn't find inventory data for {item_id}"
        
        # Generate forecast and inventory analysis
        forecast_df, model = forecasting_agent.generate_forecast(item_id, 30)
        inventory_insights = inventory_manager.generate_inventory_insights(item_id, forecast_df)
        
        if not inventory_insights['success']:
            return f"❌ Sorry, I couldn't analyze inventory for {item_id}: {inventory_insights.get('error', 'Unknown error')}"
        
        # Format response
        coverage = inventory_insights['coverage_analysis']
        reorder = inventory_insights['reorder_analysis'] 
        financial = inventory_insights['financial_analysis']
        
        response_parts = []
        response_parts.append(f"📊 **Inventory Analysis for {item_details['description']} ({item_id})**")
        response_parts.append(f"📦 **Current Stock:** {current_inventory:,} units")
        response_parts.append(f"📅 **Days of Cover:** {coverage['coverage_days']} days ({coverage['status'].upper()})")
        
        if coverage.get('cover_until'):
            response_parts.append(f"📅 **Stock Exhaustion:** {coverage['cover_until']}")
        
        response_parts.append(f"🔄 **Reorder Point:** {reorder['reorder_point']:,} units")
        response_parts.append(f"💰 **Expected Revenue:** ${financial['expected_revenue']:,.2f}")
        response_parts.append(f"📈 **Profit Margin:** {financial['profit_margin']}%")
        
        if inventory_insights.get('recommendations'):
            response_parts.append(f"🎯 **Priority Action:** {inventory_insights['recommendations'][0]}")
        
        return "\n".join(response_parts)
    
    def show_conversation_stats(self):
        """Show statistics about the current conversation."""
        human_msgs = len([m for m in self.messages if isinstance(m, HumanMessage)])
        ai_msgs = len([m for m in self.messages if isinstance(m, AIMessage)])
        
        print(f"� Conversation Stats:")
        print(f"   📝 Your questions: {human_msgs}")
        print(f"   🤖 AI responses: {ai_msgs}")
        print(f"   💾 Memory: {'Enabled' if self.save_conversations else 'Disabled'}")
    
    def clear_memory(self):
        """Clear conversation history."""
        self.messages = []
        if self.conversation_file.exists():
            self.conversation_file.unlink()
        print("🧹 Conversation memory cleared!")

def main():
    """Main CLI interface for the retail data query system with memory."""
    
    print("🧠 Retail Data Query System (Memory-Enabled)")
    print("=" * 60)
    print("🎯 Features:")
    print("  • 💬 Remembers our conversation")
    print("  • 🔗 Understands follow-up questions") 
    print("  • 💾 Saves conversation history")
    print("  • 📊 Full data analysis & visualization")
    print()
    print("Available data: sales, inventory (inv), and item dimensions (item_dim)")
    print()
    print("🗣️ Commands:")
    print("  • 'stats' - Show conversation statistics")
    print("  • 'clear' - Clear conversation memory") 
    print("  • 'quit' - Exit system")
    print("Type 'quit' to exit\n")
    
    # Initialize the memory-enabled system
    try:
        memory_system = MemoryEnabledMain()
        if len(memory_system.messages) > 0:
            print("👋 Welcome back! I remember our previous conversation.")
            memory_system.show_conversation_stats()
        else:
            print("👋 Hello! I'm ready to help with your retail data questions.")
        print("✅ Connected to retail database")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return
    
    # Main interaction loop with memory
    while True:
        try:
            # Get user input with EOF handling
            try:
                user_input = input("\n🤔 Your question: ").strip()
            except EOFError:
                print("\n👋 EOF detected. Goodbye!")
                memory_system.save_conversation_history()
                break
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                memory_system.save_conversation_history()
                print("👋 Goodbye! Conversation saved for next time.")
                break
            
            elif user_input.lower() == 'stats':
                memory_system.show_conversation_stats()
                continue
                
            elif user_input.lower() == 'clear':
                memory_system.clear_memory()
                continue
            
            if not user_input:
                continue
            
            print("� Processing (with memory)...")
            
            # Process with memory and context awareness
            ai_response = memory_system.process_query_with_context(user_input)
            
            # Print the AI's response
            if ai_response and ai_response.strip():
                print(f"\n🤖 {ai_response}")
                
                # Auto-save after each interaction
                if len(memory_system.messages) % 4 == 0:  # Save every 2 exchanges
                    memory_system.save_conversation_history()
            else:
                print("❌ No response generated")
        
        except KeyboardInterrupt:
            memory_system.save_conversation_history()
            print("\n👋 Goodbye! Conversation saved.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def example_queries():
    """Show example queries that users can ask."""
    examples = [
        "Show me the top 10 selling items",
        "What's the total sales revenue?",
        "How many items are in inventory?",
        "Which items have low stock levels?",
        "Show sales data for the last month",
        "What are the most popular product categories?",
        "Compare sales across different time periods",
        "Show inventory turnover rates",
        "Create a chart for those items",  # Memory-aware example
        "What about their inventory levels?"  # Follow-up example
    ]
    
    print("\n💡 Example questions you can ask:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    print("\n🔗 Memory Features:")
    print("  • Ask follow-up questions using 'those', 'that', 'them'")
    print("  • Reference previous results with 'it', 'the previous data'")
    print("  • Build conversations naturally with context awareness")

if __name__ == "__main__":
    # Check for command line options
    if len(sys.argv) > 1:
        if sys.argv[1] == "examples":
            example_queries()
        elif sys.argv[1] == "--help":
            print("Memory-Enabled Retail Data Query System")
            print("Options:")
            print("  examples     Show example queries")
            print("  --help       Show this help message")
        else:
            main()
    else:
        main()