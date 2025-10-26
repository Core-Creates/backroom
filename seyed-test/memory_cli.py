#!/usr/bin/env python3
"""
Enhanced CLI with full conversation memory and context awareness
"""

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

class MemoryEnabledCLI:
    """CLI with conversation memory and context awareness."""
    
    def __init__(self, save_conversations: bool = True):
        self.system = RetailDataQueryGraph()
        self.messages: List[BaseMessage] = []
        self.save_conversations = save_conversations
        self.conversation_file = Path("conversation_history.json")
        
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
        
        # Add context awareness for follow-up questions
        context_keywords = ["this", "that", "it", "them", "those", "previous", "last", "above"]
        has_context_reference = any(keyword in user_input.lower() for keyword in context_keywords)
        
        if has_context_reference and len(self.messages) > 0:
            # Enhance query with context
            context = self.get_context_summary()
            enhanced_query = f"{context}\n\nCurrent question: {user_input}"
            
            # Use the chat interface for context-aware processing
            self.messages.append(HumanMessage(content=user_input))
            
            # Process with full message history
            updated_messages = self.system.chat(self.messages.copy())
            
            # Get the latest AI response
            ai_messages = [msg for msg in updated_messages if isinstance(msg, AIMessage)]
            if ai_messages:
                response = ai_messages[-1].content
                self.messages.append(AIMessage(content=response))
                return response
        
        # Regular processing for new topics
        response = self.system.query(user_input)
        
        # Add to conversation history
        self.messages.append(HumanMessage(content=user_input))
        self.messages.append(AIMessage(content=response))
        
        return response
    
    def show_conversation_stats(self):
        """Show statistics about the current conversation."""
        human_msgs = len([m for m in self.messages if isinstance(m, HumanMessage)])
        ai_msgs = len([m for m in self.messages if isinstance(m, AIMessage)])
        
        print(f"💬 Conversation Stats:")
        print(f"   📝 Your questions: {human_msgs}")
        print(f"   🤖 AI responses: {ai_msgs}")
        print(f"   💾 Memory: {'Enabled' if self.save_conversations else 'Disabled'}")
    
    def clear_memory(self):
        """Clear conversation history."""
        self.messages = []
        if self.conversation_file.exists():
            self.conversation_file.unlink()
        print("🧹 Conversation memory cleared!")
    
    def run(self):
        """Run the interactive CLI with memory."""
        
        print("🧠 Memory-Enabled Retail Intelligence System")
        print("=" * 60)
        print("🎯 Features:")
        print("  • 💬 Remembers our conversation")
        print("  • 🔗 Understands follow-up questions") 
        print("  • 💾 Saves conversation history")
        print("  • 📊 Full data analysis & visualization")
        print()
        print("🗣️ Commands:")
        print("  • 'stats' - Show conversation statistics")
        print("  • 'clear' - Clear conversation memory") 
        print("  • 'quit' - Exit system")
        print()
        
        if len(self.messages) > 0:
            print("👋 Welcome back! I remember our previous conversation.")
            self.show_conversation_stats()
            print()
        else:
            print("👋 Hello! I'm ready to help with your retail data questions.")
            
        print("Ask me anything about your retail data!")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n💭 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.save_conversation_history()
                    print("👋 Goodbye! Conversation saved for next time.")
                    break
                
                elif user_input.lower() == 'stats':
                    self.show_conversation_stats()
                    continue
                    
                elif user_input.lower() == 'clear':
                    self.clear_memory()
                    continue
                
                elif not user_input:
                    continue
                
                # Process the query with context
                print("🔄 Processing (with memory)...")
                response = self.process_query_with_context(user_input)
                
                print(f"\n🤖 AI: {response}")
                print("-" * 60)
                
                # Auto-save after each interaction
                if len(self.messages) % 4 == 0:  # Save every 2 exchanges
                    self.save_conversation_history()
                
            except KeyboardInterrupt:
                self.save_conversation_history()
                print("\n👋 Goodbye! Conversation saved.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    
    # Check for command line options
    save_conversations = "--no-save" not in sys.argv
    
    if "--help" in sys.argv:
        print("Memory-Enabled Retail Intelligence CLI")
        print("Options:")
        print("  --no-save    Disable conversation saving")
        print("  --help       Show this help message")
        return
    
    try:
        cli = MemoryEnabledCLI(save_conversations=save_conversations)
        cli.run()
    except Exception as e:
        print(f"❌ Failed to start system: {e}")

if __name__ == "__main__":
    main()